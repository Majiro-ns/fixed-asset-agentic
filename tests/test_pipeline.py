from core.adapter import adapt_opal_to_v1
from core.classifier import classify_document
from core.policy import load_policy


def test_adapter_shapes_schema():
    opal = {
        "invoice_date": "2024-01-01",
        "vendor": "ACME Corp",
        "line_items": [
            {"item_description": "server install", "amount": 5000, "quantity": 1},
        ],
    }
    doc = adapt_opal_to_v1(opal)
    assert doc["version"] == "v1.0"
    assert doc["document_info"]["vendor"] == "ACME Corp"
    assert doc["line_items"][0]["line_no"] == 1
    assert "classification" in doc["line_items"][0]


def test_classifier_guidance_with_threshold_policy():
    opal = {"line_items": [{"description": "unknown item", "amount": 2_000_000}]}
    doc = adapt_opal_to_v1(opal)
    policy = load_policy(None)
    policy["thresholds"]["guidance_amount_jpy"] = 1_000_000
    result = classify_document(doc, policy)
    item = result["line_items"][0]
    assert item["classification"] == "GUIDANCE"
    assert "policy:amount_threshold" in item.get("flags", [])


def test_policy_missing_returns_defaults():
    policy = load_policy("does_not_exist.json")
    assert policy["keywords"]["asset_add"] == []
    assert policy["thresholds"]["guidance_amount_jpy"] is None
    assert policy["regex"]["always_guidance"] is None
