import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional


_EMPTY_POLICY = {
    "keywords": {
        "asset_add": [],
        "expense_add": [],
        "guidance_add": [],
    },
    "thresholds": {
        "guidance_amount_jpy": None,
    },
    "regex": {
        "always_guidance": None,
    },
}


def _fresh_policy() -> Dict[str, Any]:
    return deepcopy(_EMPTY_POLICY)


def _ensure_list_of_str(value: Any) -> list:
    if not isinstance(value, list):
        return []
    return [str(v) for v in value if isinstance(v, str)]


def _ensure_int_or_none(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return None


def _ensure_str_or_none(value: Any) -> Optional[str]:
    if isinstance(value, str) and value != "":
        return value
    return None


def load_policy(path: Optional[str]) -> Dict[str, Any]:
    """
    Load policy JSON. If path is None/empty/missing/invalid, return an empty policy shape.
    The returned dict always has the expected keys filled with empty defaults.
    """
    policy = _fresh_policy()

    if not path:
        return policy

    try:
        policy_path = Path(path)
    except (TypeError, ValueError):
        return policy

    if not policy_path.exists() or not policy_path.is_file():
        return policy

    try:
        with open(policy_path, "r", encoding="utf-8-sig") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return policy

    keywords = raw.get("keywords") if isinstance(raw, dict) else {}
    thresholds = raw.get("thresholds") if isinstance(raw, dict) else {}
    regex = raw.get("regex") if isinstance(raw, dict) else {}

    asset_add_raw = keywords.get("asset_add") if isinstance(keywords, dict) else []
    expense_add_raw = keywords.get("expense_add") if isinstance(keywords, dict) else []
    guidance_add_raw = keywords.get("guidance_add") if isinstance(keywords, dict) else []
    policy["keywords"]["asset_add"] = _ensure_list_of_str(asset_add_raw)
    policy["keywords"]["expense_add"] = _ensure_list_of_str(expense_add_raw)
    policy["keywords"]["guidance_add"] = _ensure_list_of_str(guidance_add_raw)

    guidance_amount = thresholds.get("guidance_amount_jpy") if isinstance(thresholds, dict) else None
    policy["thresholds"]["guidance_amount_jpy"] = _ensure_int_or_none(guidance_amount)

    always_guidance = regex.get("always_guidance") if isinstance(regex, dict) else None
    policy["regex"]["always_guidance"] = _ensure_str_or_none(always_guidance)

    return policy
