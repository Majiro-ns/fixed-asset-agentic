# -*- coding: utf-8 -*-
import re
from typing import Any, Dict, List, Optional

from core import schema


CAPITAL_KEYWORDS = [
    "更新",
    "新設",
    "設置",
    "増設",
    "購入",
    "導入",
    "構築",
    "整備",
    "改修",
]

EXPENSE_KEYWORDS = [
    "保守",
    "点検",
    "修理",
    "修繕",
    "調整",
    "清掃",
    "清拭",
    "消耗品",
    "雑費",
    "メンテナンス",
    "維持",
    "管理",
    "交換",
    "補修",
    "年間",
    "定期",
    "契約",
]

MIXED_KEYWORDS = [
    "一式",
    "撤去",
    "移設",
    "既設",
]

LABEL_JA = {
    schema.CAPITAL_LIKE: "資産寄り",
    schema.EXPENSE_LIKE: "費用寄り",
    schema.GUIDANCE: "要確認（判定しません）",
}

GUIDANCE_RATIONALE = "判断が割れる可能性があるため判定しません"


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


def _apply_tax_rules(
    amount: Optional[float],
    total_amount: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Apply Japanese tax amount thresholds (10/20/30/60万).
    Returns list of {rule_id, reason, suggests_guidance}.
    suggest_guidance=True means: set classification to GUIDANCE (stop-first).
    """
    if not isinstance(amount, (int, float)) or amount <= 0:
        return []
    rules: List[Dict[str, Any]] = []
    if amount < 100_000:
        rules.append({
            "rule_id": "R-AMOUNT-003",
            "reason": "10万円未満のため少額固定資産（費用処理可能）の可能性",
            "suggests_guidance": False,
        })
    elif amount < 200_000:
        rules.append({
            "rule_id": "R-AMOUNT-100k200k",
            "reason": "10万円以上20万円未満のため3年一括償却等の取扱いの確認が必要",
            "suggests_guidance": True,
        })
    elif amount < 300_000:
        rules.append({
            "rule_id": "R-AMOUNT-001",
            "reason": "20万円以上30万未満のため一括償却資産の可能性（要確認）",
            "suggests_guidance": True,
        })
        rules.append({
            "rule_id": "R-AMOUNT-SME300k",
            "reason": "30万円未満中小企業特例の適用可能性のため要確認",
            "suggests_guidance": True,
        })
    elif amount < 600_000:
        rules.append({
            "rule_id": "R-AMOUNT-001",
            "reason": "20万円以上60万円未満のため一括償却資産の取扱い",
            "suggests_guidance": False,
        })
    else:
        rules.append({
            "rule_id": "R-AMOUNT-600k",
            "reason": "60万円以上のため修繕費vs資本的支出の判定には追加情報が必要",
            "suggests_guidance": True,
        })
    return rules


def _calculate_confidence(
    classification: str,
    cap_hits: List[str],
    exp_hits: List[str],
    mixed_hits: List[str],
    guidance_hits: List[str],
    flags: List[str],
) -> float:
    """
    分類の確信度を計算する。
    - キーワードが明確にヒット: 0.85〜0.95
    - 混在・競合: 0.50〜0.65
    - キーワードなし: 0.30〜0.50
    """
    if classification == schema.CAPITAL_LIKE:
        # 資産寄り判定: キーワード数に応じて確信度UP
        base = 0.85
        bonus = min(len(cap_hits) - 1, 2) * 0.03  # 追加キーワードで+0.03ずつ
        return min(base + bonus, 0.95)
    elif classification == schema.EXPENSE_LIKE:
        # 費用寄り判定: キーワード数に応じて確信度UP
        base = 0.85
        bonus = min(len(exp_hits) - 1, 2) * 0.03
        return min(base + bonus, 0.95)
    else:
        # GUIDANCE: 理由によって確信度を変える
        if "conflicting_keywords" in flags:
            # 両方のキーワードがある = 判断が難しい
            return 0.55
        elif "no_keywords" in flags:
            # キーワードなし = 情報不足
            return 0.40
        elif mixed_hits:
            # 混在キーワード
            return 0.60
        elif guidance_hits:
            # ポリシーで強制GUIDANCE
            return 0.65
        else:
            return 0.50


def classify_line_item(
    item: Dict[str, Any],
    policy: Optional[Dict[str, Any]] = None,
    doc: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # descriptionに加え、evidence.source_textからもキーワード検索
    description = str(item.get("description") or "")
    evidence = item.get("evidence") or {}
    source_text = str(evidence.get("source_text") or "") if isinstance(evidence, dict) else ""
    # 両方を結合してキーワード検索対象とする
    search_text = f"{description} {source_text}"
    policy_cfg = _safe_policy(policy)
    policy_keywords = policy_cfg.get("keywords") if isinstance(policy_cfg.get("keywords"), dict) else {}
    capital_keywords = _merge_keywords(CAPITAL_KEYWORDS, policy_keywords.get("asset_add", [])) if isinstance(policy_keywords, dict) else CAPITAL_KEYWORDS
    expense_keywords = _merge_keywords(EXPENSE_KEYWORDS, policy_keywords.get("expense_add", [])) if isinstance(policy_keywords, dict) else EXPENSE_KEYWORDS
    guidance_keywords = policy_keywords.get("guidance_add", []) if isinstance(policy_keywords, dict) else []

    cap_hits = _find_keywords(search_text, capital_keywords)
    exp_hits = _find_keywords(search_text, expense_keywords)
    mixed_hits = _find_keywords(search_text, MIXED_KEYWORDS)
    guidance_hits = _find_keywords(search_text, guidance_keywords)

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

    # Tax rules (10/20/30/60万): add flags as reference info
    # キーワードで明確に判定できている場合は税ルールで上書きしない
    total_amount = None
    if isinstance(doc, dict):
        totals = doc.get("totals") or {}
        total_amount = totals.get("total") if isinstance(totals, dict) else None
    tax_results = _apply_tax_rules(amount_value if isinstance(amount_value, (int, float)) and not isinstance(amount_value, bool) else None, total_amount)
    for tr in tax_results:
        flag = f"tax_rule:{tr['rule_id']}:{tr['reason']}"
        _append_flag(flags, flag)
        # 既にGUIDANCEの場合のみ税ルールを適用（CAPITAL_LIKE/EXPENSE_LIKEは維持）
        if tr.get("suggests_guidance") is True and classification == schema.GUIDANCE:
            classification = schema.GUIDANCE

    label_ja = LABEL_JA[classification]

    if classification == schema.CAPITAL_LIKE:
        rationale_ja = f"明細に「{cap_hits[0]}」が含まれるため資産寄りと判定"
    elif classification == schema.EXPENSE_LIKE:
        rationale_ja = f"明細に「{exp_hits[0]}」が含まれるため費用寄りと判定"
    else:
        rationale_ja = GUIDANCE_RATIONALE

    # 確信度を計算
    confidence = _calculate_confidence(
        classification, cap_hits, exp_hits, mixed_hits, guidance_hits, flags
    )

    item.update(
        {
            "classification": classification,
            "label_ja": label_ja,
            "rationale_ja": rationale_ja,
            "flags": flags,
            "confidence": confidence,
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
            classify_line_item(item, policy, doc=doc)

    return doc
