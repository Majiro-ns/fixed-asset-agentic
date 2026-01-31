# -*- coding: utf-8 -*-
"""
Gemini API integration for fixed asset classification.
Feature-flagged: Only active when GEMINI_ENABLED=1 and API key configured.

This module implements the Stop-first principle:
- When confident: return CAPITAL_LIKE or EXPENSE_LIKE
- When uncertain: return GUIDANCE (never guess)
"""
import json
import os
from typing import Any, Dict, List, Optional


def _bool_env(name: str, default: bool = False) -> bool:
    """Check environment variable for boolean flag."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_model_name() -> str:
    """Get model name from env or use default (flash for speed)."""
    return os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


# System prompt for Stop-first classification
CLASSIFICATION_SYSTEM_PROMPT = """あなたは固定資産と費用の判定を支援するAIアシスタントです。

【重要な原則: Stop-first】
- 確信がある場合のみ CAPITAL_LIKE または EXPENSE_LIKE を返す
- 少しでも判断に迷う場合は GUIDANCE を返す
- 推測や断定は禁止。迷ったら止まる

【判定基準】
CAPITAL_LIKE（固定資産寄り）:
- 耐用年数1年以上、取得価額10万円以上
- 新規取得、増設、改良
- キーワード: 購入、設置、導入、新規、取得

EXPENSE_LIKE（費用寄り）:
- 修繕、維持、消耗品
- 少額（10万円未満）
- キーワード: 修理、修繕、メンテナンス、消耗品

GUIDANCE（要確認）:
- 撤去、移設、既設など判断が割れる語
- 金額が境界付近（10万円、20万円、60万円前後）
- 情報不足で判断できない場合

【出力形式】
必ず以下のJSON形式で回答してください:
{
  "decision": "CAPITAL_LIKE" | "EXPENSE_LIKE" | "GUIDANCE",
  "confidence": 0.0〜1.0の数値,
  "reasoning": "判定理由（日本語）",
  "flags": ["該当するキーワードやフラグ"]
}
"""


def classify_with_gemini(
    item_description: str,
    amount: float,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classify a line item using Gemini API.

    Args:
        item_description: Description of the item (e.g., "サーバー設置工事")
        amount: Amount in JPY
        context: Optional context dict with additional info

    Returns:
        {
            "decision": "CAPITAL_LIKE" | "EXPENSE_LIKE" | "GUIDANCE",
            "confidence": float (0.0-1.0),
            "reasoning": str,
            "flags": list[str],
            "error": str (if any error occurred)
        }

    If feature is disabled or API fails, returns GUIDANCE (safe fallback).
    """
    # Default safe response (Stop-first: when in doubt, stop)
    default_response = {
        "decision": "GUIDANCE",
        "confidence": 0.0,
        "reasoning": "Gemini API未使用（フォールバック）",
        "flags": ["gemini_fallback"],
    }

    # Feature flag check
    if not _bool_env("GEMINI_ENABLED", False):
        default_response["reasoning"] = "Gemini機能が無効（GEMINI_ENABLED=1で有効化）"
        default_response["flags"] = ["gemini_disabled"]
        return default_response

    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        default_response["reasoning"] = "GOOGLE_API_KEYが未設定"
        default_response["flags"] = ["missing_api_key"]
        return default_response

    try:
        # Import only when feature is enabled
        import google.generativeai as genai

        # Configure API
        genai.configure(api_key=api_key)

        # Get model
        model_name = _get_model_name()
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=CLASSIFICATION_SYSTEM_PROMPT,
        )

        # Build user prompt
        user_prompt = _build_user_prompt(item_description, amount, context)

        # Generate response
        response = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,  # Low temperature for consistent results
            ),
        )

        # Parse response
        return _parse_gemini_response(response.text)

    except ImportError:
        default_response["reasoning"] = "google-generativeaiライブラリ未インストール"
        default_response["flags"] = ["library_not_installed"]
        return default_response

    except json.JSONDecodeError:
        # JSON parsing failed
        default_response["reasoning"] = "Gemini レスポンス解析エラー"
        default_response["flags"] = ["parse_error"]
        return default_response

    except Exception:
        # Any other error: return safe GUIDANCE (Stop-first principle)
        # Don't expose error details in response
        default_response["reasoning"] = "Gemini API エラー（詳細はログ参照）"
        default_response["flags"] = ["api_error"]
        return default_response


def _build_user_prompt(
    item_description: str,
    amount: float,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """Build the user prompt for classification."""
    prompt_parts = [
        "以下の明細項目を固定資産/費用のどちらに分類すべきか判定してください。",
        "",
        f"【項目】{item_description}",
        f"【金額】{amount:,.0f}円",
    ]

    # Add context if available
    if context:
        if context.get("vendor"):
            prompt_parts.append(f"【取引先】{context['vendor']}")
        if context.get("date"):
            prompt_parts.append(f"【日付】{context['date']}")
        if context.get("notes"):
            prompt_parts.append(f"【備考】{context['notes']}")

    prompt_parts.extend([
        "",
        "【注意】",
        "- 判断に迷う場合は必ず GUIDANCE を選択してください",
        "- 撤去、移設、既設などの語が含まれる場合は GUIDANCE を選択してください",
        "- 推測や断定は禁止です",
    ])

    return "\n".join(prompt_parts)


def _parse_gemini_response(response_text: str) -> Dict[str, Any]:
    """Parse Gemini response JSON."""
    try:
        result = json.loads(response_text)

        # Validate required fields
        decision = result.get("decision", "GUIDANCE")
        if decision not in ("CAPITAL_LIKE", "EXPENSE_LIKE", "GUIDANCE"):
            decision = "GUIDANCE"  # Safe fallback

        confidence = result.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = max(0.0, min(1.0, float(confidence)))

        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": result.get("reasoning", ""),
            "flags": result.get("flags", []),
        }

    except json.JSONDecodeError:
        # If JSON parsing fails, return safe GUIDANCE
        return {
            "decision": "GUIDANCE",
            "confidence": 0.0,
            "reasoning": f"レスポンス解析エラー: {response_text[:100]}",
            "flags": ["parse_error"],
        }


def classify_line_items(
    line_items: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Classify multiple line items.

    Args:
        line_items: List of dicts with 'item_description' and 'amount'
        context: Optional shared context

    Returns:
        List of classification results
    """
    results = []
    for item in line_items:
        description = item.get("item_description", item.get("description", ""))
        amount = item.get("amount", 0)

        result = classify_with_gemini(description, amount, context)
        result["line_item"] = item  # Include original item
        results.append(result)

    return results


# Convenience function for integration with existing classifier
def enhance_classification(
    existing_result: Dict[str, Any],
    item_description: str,
    amount: float,
) -> Dict[str, Any]:
    """
    Enhance existing rule-based classification with Gemini analysis.

    Only called when existing result is GUIDANCE (uncertain).
    Returns enhanced result with Gemini's analysis added.
    """
    # Only enhance GUIDANCE cases
    if existing_result.get("decision") != "GUIDANCE":
        return existing_result

    # Get Gemini's opinion
    gemini_result = classify_with_gemini(item_description, amount)

    # Add Gemini analysis to existing result
    enhanced = existing_result.copy()
    enhanced["gemini_analysis"] = {
        "decision": gemini_result["decision"],
        "confidence": gemini_result["confidence"],
        "reasoning": gemini_result["reasoning"],
    }

    # If Gemini is confident, suggest its decision
    if gemini_result["confidence"] >= 0.8 and gemini_result["decision"] != "GUIDANCE":
        enhanced["gemini_suggestion"] = gemini_result["decision"]

    return enhanced
