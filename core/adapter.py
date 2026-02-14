import logging
import re
from typing import Any, Dict, List

from core import schema

logger = logging.getLogger(__name__)

# Regex to detect summary/total rows that should not be classified as line items
_SUMMARY_ROW_RE = re.compile(
    r"^(小計|消費税|合計|税込合計|税抜合計|値引|割引|出精値引)"
)


def _get_first(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """Return the value of the first key found in *data* that is not None or empty string.

    Args:
        data: Source dictionary to search.
        keys: Ordered list of candidate key names.
        default: Fallback value when no key matches.

    Returns:
        The first non-empty value found, or *default*.
    """
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return default


def _normalize_vendor(value: Any) -> Any:
    """Normalize a vendor value to ``None`` when it is absent or blank.

    Args:
        value: Raw vendor value (may be ``None``, empty string, or a valid name).

    Returns:
        The original value if it is a non-blank string, otherwise ``None``.
    """
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _to_quantity_str(value: Any) -> str:
    """Convert a quantity value to its string representation.

    Floats that represent whole numbers (e.g. ``3.0``) are converted to ``"3"``.

    Args:
        value: Raw quantity (int, float, str, or ``None``).

    Returns:
        A stripped string representation, or ``""`` when *value* is ``None``.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return str(value)
    return str(value).strip()


def _safe_number(value: Any) -> Any:
    """Return *value* unchanged if it is numeric (``int`` or ``float``), otherwise ``None``.

    Args:
        value: Any raw value to validate.

    Returns:
        The numeric value or ``None``.
    """
    return value if isinstance(value, (int, float)) else None


def _normalize_evidence(raw: Any, description: str) -> Dict[str, Any]:
    """Ensure the evidence dict always contains ``source_text`` and ``position_hint``.

    If *raw* is not a dict an empty one is created.  Missing ``source_text``
    defaults to *description*; missing ``position_hint`` defaults to ``""``.

    Args:
        raw: Raw evidence value from the upstream data (may be ``None`` or a dict).
        description: Fallback text used when ``source_text`` is absent.

    Returns:
        A normalized evidence dictionary.
    """
    if isinstance(raw, dict):
        evidence = dict(raw)
    else:
        evidence = {}
    if not evidence.get("source_text"):
        evidence["source_text"] = description
    if "position_hint" not in evidence:
        evidence["position_hint"] = ""
    return evidence


def _is_summary_row(description: str) -> bool:
    """Return True if *description* looks like a summary row (subtotal, tax, total, etc.).

    These rows should be excluded from classification because they represent
    aggregated amounts, not individual line items.

    Args:
        description: The item description text.

    Returns:
        True if this is a summary/total row that should be filtered out.
    """
    return bool(_SUMMARY_ROW_RE.match(description.strip()))


def _build_line_items(items: Any) -> List[Dict[str, Any]]:
    """Convert raw line-item entries into the normalized v1 schema format.

    Each item receives a sequential ``line_no``, normalized description/quantity/
    unit_price/amount fields, and placeholder classification/rationale/flags/evidence
    fields ready for the classifier stage.

    Summary rows (subtotal, tax, total, discount) are filtered out before
    normalization to prevent them from being classified as line items.

    Args:
        items: A list of raw line-item dicts.  Non-list inputs return an empty list.

    Returns:
        List of normalized line-item dicts conforming to v1 schema.
    """
    normalized: List[Dict[str, Any]] = []
    if not isinstance(items, list):
        return normalized

    total_before = len(items)
    line_no = 0
    for raw in items:
        description = _get_first(raw, ["item_description", "description"], default="") if isinstance(raw, dict) else ""

        # Filter out summary rows (subtotal, tax, total, discount, etc.)
        if isinstance(raw, dict) and _is_summary_row(description):
            continue

        line_no += 1
        quantity = _to_quantity_str(raw.get("quantity")) if isinstance(raw, dict) else ""
        unit_price = _safe_number(raw.get("unit_price")) if isinstance(raw, dict) else None
        amount = _safe_number(raw.get("amount")) if isinstance(raw, dict) else None

        normalized.append(
            {
                "line_no": line_no,
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
                "classification": None,
                "rationale": "",
                "flags": [],
                "evidence": _normalize_evidence(raw.get("evidence") if isinstance(raw, dict) else None, description),
            }
        )

    filtered_count = total_before - len(normalized)
    if filtered_count > 0:
        logger.info("Filtered %d summary row(s) from %d total items", filtered_count, total_before)

    return normalized


def adapt_opal_to_v1(opal: Dict[str, Any]) -> Dict[str, Any]:
    """Transform an OPAL-format extraction dict into the internal v1 schema.

    The v1 schema is the canonical intermediate representation used throughout
    the classification pipeline.  It contains ``version``, ``document_info``,
    ``line_items``, and ``totals`` sections.

    Args:
        opal: Raw extraction result in OPAL format (may be ``None`` or non-dict,
              in which case safe defaults are used).

    Returns:
        A dict conforming to v1 schema (``schema.VERSION``).
    """
    line_items_raw = opal.get("line_items") if isinstance(opal, dict) else []

    return {
        "version": schema.VERSION,
        "document_info": {
            "title": _get_first(opal, ["title"], default="見積書") if isinstance(opal, dict) else "見積書",
            "date": _get_first(opal, ["invoice_date", "date"], default="") if isinstance(opal, dict) else "",
            "vendor": _normalize_vendor(opal.get("vendor")) if isinstance(opal, dict) else None,
        },
        "line_items": _build_line_items(line_items_raw if line_items_raw is not None else []),
        "totals": {
            "subtotal": _safe_number(_get_first(opal, ["subtotal_amount", "subtotal"])) if isinstance(opal, dict) else None,
            "tax": _safe_number(_get_first(opal, ["tax_amount", "tax"])) if isinstance(opal, dict) else None,
            "total": _safe_number(_get_first(opal, ["total_amount", "total"])) if isinstance(opal, dict) else None,
        },
    }
