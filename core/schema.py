VERSION = "v1.0"

CAPITAL_LIKE = "CAPITAL_LIKE"
EXPENSE_LIKE = "EXPENSE_LIKE"
GUIDANCE = "GUIDANCE"

"""
Frozen schema v1.0 keys:
- document_info.title, document_info.date, document_info.vendor
- line_items[].line_no, description, quantity, unit_price, amount, classification, rationale, flags, evidence.source_text, evidence.position_hint
- totals.subtotal, totals.tax, totals.total
"""
