# -*- coding: utf-8 -*-
"""
Useful Life Estimator using Gemini API

Estimates the legal useful life (耐用年数) of fixed assets based on
Japanese tax depreciation rules.

Feature-flagged: Set GEMINI_API_KEY environment variable to enable.
"""
import json
import os
from typing import Any, Dict, List, Optional

# Optional: Google Generative AI (Gemini)
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None


# ============================================================================
# 主要な法定耐用年数マスタ（減価償却資産の耐用年数等に関する省令より）
# ============================================================================
USEFUL_LIFE_MASTER = {
    # 器具及び備品
    "パソコン": {"years": 4, "category": "器具及び備品", "subcategory": "電子計算機", "basis": "別表第一 器具及び備品 11"},
    "ノートパソコン": {"years": 4, "category": "器具及び備品", "subcategory": "電子計算機", "basis": "別表第一 器具及び備品 11"},
    "サーバー": {"years": 5, "category": "器具及び備品", "subcategory": "電子計算機（サーバー用）", "basis": "別表第一 器具及び備品 11"},
    "サーバ": {"years": 5, "category": "器具及び備品", "subcategory": "電子計算機（サーバー用）", "basis": "別表第一 器具及び備品 11"},
    "事務机": {"years": 15, "category": "器具及び備品", "subcategory": "事務机、事務いす", "basis": "別表第一 器具及び備品 1"},
    "事務椅子": {"years": 15, "category": "器具及び備品", "subcategory": "事務机、事務いす", "basis": "別表第一 器具及び備品 1"},
    "デスク": {"years": 15, "category": "器具及び備品", "subcategory": "事務机、事務いす", "basis": "別表第一 器具及び備品 1"},
    "椅子": {"years": 15, "category": "器具及び備品", "subcategory": "事務机、事務いす", "basis": "別表第一 器具及び備品 1"},
    "キャビネット": {"years": 15, "category": "器具及び備品", "subcategory": "金属製のもの", "basis": "別表第一 器具及び備品 1"},
    "エアコン": {"years": 6, "category": "器具及び備品", "subcategory": "冷暖房設備", "basis": "別表第一 器具及び備品 6"},
    "空調機": {"years": 6, "category": "器具及び備品", "subcategory": "冷暖房設備", "basis": "別表第一 器具及び備品 6"},
    "冷暖房": {"years": 6, "category": "器具及び備品", "subcategory": "冷暖房設備", "basis": "別表第一 器具及び備品 6"},
    "複合機": {"years": 5, "category": "器具及び備品", "subcategory": "事務機器", "basis": "別表第一 器具及び備品 11"},
    "プリンター": {"years": 5, "category": "器具及び備品", "subcategory": "事務機器", "basis": "別表第一 器具及び備品 11"},
    "コピー機": {"years": 5, "category": "器具及び備品", "subcategory": "事務機器", "basis": "別表第一 器具及び備品 11"},
    "電話機": {"years": 6, "category": "器具及び備品", "subcategory": "通信機器", "basis": "別表第一 器具及び備品 11"},
    "ディスプレイ": {"years": 5, "category": "器具及び備品", "subcategory": "電子計算機", "basis": "別表第一 器具及び備品 11"},
    "モニター": {"years": 5, "category": "器具及び備品", "subcategory": "電子計算機", "basis": "別表第一 器具及び備品 11"},

    # 車両運搬具
    "自動車": {"years": 6, "category": "車両運搬具", "subcategory": "普通自動車", "basis": "別表第一 車両及び運搬具"},
    "普通車": {"years": 6, "category": "車両運搬具", "subcategory": "普通自動車", "basis": "別表第一 車両及び運搬具"},
    "乗用車": {"years": 6, "category": "車両運搬具", "subcategory": "普通自動車", "basis": "別表第一 車両及び運搬具"},
    "軽自動車": {"years": 4, "category": "車両運搬具", "subcategory": "軽自動車", "basis": "別表第一 車両及び運搬具"},
    "トラック": {"years": 5, "category": "車両運搬具", "subcategory": "貨物自動車", "basis": "別表第一 車両及び運搬具"},
    "フォークリフト": {"years": 4, "category": "車両運搬具", "subcategory": "フォークリフト", "basis": "別表第一 車両及び運搬具"},

    # 機械装置
    "工作機械": {"years": 10, "category": "機械装置", "subcategory": "金属加工機械", "basis": "別表第二 機械及び装置"},
    "製造装置": {"years": 10, "category": "機械装置", "subcategory": "一般産業用機械", "basis": "別表第二 機械及び装置"},
    "コンベヤー": {"years": 10, "category": "機械装置", "subcategory": "運搬機械", "basis": "別表第二 機械及び装置"},

    # 建物附属設備
    "照明設備": {"years": 15, "category": "建物附属設備", "subcategory": "電気設備", "basis": "別表第一 建物附属設備"},
    "電気設備": {"years": 15, "category": "建物附属設備", "subcategory": "電気設備", "basis": "別表第一 建物附属設備"},
    "給排水設備": {"years": 15, "category": "建物附属設備", "subcategory": "給排水設備", "basis": "別表第一 建物附属設備"},
    "消火設備": {"years": 8, "category": "建物附属設備", "subcategory": "消火・防災設備", "basis": "別表第一 建物附属設備"},
    "エレベーター": {"years": 17, "category": "建物附属設備", "subcategory": "昇降機設備", "basis": "別表第一 建物附属設備"},

    # ソフトウェア
    "ソフトウェア": {"years": 5, "category": "無形固定資産", "subcategory": "ソフトウェア（複写販売用以外）", "basis": "別表第三 無形減価償却資産"},
    "システム": {"years": 5, "category": "無形固定資産", "subcategory": "ソフトウェア", "basis": "別表第三 無形減価償却資産"},

    # 建物
    "事務所": {"years": 50, "category": "建物", "subcategory": "鉄骨鉄筋コンクリート造（事務所用）", "basis": "別表第一 建物"},
    "工場": {"years": 38, "category": "建物", "subcategory": "鉄骨鉄筋コンクリート造（工場用）", "basis": "別表第一 建物"},
    "倉庫": {"years": 38, "category": "建物", "subcategory": "鉄骨鉄筋コンクリート造（倉庫用）", "basis": "別表第一 建物"},
}


def _normalize_description(description: str) -> str:
    """Normalize asset description for matching."""
    # 全角→半角、小文字化、空白除去
    normalized = description.lower()
    normalized = normalized.replace("　", " ").strip()
    return normalized


def _lookup_master(description: str) -> Optional[Dict[str, Any]]:
    """
    Look up useful life from master data.
    Returns match if found, None otherwise.
    """
    normalized = _normalize_description(description)

    for keyword, data in USEFUL_LIFE_MASTER.items():
        if keyword.lower() in normalized:
            return {
                "useful_life_years": data["years"],
                "category": data["category"],
                "subcategory": data["subcategory"],
                "legal_basis": data["basis"],
                "confidence": 0.95,  # High confidence for master match
                "source": "master_lookup",
            }

    return None


def _build_gemini_prompt(asset_description: str, asset_category: Optional[str] = None) -> str:
    """Build prompt for Gemini API."""

    # Include reference table in prompt
    reference_examples = """
【主要な法定耐用年数（参考）】
- パソコン、ノートPC: 4年（器具及び備品・電子計算機）
- サーバー: 5年（器具及び備品・電子計算機）
- 事務机、事務椅子: 15年（器具及び備品）
- エアコン、空調機: 6年（器具及び備品・冷暖房設備）
- 複合機、プリンター: 5年（器具及び備品・事務機器）
- 普通自動車: 6年（車両運搬具）
- 軽自動車: 4年（車両運搬具）
- トラック: 5年（車両運搬具）
- ソフトウェア: 5年（無形固定資産）
- 電気設備: 15年（建物附属設備）
- 消火設備: 8年（建物附属設備）
"""

    category_hint = f"\n資産カテゴリ: {asset_category}" if asset_category else ""

    prompt = f"""あなたは日本の税務に詳しい専門家です。
以下の固定資産について、減価償却資産の耐用年数等に関する省令に基づいて、法定耐用年数を推定してください。

【資産の説明】
{asset_description}{category_hint}

{reference_examples}

以下のJSON形式で回答してください。推測が困難な場合はconfidenceを低く設定してください。

{{
    "useful_life_years": <耐用年数（整数）>,
    "category": "<資産区分（器具及び備品、車両運搬具、機械装置、建物附属設備、無形固定資産など）>",
    "subcategory": "<細目>",
    "legal_basis": "<法的根拠（別表第○など）>",
    "confidence": <0.0-1.0の信頼度>,
    "reasoning": "<判断理由の簡潔な説明>"
}}

JSON形式のみで回答してください。"""

    return prompt


def _call_gemini_api(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Call Gemini API and parse response.
    Returns parsed JSON or None on failure.
    """
    if not GENAI_AVAILABLE:
        return None

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)

        # Use Gemini 1.5 Flash for fast response
        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent results
                "max_output_tokens": 500,
            }
        )

        # Parse JSON from response
        text = response.text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)
        result["source"] = "gemini_api"
        return result

    except json.JSONDecodeError:
        # JSON parsing failed
        return None
    except Exception:
        # API error - don't expose details in logs
        return None


def estimate_useful_life(
    asset_description: str,
    asset_category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Estimate the legal useful life (耐用年数) of a fixed asset.

    Uses a two-stage approach:
    1. First, look up in master data for exact/partial matches
    2. If no match, use Gemini API for intelligent estimation

    Args:
        asset_description: Description of the asset (e.g., "サーバー新設工事")
        asset_category: Optional category hint (e.g., "器具及び備品")

    Returns:
        dict with keys:
            - useful_life_years: int - Estimated useful life in years
            - category: str - Asset category
            - subcategory: str - Asset subcategory (optional)
            - legal_basis: str - Legal basis reference
            - confidence: float - Confidence score (0.0-1.0)
            - source: str - "master_lookup" or "gemini_api" or "default"
            - reasoning: str - Explanation (optional, from Gemini)

    Example:
        >>> result = estimate_useful_life("Dell PowerEdge サーバー")
        >>> print(result)
        {
            "useful_life_years": 5,
            "category": "器具及び備品",
            "subcategory": "電子計算機（サーバー用）",
            "legal_basis": "別表第一 器具及び備品 11",
            "confidence": 0.95,
            "source": "master_lookup"
        }
    """
    if not asset_description:
        return {
            "useful_life_years": 0,
            "category": "不明",
            "subcategory": None,
            "legal_basis": "判定不可",
            "confidence": 0.0,
            "source": "error",
            "error": "asset_description is required",
        }

    # Stage 1: Master lookup (fast, high confidence)
    master_result = _lookup_master(asset_description)
    if master_result:
        return master_result

    # Also check category hint if provided
    if asset_category:
        master_result = _lookup_master(asset_category)
        if master_result:
            master_result["confidence"] = 0.85  # Slightly lower confidence
            return master_result

    # Stage 2: Gemini API (intelligent estimation)
    prompt = _build_gemini_prompt(asset_description, asset_category)
    gemini_result = _call_gemini_api(prompt)
    if gemini_result and gemini_result.get("useful_life_years"):
        return gemini_result

    # Fallback: Default values with low confidence
    return {
        "useful_life_years": 5,  # Common default
        "category": "不明",
        "subcategory": None,
        "legal_basis": "要確認",
        "confidence": 0.3,
        "source": "default",
        "note": "マスタ照合・API推定とも該当なし。手動確認を推奨。",
    }


def estimate_useful_life_batch(
    items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Estimate useful life for multiple items.

    Args:
        items: List of dicts with "description" and optional "category" keys

    Returns:
        List of estimation results
    """
    results = []
    for item in items:
        description = item.get("description", "")
        category = item.get("category")
        result = estimate_useful_life(description, category)
        result["original_description"] = description
        results.append(result)
    return results


# ============================================================================
# Feature flag helper
# ============================================================================
def is_useful_life_enabled() -> bool:
    """Check if useful life estimation is available."""
    # Master lookup is always available
    # Gemini API requires API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return GENAI_AVAILABLE and bool(api_key)


def get_feature_status() -> Dict[str, Any]:
    """Get feature status for debugging."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return {
        "genai_available": GENAI_AVAILABLE,
        "api_key_set": bool(api_key),
        "master_entries": len(USEFUL_LIFE_MASTER),
        "enabled": is_useful_life_enabled(),
    }


# ============================================================================
# CLI for testing
# ============================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        description = " ".join(sys.argv[1:])
    else:
        description = "Dell PowerEdge サーバー"

    print(f"Estimating useful life for: {description}")
    print("-" * 50)

    result = estimate_useful_life(description)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("-" * 50)
    print(f"Feature status: {get_feature_status()}")
