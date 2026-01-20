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
    answers: Optional[Dict[str, str]] = None


class ClassifyResponse(BaseModel):
    decision: str
    reasons: List[str]
    evidence: List[Dict[str, Any]]
    questions: List[str]
    metadata: Dict[str, Any]
    # WIN+1 additive fields
    is_valid_document: bool
    confidence: float
    error_code: Optional[str] = None
    trace: List[str]
    missing_fields: List[str]
    why_missing_matters: List[str]


def _format_classify_response(doc: Dict[str, Any], trace_steps: Optional[List[str]] = None) -> ClassifyResponse:
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
                    "confidence": ev.get("confidence", 0.8),  # WIN+1: default 0.8
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
    
    # WIN+1: additive fields
    is_valid_document = bool(doc.get("document_info")) and len(line_items) > 0
    # Calculate confidence: average of evidence confidences, default to 0.7 if no evidence
    confidences = [e.get("confidence", 0.8) for e in evidence]
    confidence = sum(confidences) / len(confidences) if confidences else 0.7
    
    # missing_fields and why_missing_matters: only for GUIDANCE
    missing_fields: List[str] = []
    why_missing_matters: List[str] = []
    if decision == "GUIDANCE":
        # Extract missing field hints from flags and questions
        for item in guidance_items:
            flags = item.get("flags", [])
            desc = item.get("description", "")
            # Heuristic: flags often indicate missing info
            if flags:
                missing_fields.extend([f"{desc}:{f}" for f in flags if isinstance(f, str)])
                why_missing_matters.append(f"Missing information in '{desc}' prevents automatic classification")
        # Deduplicate
        missing_fields = list(set(missing_fields))
        why_missing_matters = list(set(why_missing_matters))
    
    # trace: execution steps
    if trace_steps is None:
        trace_steps = ["extract", "parse", "rules", "format"]
    
    return ClassifyResponse(
        decision=decision,
        reasons=reasons,
        evidence=evidence,
        questions=questions,
        metadata=metadata,
        is_valid_document=is_valid_document,
        confidence=confidence,
        error_code=None,
        trace=trace_steps,
        missing_fields=missing_fields,
        why_missing_matters=why_missing_matters,
    )


@app.get("/healthz")
@app.get("/health")
async def healthz() -> Dict[str, bool]:
    """Health check endpoint. Cloud Run reserves /healthz, so /health also works."""
    return {"ok": True}

@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "Fixed Asset Classification API", "version": "1.0.0"}


@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest) -> ClassifyResponse:
    """
    Classify fixed asset items from Opal JSON.
    
    Uses existing core.adapter and core.classifier functions.
    WIN+1: Supports agentic loop with answers for GUIDANCE cases.
    """
    try:
        trace_steps = ["extract"]
        # Use existing pipeline functions
        opal_json = request.opal_json
        
        # Normalize using adapter
        normalized = adapt_opal_to_v1(opal_json)
        trace_steps.append("parse")
        
        # Load policy (default to company_default.json if not provided)
        policy_path = request.policy_path
        if not policy_path:
            default_policy = PROJECT_ROOT / "policies" / "company_default.json"
            if default_policy.exists():
                policy_path = str(default_policy)
        
        policy = load_policy(policy_path)
        
        # Classify using classifier
        classified = classify_document(normalized, policy)
        trace_steps.append("rules")
        
        # Format initial response
        initial_response = _format_classify_response(classified, trace_steps=trace_steps.copy())
        
        # WIN+1: Minimal agentic loop - if GUIDANCE and answers provided, try rerun
        if initial_response.decision == "GUIDANCE" and request.answers and initial_response.missing_fields:
            # Check if answers cover missing fields
            answered_fields = set(request.answers.keys())
            missing_set = set(initial_response.missing_fields)
            # Simple heuristic: if answers match any missing field pattern
            if answered_fields and any(k in str(mf).lower() for mf in missing_set for k in answered_fields):
                trace_steps.append("rerun_with_answers")
                # Apply answers to opal_json (merge into line items or document_info)
                enhanced_opal = opal_json.copy()
                # Simple merge: add answers to document_info context
                if "document_info" not in enhanced_opal:
                    enhanced_opal["document_info"] = {}
                enhanced_opal["document_info"]["user_answers"] = request.answers
                
                # Rerun classification
                enhanced_normalized = adapt_opal_to_v1(enhanced_opal)
                enhanced_classified = classify_document(enhanced_normalized, policy)
                trace_steps.append("format")
                return _format_classify_response(enhanced_classified, trace_steps=trace_steps)
        
        trace_steps.append("format")
        return _format_classify_response(classified, trace_steps=trace_steps)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
