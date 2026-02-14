# -*- coding: utf-8 -*-
"""
Gemini API integration for fixed asset classification.
Feature-flagged: Only active when GEMINI_ENABLED=1 and API key configured.

This module implements the Stop-first principle:
- When confident: return CAPITAL_LIKE or EXPENSE_LIKE
- When uncertain: return GUIDANCE (never guess)
"""
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("fixed_asset_api")


def _bool_env(name: str, default: bool = False) -> bool:
    """Check environment variable for boolean flag."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_model_name() -> str:
    """Get model name from env or use default (flash for speed)."""
    return os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")


# ---------------------------------------------------------------------------
# System prompt — 税務知識を注入した全面改善版
# ---------------------------------------------------------------------------
CLASSIFICATION_SYSTEM_PROMPT = """あなたは日本の税務・会計に精通した固定資産判定の専門AIアシスタントです。
見積書・請求書の各明細を**個別に**判定し、4段階のフローで結果を集約します。

═══════════════════════════════════════
【最重要原則: Stop-first】
═══════════════════════════════════════
- 確信がある場合のみ CAPITAL_LIKE または EXPENSE_LIKE を返す
- 少しでも判断に迷う場合は GUIDANCE を返す（推測・断定禁止）
- 情報不足のときも GUIDANCE を返す

═══════════════════════════════════════
【税務知識: 取得価額の範囲】
═══════════════════════════════════════

■ 取得価額に「含める」もの:
  - 購入代価（本体価格）
  - 付随費用: 引取運賃、荷役費、運送保険料、購入手数料
  - 設計費、据付費（基礎工事含む）、試運転費
  - ソフトウェアの導入・カスタマイズ費用
  → これらは取得価額に含める。各明細のincluded_in_acquisition_costで判定すること。

■ 取得価額に「含めない」もの:
  - 撤去費用（既存設備の除却）
  - 不動産取得税、登録免許税
  - 借入金利子（原則）
  - 引越費用、移転費用
  → これらは個別に費用処理が可能。

═══════════════════════════════════════
【税務知識: 資本的支出 vs 修繕費】
═══════════════════════════════════════

■ 修繕費として処理できるもの:
  - 3年以内の周期で行う定期修繕・保守点検
  - 20万円未満の修理・改良
  - 60万円未満 or 前期末取得価額の10%以下の修理
  - 原状回復のための修繕

■ 資本的支出となるもの:
  - 増設、拡張
  - 用途変更のための改造
  - 耐用年数を延長する改良
  - 資産価値を明らかに増加させる改良

═══════════════════════════════════════
【金額基準（少額資産の特例）】
═══════════════════════════════════════
  - 10万円未満 → 少額減価償却資産（全額を即時経費処理）
  - 10万円以上〜20万円未満 → 一括償却資産（3年均等償却）
  - 20万円以上〜30万円未満 → 中小企業の特例（即時経費、年300万円上限）
  - 30万円超 → 通常の固定資産（法定耐用年数で償却）

  ★ 金額基準（10万/20万/30万円等）は各明細の個別金額に対して適用すること。明細の金額を合算して判定してはならない

═══════════════════════════════════════
【明細個別判定の原則】
═══════════════════════════════════════
  - 各明細は独立して判定すること。他の明細の金額と合算して判定してはならない
  - 付随費用（設置費、運搬費等）は、品名から明確に本体に紐づくと判断できる場合のみ included_in_acquisition_cost: true とし、判断に迷う場合はGUIDANCEとすること
  - 1つの書類に資産計上と費用処理が混在するのは正常（明細ごとに判定）
  - 書類タイトルや取引先は参考情報とし、判定は各明細の内容と個別金額に基づくこと

═══════════════════════════════════════
【分類ルール】
═══════════════════════════════════════

CAPITAL_LIKE（固定資産寄り）:
  - 新規取得、増設、改良で当該明細の金額が10万円以上
  - 品名から明らかに資産性がある場合

EXPENSE_LIKE（費用寄り）:
  - 修繕費の要件を満たす修理・保守
  - 取得価額に含めない撤去費用等
  - 少額減価償却資産（10万円未満）

GUIDANCE（要確認 — 迷ったら必ずこれ）:
  - 資本的支出か修繕費か判断が分かれる場合
  - 金額が境界付近（10万/20万/30万/60万前後）
  - 撤去、移設、既設など判断が割れる語を含む
  - 情報不足で判断できない場合
  - 一式工事で明細の内訳が不明な場合

═══════════════════════════════════════
【GUIDANCE判定時: 類似事例の生成】
═══════════════════════════════════════
GUIDANCE判定の場合、similar_caseとして参考になる類似の実務事例を1つ生成してください。
経理担当者が「うちの場合はどうだろう？」と考える手がかりになる事例です。

形式:
{
  "description": "事例の概要（何の工事・購入だったか）",
  "outcome": "実際にどう処理されたか",
  "lesson": "この事例から得られる判断のポイント"
}

例:
{
  "description": "空調設備の更新工事（撤去費含む一式見積）",
  "outcome": "撤去費を除外し、資本的支出80万円＋修繕費40万円に分離計上",
  "lesson": "一式の中に撤去費が含まれる場合、分離すると有利な場合がある"
}

CAPITAL_LIKEやEXPENSE_LIKEの場合はsimilar_caseはnullとしてください。

═══════════════════════════════════════
【判定フロー（4段階）】
═══════════════════════════════════════
以下の4段階を順に実行し、結果をJSONで返してください。

STEP 1: 各明細行を個別に判定
  - 各明細を独立してCAPITAL_LIKE / EXPENSE_LIKE / GUIDANCEに分類
  - 金額基準（10万/20万/30万円）は各明細の個別金額に対して適用
  - 他の明細の金額と合算して判定しないこと

STEP 2: 各明細が取得価額に含めるべきか個別判定
  - 各明細にincluded_in_acquisition_cost: true/falseを設定
  - 資産性の判断根拠をacquisition_cost_reasonに記載
  - 付随費用（設置費、運搬費等）は品名から判断。迷う場合はfalse

STEP 3: 取得価額合計と費用合計を算出（税抜き基準）
  - acquisition_cost_total: included_in_acquisition_cost: trueの明細の合計
  - expense_total: included_in_acquisition_cost: falseの明細の合計
  - 税抜き金額で算出すること

STEP 4: 資産分の想定耐用年数を提示
  - 減価償却資産の耐用年数等に関する省令を参照
  - estimated_useful_life_years: 想定耐用年数
  - useful_life_basis: 根拠（例: 「サーバー: 器具及び備品 - 電子計算機 → 4年」）
  - asset_category: 資産区分

═══════════════════════════════════════
【出力形式】
═══════════════════════════════════════
必ず以下のJSON形式で回答してください:
{
  "decision": "CAPITAL_LIKE" | "EXPENSE_LIKE" | "GUIDANCE",
  "confidence": 0.0〜1.0,
  "reasons": ["判定理由1", "判定理由2"],
  "reasoning": "4段階フローの判定過程の説明",
  "line_item_analysis": [
    {
      "line_no": 1,
      "description": "品名",
      "amount": 400000,
      "classification": "CAPITAL_LIKE" | "EXPENSE_LIKE" | "GUIDANCE",
      "confidence": 0.0〜1.0,
      "included_in_acquisition_cost": true,
      "acquisition_cost_reason": "取得価額に含める理由/含めない理由",
      "flags": [],
      "reason": "判定理由"
    }
  ],
  "acquisition_cost_total": 0,
  "expense_total": 0,
  "estimated_useful_life_years": 0,
  "useful_life_basis": "根拠（減価償却資産の耐用年数等に関する省令より）",
  "asset_category": "資産区分（例: 器具及び備品 - 電子計算機）",
  "missing_fields": ["不足情報1"],
  "why_missing_matters": ["なぜその情報が必要か"],
  "similar_case": null,
  "evidence": []
}

【出力ルール】
- decision: 各明細の個別判定を集約した結果。CAPITAL_LIKEとEXPENSE_LIKEが混在する場合はGUIDANCE
- confidence: 0.7未満なら GUIDANCE にすること
- reasons: 日本語で判定理由を箇条書き
- reasoning: 4段階フローの判定過程を文章で説明
- line_item_analysis: 各明細の個別判定（STEP 1, 2の結果）。明細ごとにclassification, confidence, included_in_acquisition_costを設定
- acquisition_cost_total: 取得価額に含める明細の合計額（税抜き、STEP 3）
- expense_total: 費用として処理する明細の合計額（税抜き、STEP 3）
- estimated_useful_life_years: 想定耐用年数（STEP 4）。CAPITAL_LIKE明細がない場合は0
- useful_life_basis: 耐用年数の根拠。減価償却資産の耐用年数等に関する省令を参照
- asset_category: 資産区分（例: 器具及び備品 - 電子計算機）
- missing_fields: 判定に不足している情報（あれば）
- why_missing_matters: なぜその情報が必要か（あれば）
- evidence: 判定の根拠となる情報（あれば）
"""


# ---------------------------------------------------------------------------
# メイン関数
# ---------------------------------------------------------------------------

def classify_with_gemini(
    line_items: Union[List[Dict[str, Any]], str],
    context: str = "",
    document_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classify line items using Gemini API.

    Args:
        line_items: List of dicts (new) or description string (legacy fallback).
                    List format: [{"description": str, "amount": int/float, ...}, ...]
                    String format: "サーバー設置工事" (legacy single-item mode)
        context: Additional context string
        document_info: Document metadata dict with keys like:
                       title, vendor, total, date, notes

    Returns:
        {
            "decision": "CAPITAL_LIKE" | "EXPENSE_LIKE" | "GUIDANCE",
            "confidence": float (0.0-1.0),
            "reasons": list[str],
            "line_item_analysis": list[dict],
            "acquisition_cost_total": int,
            "excluded_total": int,
            "missing_fields": list[str],
            "why_missing_matters": list[str],
            "evidence": list,
            "useful_life": dict | None,
            "error": str (if any error occurred)
        }

    If feature is disabled or API fails, returns GUIDANCE (safe fallback).
    """
    # Default safe response (Stop-first: when in doubt, stop)
    default_response: Dict[str, Any] = {
        "decision": "GUIDANCE",
        "confidence": 0.0,
        "reasons": ["Gemini API未使用（フォールバック）"],
        "reasoning": "",
        "line_item_analysis": [],
        "acquisition_cost_total": 0,
        "expense_total": 0,
        "excluded_total": 0,
        "estimated_useful_life_years": 0,
        "useful_life_basis": "",
        "asset_category": "",
        "missing_fields": [],
        "why_missing_matters": [],
        "similar_case": None,
        "evidence": [],
        "useful_life": None,
        "flags": ["gemini_fallback"],
    }

    # Feature flag check
    if not _bool_env("GEMINI_ENABLED", False):
        default_response["reasons"] = ["Gemini機能が無効（GEMINI_ENABLED=1で有効化）"]
        default_response["flags"] = ["gemini_disabled"]
        return default_response

    try:
        # Import only when feature is enabled
        from google import genai
        from google.genai import types

        # Initialize client (RISK-003: timeout 30s)
        _http_opts = types.HttpOptions(timeout=_GEMINI_TIMEOUT_MS)
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true":
            client = genai.Client(http_options=_http_opts)
        elif api_key:
            client = genai.Client(api_key=api_key, http_options=_http_opts)
        else:
            default_response["reasons"] = ["認証情報が未設定（Vertex AI環境変数またはAPIキー）"]
            default_response["flags"] = ["missing_credentials"]
            return default_response

        model_name = _get_model_name()

        # Normalize input: legacy str → list conversion
        normalized_items = _normalize_line_items(line_items)

        # Build user prompt
        user_prompt = _build_user_prompt(normalized_items, context, document_info)

        # Generate response
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=CLASSIFICATION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
            ),
        )

        # Parse response
        return _parse_gemini_response(response.text)

    except ImportError:
        default_response["reasons"] = ["google-genaiライブラリ未インストール"]
        default_response["flags"] = ["library_not_installed"]
        return default_response

    except json.JSONDecodeError:
        default_response["reasons"] = ["Gemini レスポンス解析エラー"]
        default_response["flags"] = ["parse_error"]
        return default_response

    except (ConnectionError, TimeoutError, OSError, RuntimeError, ValueError) as e:
        logger.exception("Gemini API error: %s", e)
        default_response["reasons"] = [f"Gemini API エラー: {type(e).__name__}"]
        default_response["flags"] = ["api_error"]
        return default_response


# ---------------------------------------------------------------------------
# 入力正規化
# ---------------------------------------------------------------------------

def _normalize_line_items(
    line_items: Union[List[Dict[str, Any]], str],
) -> List[Dict[str, Any]]:
    """Normalize input to list of dicts. Supports legacy str input."""
    if isinstance(line_items, str):
        # Legacy fallback: single description string
        return [{"description": line_items, "amount": 0}]

    if isinstance(line_items, list):
        normalized = []
        for item in line_items:
            if isinstance(item, dict):
                normalized.append({
                    "description": item.get("description", item.get("item_description", "")),
                    "amount": item.get("amount", 0),
                    **{k: v for k, v in item.items() if k not in ("description", "item_description", "amount")},
                })
            elif isinstance(item, str):
                normalized.append({"description": item, "amount": 0})
            else:
                normalized.append({"description": str(item), "amount": 0})
        return normalized

    return [{"description": str(line_items), "amount": 0}]


# ---------------------------------------------------------------------------
# C-04: 入力サニタイズ（プロンプトインジェクション対策）
# ---------------------------------------------------------------------------

_MAX_INPUT_LENGTH = 50000
_MAX_PROMPT_CHARS = 10000
_MAX_LINE_ITEMS = 50
_GEMINI_TIMEOUT_MS = 30_000


def _sanitize_text(text: str) -> str:
    """Sanitize user input text for prompt injection prevention."""
    if not isinstance(text, str):
        return ""
    text = text[:_MAX_INPUT_LENGTH]
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text


# ---------------------------------------------------------------------------
# プロンプト構築
# ---------------------------------------------------------------------------

def _build_user_prompt(
    line_items: List[Dict[str, Any]],
    context: str = "",
    document_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Build user prompt with full document context and all line items."""
    parts: List[str] = []

    parts.append("以下の書類の各明細を個別に判定してください。4段階フローに従い、明細個別判定→取得価額算入判定→合計算出→耐用年数提示の順で処理してください。")
    parts.append("")

    # Document info (sanitized, delimited)
    if document_info:
        parts.append("═══ 書類情報 ═══")
        parts.append("```")
        if document_info.get("title"):
            parts.append(f"書類タイトル: {_sanitize_text(str(document_info['title']))}")
        if document_info.get("vendor"):
            parts.append(f"取引先: {_sanitize_text(str(document_info['vendor']))}")
        if document_info.get("date"):
            parts.append(f"日付: {_sanitize_text(str(document_info['date']))}")
        # NOTE: 合計金額は表示しない（合計ベース判定のバイアス防止）
        if document_info.get("notes"):
            parts.append(f"備考: {_sanitize_text(str(document_info['notes']))}")
        parts.append("```")
        parts.append("")

    # Line items (sanitized, delimited, truncated for cost control)
    truncated = len(line_items) > _MAX_LINE_ITEMS
    display_items = line_items[:_MAX_LINE_ITEMS]
    parts.append("═══ 明細一覧 ═══")
    if truncated:
        parts.append(f"（※ 全{len(line_items)}件中、先頭{_MAX_LINE_ITEMS}件を表示）")
    parts.append("```")
    for i, item in enumerate(display_items, 1):
        desc = _sanitize_text(item.get("description", ""))
        amount = item.get("amount", 0)
        amount_str = f"¥{int(amount):,}" if amount else "金額不明"
        line = f"{i}. {desc} — {amount_str}"
        # Add extra fields if present
        extras = []
        if item.get("quantity"):
            extras.append(f"数量:{item['quantity']}")
        if item.get("unit"):
            extras.append(f"単位:{item['unit']}")
        if item.get("remarks"):
            extras.append(f"備考:{_sanitize_text(str(item['remarks']))}")
        if extras:
            line += f"  ({', '.join(extras)})"
        parts.append(line)

    # NOTE: 明細合計は表示しない（合計ベース判定のバイアス防止）
    parts.append("```")

    # Additional context (sanitized, delimited)
    if context:
        parts.append("")
        parts.append("═══ 追加コンテキスト ═══")
        parts.append("```")
        parts.append(_sanitize_text(context))
        parts.append("```")

    # Instructions
    parts.extend([
        "",
        "═══ 判定指示 ═══",
        "- 各明細を独立して判定してください。金額基準（10万/20万/30万円）は明細個別の金額に適用してください",
        "- 付随費用かどうかは明細名から慎重に判断し、判断に迷う場合はGUIDANCEとしてください",
        "- 取得価額に含めるべき明細の合計と費用の合計を税抜きで算出してください",
        "- 資産については減価償却資産の耐用年数等に関する省令に基づく耐用年数を提示してください",
        "- 各明細が取得価額に含まれるか含まれないかを line_item_analysis で明示してください",
        "- 判断に迷う場合は必ず GUIDANCE を選択してください",
        "- 撤去、移設、既設などの語が含まれる場合は特に慎重に判断してください",
    ])

    prompt = "\n".join(parts)
    # RISK-004: Truncate prompt if exceeds cost limit
    if len(prompt) > _MAX_PROMPT_CHARS:
        logger.warning("Prompt truncated from %d to %d chars", len(prompt), _MAX_PROMPT_CHARS)
        prompt = prompt[:_MAX_PROMPT_CHARS] + "\n```\n（※ 入力が長いため切り詰めました）"
    return prompt


# ---------------------------------------------------------------------------
# レスポンス解析
# ---------------------------------------------------------------------------

def _parse_gemini_response(response_text: str) -> Dict[str, Any]:
    """Parse Gemini response JSON with new output structure."""
    try:
        result = json.loads(response_text)

        # Validate decision
        decision = result.get("decision", "GUIDANCE")
        if decision not in ("CAPITAL_LIKE", "EXPENSE_LIKE", "GUIDANCE"):
            decision = "GUIDANCE"

        # Validate confidence
        confidence = result.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = max(0.0, min(1.0, float(confidence)))

        # Low confidence → force GUIDANCE (Stop-first)
        if confidence < 0.7 and decision != "GUIDANCE":
            decision = "GUIDANCE"

        # Normalize reasons (support legacy "reasoning" field)
        reasons = result.get("reasons", [])
        if not reasons and result.get("reasoning"):
            reasons = [result["reasoning"]]
        if not isinstance(reasons, list):
            reasons = [str(reasons)]

        # line_item_analysis
        line_item_analysis = result.get("line_item_analysis", [])
        if not isinstance(line_item_analysis, list):
            line_item_analysis = []

        # Totals (4段階フロー STEP 3)
        acquisition_cost_total = result.get("acquisition_cost_total", 0)
        if not isinstance(acquisition_cost_total, (int, float)):
            acquisition_cost_total = 0
        expense_total = result.get("expense_total", 0)
        if not isinstance(expense_total, (int, float)):
            expense_total = 0
        # Legacy field support
        excluded_total = result.get("excluded_total", 0)
        if not isinstance(excluded_total, (int, float)):
            excluded_total = 0

        # 4段階フロー STEP 4: 耐用年数
        estimated_useful_life_years = result.get("estimated_useful_life_years", 0)
        if not isinstance(estimated_useful_life_years, (int, float)):
            estimated_useful_life_years = 0
        useful_life_basis = result.get("useful_life_basis", "")
        if not isinstance(useful_life_basis, str):
            useful_life_basis = str(useful_life_basis) if useful_life_basis else ""
        asset_category = result.get("asset_category", "")
        if not isinstance(asset_category, str):
            asset_category = str(asset_category) if asset_category else ""

        # Reasoning (4段階フロー判定過程)
        reasoning = result.get("reasoning", "")
        if not isinstance(reasoning, str):
            reasoning = str(reasoning) if reasoning else ""

        # Missing fields
        missing_fields = result.get("missing_fields", [])
        if not isinstance(missing_fields, list):
            missing_fields = [str(missing_fields)] if missing_fields else []
        why_missing_matters = result.get("why_missing_matters", [])
        if not isinstance(why_missing_matters, list):
            why_missing_matters = [str(why_missing_matters)] if why_missing_matters else []

        # Similar case (GUIDANCE only)
        similar_case = result.get("similar_case")
        if similar_case and not isinstance(similar_case, dict):
            similar_case = None

        # Evidence and useful_life
        evidence = result.get("evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        useful_life = result.get("useful_life")
        if useful_life and not isinstance(useful_life, dict):
            useful_life = None

        # Legacy flags support
        flags = result.get("flags", [])
        if not isinstance(flags, list):
            flags = [str(flags)] if flags else []

        return {
            "decision": decision,
            "confidence": confidence,
            "reasons": reasons,
            "reasoning": reasoning,
            "line_item_analysis": line_item_analysis,
            "acquisition_cost_total": int(acquisition_cost_total),
            "expense_total": int(expense_total),
            "excluded_total": int(excluded_total),
            "estimated_useful_life_years": int(estimated_useful_life_years),
            "useful_life_basis": useful_life_basis,
            "asset_category": asset_category,
            "missing_fields": missing_fields,
            "why_missing_matters": why_missing_matters,
            "similar_case": similar_case,
            "evidence": evidence,
            "useful_life": useful_life,
            "flags": flags,
        }

    except json.JSONDecodeError:
        return {
            "decision": "GUIDANCE",
            "confidence": 0.0,
            "reasons": [f"レスポンス解析エラー: {response_text[:100]}"],
            "reasoning": "",
            "line_item_analysis": [],
            "acquisition_cost_total": 0,
            "expense_total": 0,
            "excluded_total": 0,
            "estimated_useful_life_years": 0,
            "useful_life_basis": "",
            "asset_category": "",
            "missing_fields": [],
            "why_missing_matters": [],
            "similar_case": None,
            "evidence": [],
            "useful_life": None,
            "flags": ["parse_error"],
        }


# ---------------------------------------------------------------------------
# 複数明細の分類（既存互換ラッパー）
# ---------------------------------------------------------------------------

def classify_line_items(
    line_items: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Classify multiple line items (legacy wrapper).

    Now delegates to classify_with_gemini with full document context.

    Args:
        line_items: List of dicts with 'description'/'item_description' and 'amount'
        context: Optional shared context dict

    Returns:
        List with single result containing all line item analyses
    """
    doc_info = None
    ctx_str = ""
    if context:
        doc_info = {
            "vendor": context.get("vendor"),
            "date": context.get("date"),
            "title": context.get("title"),
            "total": context.get("total"),
            "notes": context.get("notes"),
        }
        if context.get("notes"):
            ctx_str = context["notes"]

    result = classify_with_gemini(line_items, ctx_str, doc_info)
    result["line_items_input"] = line_items
    return [result]


# ---------------------------------------------------------------------------
# 既存分類の拡張（既存互換）
# ---------------------------------------------------------------------------

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
    if existing_result.get("decision") != "GUIDANCE":
        return existing_result

    gemini_result = classify_with_gemini(item_description)

    enhanced = existing_result.copy()
    enhanced["gemini_analysis"] = {
        "decision": gemini_result["decision"],
        "confidence": gemini_result["confidence"],
        "reasons": gemini_result.get("reasons", []),
    }

    if gemini_result["confidence"] >= 0.8 and gemini_result["decision"] != "GUIDANCE":
        enhanced["gemini_suggestion"] = gemini_result["decision"]

    return enhanced
