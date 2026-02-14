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
    # 明確に資産性なし（法人税基本通達7-3-3の2）
    "撤去",
    "廃棄",
    "処分",
    "解体",
    "除却",
    "原状回復",
    "養生",
    "仮設",
]

# 取得価額に算入すべきキーワード（運搬費等）
ASSET_INCLUSION_KEYWORDS = [
    "運搬",
    "運賃",
    "搬入",
    "配送",
    "据付",
    "荷造",
]

# 按分対象キーワード（資産/費用の金額比率で按分）
PRORATE_KEYWORDS = [
    "諸経費",
    "一般管理費",
    "現場管理費",
    "共通仮設",
]

MIXED_KEYWORDS = [
    "一式",
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
    """Return the subset of *keywords* that appear in *text*.

    Args:
        text: The text to search (typically a description or source_text).
        keywords: Candidate keywords to look for.

    Returns:
        List of matched keywords, preserving the order of *keywords*.
    """
    return [kw for kw in keywords if kw in text]


def _merge_keywords(base: List[str], additions: List[str]) -> List[str]:
    """Merge two keyword lists, preserving order and removing duplicates.

    Args:
        base: Primary keyword list.
        additions: Additional keywords to append (duplicates ignored).

    Returns:
        A new list containing all unique keywords from *base* then *additions*.
    """
    merged: List[str] = []
    seen = set()
    for kw in base + additions:
        if kw not in seen:
            merged.append(kw)
            seen.add(kw)
    return merged


def _safe_policy(policy: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return *policy* if it is a dict, otherwise return an empty policy skeleton.

    Args:
        policy: A policy configuration dict or ``None``.

    Returns:
        A dict guaranteed to have ``keywords``, ``thresholds``, and ``regex`` keys.
    """
    return policy if isinstance(policy, dict) else {"keywords": {}, "thresholds": {}, "regex": {}}


def _append_flag(flags: List[str], flag: str) -> None:
    """Append *flag* to *flags* only if it is not already present (dedup guard).

    Args:
        flags: Mutable list of flag strings.
        flag: The flag string to add.
    """
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
    """Classify a single line item as CAPITAL_LIKE, EXPENSE_LIKE, or GUIDANCE.

    Classification uses keyword matching against the item description and
    evidence source_text, policy overrides (regex, guidance keywords, amount
    thresholds), and Japanese tax-law rules (10万/20万/30万/60万 thresholds).
    The item dict is updated **in-place** with ``classification``, ``label_ja``,
    ``rationale_ja``, ``flags``, and ``confidence`` keys.

    Args:
        item: A normalized line-item dict (must contain at least ``description``).
        policy: Optional policy configuration for keyword/threshold overrides.
        doc: The parent document dict (used to retrieve ``totals`` for tax rules).

    Returns:
        The same *item* dict, updated with classification results.
    """
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
    asset_inclusion_hits = _find_keywords(search_text, ASSET_INCLUSION_KEYWORDS)
    prorate_hits = _find_keywords(search_text, PRORATE_KEYWORDS)

    flags: List[str] = []

    # 按分対象の場合はフラグを立てる（後で按分処理）
    if prorate_hits:
        flags.append(f"prorate:{prorate_hits[0]}")
        item["_prorate"] = True

    # 運搬費等は資産取得価額に算入
    if asset_inclusion_hits and not exp_hits:
        cap_hits = cap_hits or asset_inclusion_hits
        flags.append(f"asset_inclusion:{asset_inclusion_hits[0]}")

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
    keyword_based = classification in (schema.CAPITAL_LIKE, schema.EXPENSE_LIKE)
    total_amount = None
    if isinstance(doc, dict):
        totals = doc.get("totals") or {}
        total_amount = totals.get("total") if isinstance(totals, dict) else None
    tax_results = _apply_tax_rules(amount_value if isinstance(amount_value, (int, float)) and not isinstance(amount_value, bool) else None, total_amount)
    for tr in tax_results:
        flag = f"tax_rule:{tr['rule_id']}:{tr['reason']}"
        _append_flag(flags, flag)
        # 税ルールがGUIDANCEを示す場合でも、キーワードで明確に判定済みなら上書きしない
        if tr.get("suggests_guidance") is True and not keyword_based:
            classification = schema.GUIDANCE

    # 単価ベース判定: 単価が10万円未満の場合、個別では少額資産の可能性
    # CAPITAL_LIKE判定でも単価が10万未満なら GUIDANCE に引き上げ（Stop-first原則）
    unit_price = item.get("unit_price")
    if (
        classification == schema.CAPITAL_LIKE
        and isinstance(unit_price, (int, float))
        and not isinstance(unit_price, bool)
        and unit_price < 100_000
    ):
        classification = schema.GUIDANCE
        _append_flag(flags, f"tax_rule:R-UNIT-PRICE-100k:単価{int(unit_price):,}円が10万円未満のため少額資産の可能性（要確認）")

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


def _prorate_items(line_items: List[Dict[str, Any]]) -> None:
    """諸経費等の按分対象明細を、資産/費用の金額比率で按分する。

    _prorate フラグが立った明細の金額を、他の明細の CAPITAL_LIKE / EXPENSE_LIKE
    の金額比率で按分し、それぞれの分類に分配する。
    按分結果は元の明細を更新する（1円未満は経費側に寄せる）。
    """
    prorate_items = [it for it in line_items if isinstance(it, dict) and it.get("_prorate")]
    if not prorate_items:
        return

    capital_total = sum(
        (it.get("amount") or 0) for it in line_items
        if isinstance(it, dict) and it.get("classification") == schema.CAPITAL_LIKE and not it.get("_prorate")
    )
    expense_total = sum(
        (it.get("amount") or 0) for it in line_items
        if isinstance(it, dict) and it.get("classification") == schema.EXPENSE_LIKE and not it.get("_prorate")
    )
    base_total = capital_total + expense_total

    if base_total <= 0:
        return

    capital_ratio = capital_total / base_total

    for item in prorate_items:
        amt = item.get("amount") or 0
        if amt <= 0:
            continue
        # 経費按分額（1円未満は経費側に寄せる — 殿の指示）
        expense_share = int(amt * (1 - capital_ratio) + 0.5)
        capital_share = amt - expense_share

        item["_prorate_capital"] = capital_share
        item["_prorate_expense"] = expense_share
        # 按分結果に基づき分類（資産比率が高ければCAPITAL_LIKE）
        if capital_share >= expense_share:
            item["classification"] = schema.CAPITAL_LIKE
            item["rationale_ja"] = f"諸経費を按分: 資産¥{capital_share:,} / 経費¥{expense_share:,}"
        else:
            item["classification"] = schema.EXPENSE_LIKE
            item["rationale_ja"] = f"諸経費を按分: 経費¥{expense_share:,} / 資産¥{capital_share:,}"
        item["label_ja"] = LABEL_JA[item["classification"]]
        # 一時フラグ除去
        del item["_prorate"]


def classify_document(doc: Dict[str, Any], policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Classify every line item in a v1-schema document.

    Iterates over ``doc["line_items"]`` and applies :func:`classify_line_item`
    to each entry.  Non-dict items are silently skipped.
    After individual classification, prorate items (諸経費等) are distributed
    based on the capital/expense ratio.

    Args:
        doc: A normalized document dict (v1 schema).
        policy: Optional policy configuration passed through to the line-item
                classifier.

    Returns:
        The same *doc* dict with all line items classified in-place.
    """
    if not isinstance(doc, dict):
        return doc

    line_items = doc.get("line_items")
    if not isinstance(line_items, list):
        return doc

    for item in line_items:
        if isinstance(item, dict):
            classify_line_item(item, policy, doc=doc)

    # 諸経費の按分処理
    _prorate_items(line_items)

    return doc
