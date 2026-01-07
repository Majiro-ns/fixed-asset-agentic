import re
from typing import Any, Dict, List, Optional

from core import schema


CAPITAL_KEYWORDS = [
    "�X�V",
    "�V��",
    "����",
    "�ݒu",
    "�w��",
    "����",
    "�\\�z",
    "����",
    "����",
]

EXPENSE_KEYWORDS = [
    "�ێ�",
    "�_��",
    "���|",
    "����",
    "�C��",
    "����",
    "�����e",
    "�Z��",
]

MIXED_KEYWORDS = [
    "�P��",
    "���",
    "�ڐ�",
    "�p��",
    "����",
]

LABEL_JA = {
    schema.CAPITAL_LIKE: "���Y���",
    schema.EXPENSE_LIKE: "��p���",
    schema.GUIDANCE: "�v�m�F�i�f�肵�܂���j",
}

GUIDANCE_RATIONALE = "���f�������\\�������邽�ߒf�肵�܂���"


def _find_keywords(text: str, keywords: List[str]) -> List[str]:
    return [kw for kw in keywords if kw in text]


def _merge_keywords(base: List[str], additions: List[str]) -> List[str]:
    merged: List[str] = []
    seen = set()
    for kw in base + additions:
        if kw not in seen:
            merged.append(kw)
            seen.add(kw)
    return merged


def _safe_policy(policy: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return policy if isinstance(policy, dict) else {"keywords": {}, "thresholds": {}, "regex": {}}


def _append_flag(flags: List[str], flag: str) -> None:
    if flag not in flags:
        flags.append(flag)


def classify_line_item(item: Dict[str, Any], policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    description = str(item.get("description") or "")
    policy_cfg = _safe_policy(policy)
    policy_keywords = policy_cfg.get("keywords") if isinstance(policy_cfg.get("keywords"), dict) else {}
    capital_keywords = _merge_keywords(CAPITAL_KEYWORDS, policy_keywords.get("asset_add", [])) if isinstance(policy_keywords, dict) else CAPITAL_KEYWORDS
    expense_keywords = _merge_keywords(EXPENSE_KEYWORDS, policy_keywords.get("expense_add", [])) if isinstance(policy_keywords, dict) else EXPENSE_KEYWORDS
    guidance_keywords = policy_keywords.get("guidance_add", []) if isinstance(policy_keywords, dict) else []

    cap_hits = _find_keywords(description, capital_keywords)
    exp_hits = _find_keywords(description, expense_keywords)
    mixed_hits = _find_keywords(description, MIXED_KEYWORDS)
    guidance_hits = _find_keywords(description, guidance_keywords)

    flags: List[str] = []

    # Guidance if mixed keywords present, or both sides hit, or neither side hits.
    if mixed_hits:
        classification = schema.GUIDANCE
        flags.append(f"mixed_keyword:{mixed_hits[0]}")
    elif cap_hits and exp_hits:
        classification = schema.GUIDANCE
        flags.append("conflicting_keywords")
    elif cap_hits:
        classification = schema.CAPITAL_LIKE
    elif exp_hits:
        classification = schema.EXPENSE_LIKE
    else:
        classification = schema.GUIDANCE
        flags.append("no_keywords")

    # Stop-first: policy overrides only add more GUIDANCE reasons.
    regex_cfg = policy_cfg.get("regex") if isinstance(policy_cfg.get("regex"), dict) else {}
    always_guidance_pattern = regex_cfg.get("always_guidance") if isinstance(regex_cfg, dict) else None
    if isinstance(always_guidance_pattern, str) and always_guidance_pattern:
        try:
            if re.search(always_guidance_pattern, description):
                classification = schema.GUIDANCE
                _append_flag(flags, "policy:always_guidance")
        except re.error:
            pass

    if guidance_hits:
        classification = schema.GUIDANCE
        _append_flag(flags, f"policy:guidance_add:{guidance_hits[0]}")

    thresholds_cfg = policy_cfg.get("thresholds") if isinstance(policy_cfg.get("thresholds"), dict) else {}
    threshold_amount = thresholds_cfg.get("guidance_amount_jpy") if isinstance(thresholds_cfg, dict) else None
    amount_value = item.get("amount")
    if (
        classification == schema.GUIDANCE
        and isinstance(threshold_amount, (int, float))
        and not isinstance(threshold_amount, bool)
        and isinstance(amount_value, (int, float))
        and not isinstance(amount_value, bool)
        and amount_value >= threshold_amount
    ):
        _append_flag(flags, "policy:amount_threshold")

    label_ja = LABEL_JA[classification]

    if classification == schema.CAPITAL_LIKE:
        rationale_ja = f"�i�ڂɁu{cap_hits[0]}�v���܂܂�邽�ߎ��Y���Ɣ���"
    elif classification == schema.EXPENSE_LIKE:
        rationale_ja = f"�i�ڂɁu{exp_hits[0]}�v���܂܂�邽�ߔ�p���Ɣ���"
    else:
        rationale_ja = GUIDANCE_RATIONALE

    item.update(
        {
            "classification": classification,
            "label_ja": label_ja,
            "rationale_ja": rationale_ja,
            "flags": flags,
        }
    )
    return item


def classify_document(doc: Dict[str, Any], policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not isinstance(doc, dict):
        return doc

    line_items = doc.get("line_items")
    if not isinstance(line_items, list):
        return doc

    for item in line_items:
        if isinstance(item, dict):
            classify_line_item(item, policy)

    return doc
