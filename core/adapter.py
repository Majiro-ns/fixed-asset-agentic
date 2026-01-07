from typing import Any, Dict, List

from core import schema


def _get_first(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return default


def _normalize_vendor(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _to_quantity_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return str(value)
    return str(value).strip()


def _safe_number(value: Any) -> Any:
    return value if isinstance(value, (int, float)) else None


def _normalize_evidence(raw: Any, description: str) -> Dict[str, Any]:
    if isinstance(raw, dict):
        evidence = dict(raw)
    else:
        evidence = {}
    if not evidence.get("source_text"):
        evidence["source_text"] = description
    if "position_hint" not in evidence:
        evidence["position_hint"] = ""
    return evidence


def _build_line_items(items: Any) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    if not isinstance(items, list):
        return normalized

    for idx, raw in enumerate(items, start=1):
        description = _get_first(raw, ["item_description", "description"], default="") if isinstance(raw, dict) else ""
        quantity = _to_quantity_str(raw.get("quantity")) if isinstance(raw, dict) else ""
        unit_price = _safe_number(raw.get("unit_price")) if isinstance(raw, dict) else None
        amount = _safe_number(raw.get("amount")) if isinstance(raw, dict) else None

        normalized.append(
            {
                "line_no": idx,
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

    return normalized


def adapt_opal_to_v1(opal: Dict[str, Any]) -> Dict[str, Any]:
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
