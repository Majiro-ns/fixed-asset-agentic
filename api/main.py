# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.adapter import adapt_opal_to_v1
from core.classifier import classify_document
from core.policy import load_policy

PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="Fixed Asset Classification API", version="1.0.0")


class ClassifyRequest(BaseModel):
    opal_json: Dict[str, Any]
    policy_path: Optional[str] = None


class ClassifyResponse(BaseModel):
    decision: str
    reasons: List[str]
    evidence: List[Dict[str, Any]]
    questions: List[str]
    metadata: Dict[str, Any]


def _format_classify_response(doc: Dict[str, Any]) -> ClassifyResponse:
    """
    Convert pipeline output to API response format.
    Maps existing classifier/pipeline outputs to decision/reasons/evidence/questions/metadata.
    """
    line_items = doc.get("line_items", [])
    
    # decision: aggregate classifications (GUIDANCE takes priority, then most common)
    classifications = []
    guidance_items = []
    for item in line_items:
        if isinstance(item, dict):
            cls = item.get("classification")
            if cls:
                classifications.append(cls)
                if cls == "GUIDANCE":
                    guidance_items.append(item)
    
    if guidance_items:
        decision = "GUIDANCE"
    elif classifications:
        # Most common classification
        decision = max(set(classifications), key=classifications.count)
    else:
        decision = "UNKNOWN"
    
    # reasons: from rationale_ja and flags
    reasons: List[str] = []
    for item in line_items:
        if isinstance(item, dict):
            rationale = item.get("rationale_ja")
            if rationale:
                reasons.append(rationale)
            flags = item.get("flags", [])
            for flag in flags:
                if isinstance(flag, str) and flag not in reasons:
                    reasons.append(f"flag: {flag}")
    
    # evidence: from line_item evidence
    evidence: List[Dict[str, Any]] = []
    for item in line_items:
        if isinstance(item, dict):
            ev = item.get("evidence")
            if isinstance(ev, dict):
                evidence_item = {
                    "line_no": item.get("line_no"),
                    "description": item.get("description"),
                    "source_text": ev.get("source_text", ""),
                    "position_hint": ev.get("position_hint", ""),
                }
                # Include snippets if available
                snippets = ev.get("snippets")
                if snippets:
                    evidence_item["snippets"] = snippets
                evidence.append(evidence_item)
    
    # questions: for GUIDANCE items, generate questions from flags
    questions: List[str] = []
    for item in guidance_items:
        if isinstance(item, dict):
            flags = item.get("flags", [])
            desc = item.get("description", "")
            if flags:
                flag_str = ", ".join(flags) if isinstance(flags, list) else str(flags)
                questions.append(f"Line {item.get('line_no', '?')}: {desc} - flags: {flag_str}")
            else:
                questions.append(f"Line {item.get('line_no', '?')}: {desc} - requires manual review")
    
    # metadata: document_info, totals, version, etc.
    metadata: Dict[str, Any] = {
        "version": doc.get("version", ""),
        "document_info": doc.get("document_info", {}),
        "totals": doc.get("totals", {}),
        "line_item_count": len(line_items),
        "classification_counts": {
            "GUIDANCE": sum(1 for c in classifications if c == "GUIDANCE"),
            "CAPITAL_LIKE": sum(1 for c in classifications if c == "CAPITAL_LIKE"),
            "EXPENSE_LIKE": sum(1 for c in classifications if c == "EXPENSE_LIKE"),
        },
    }
    
    return ClassifyResponse(
        decision=decision,
        reasons=reasons,
        evidence=evidence,
        questions=questions,
        metadata=metadata,
    )


@app.get("/healthz")
async def healthz() -> Dict[str, bool]:
    """Health check endpoint."""
    return {"ok": True}


@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest) -> ClassifyResponse:
    """
    Classify fixed asset items from Opal JSON.
    
    Uses existing core.adapter and core.classifier functions.
    """
    try:
        # Use existing pipeline functions
        opal_json = request.opal_json
        
        # Normalize using adapter
        normalized = adapt_opal_to_v1(opal_json)
        
        # Load policy (default to company_default.json if not provided)
        policy_path = request.policy_path
        if not policy_path:
            default_policy = PROJECT_ROOT / "policies" / "company_default.json"
            if default_policy.exists():
                policy_path = str(default_policy)
        
        policy = load_policy(policy_path)
        
        # Classify using classifier
        classified = classify_document(normalized, policy)
        
        # Format response
        return _format_classify_response(classified)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
