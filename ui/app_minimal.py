#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal Streamlit UI for fixed asset classification."""
import json
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent

st.set_page_config(page_title="Fixed Asset Classifier", layout="wide")

st.title("Fixed Asset Classification")
st.caption("Classify invoices/estimates into CAPITAL_LIKE / EXPENSE_LIKE / GUIDANCE")

# Sidebar: Service URL and demo case selector
with st.sidebar:
    st.markdown("### Configuration")
    service_url = st.text_input(
        "Service URL",
        value="https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app",
        key="service_url",
    )
    
    st.markdown("### Demo Cases")
    demo_cases_dir = ROOT_DIR / "data" / "demo"
    demo_cases = []
    if demo_cases_dir.exists():
        demo_cases = sorted([f.name for f in demo_cases_dir.glob("*.json")])
    
    if demo_cases:
        selected_demo = st.selectbox("Load Demo Case", ["None"] + demo_cases, key="demo_selector")
    else:
        selected_demo = "None"
    
    st.markdown("---")
    st.markdown("### PDF Upload (Optional)")
    st.caption("PDF upload is always available. Server-side feature flag status is shown when you upload a PDF.")

# Initialize session state
if "result" not in st.session_state:
    st.session_state.result = None
if "prev_result" not in st.session_state:
    st.session_state.prev_result = None
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "initial_opal" not in st.session_state:
    st.session_state.initial_opal = None

# Input section
st.markdown("## Input")

# PDF Upload (always available, server-side feature flag checked on upload)
uploaded_pdf = st.file_uploader("PDF Upload (Optional)", type=["pdf"], key="pdf_upload")
if uploaded_pdf:
    st.info(f"PDF uploaded: {uploaded_pdf.name} ({uploaded_pdf.size} bytes)")

# Opal JSON input (default flow)
opal_json_text = ""
if not uploaded_pdf:
    # Load demo case if selected
    if selected_demo != "None" and demo_cases:
        demo_path = demo_cases_dir / selected_demo
        try:
            demo_json = json.loads(demo_path.read_text(encoding="utf-8"))
            opal_json_text = st.text_area(
                "Opal JSON",
                height=200,
                value=json.dumps(demo_json, ensure_ascii=False, indent=2),
                key="opal_input",
            )
        except Exception as e:
            st.error(f"Failed to load demo case: {e}")
            opal_json_text = st.text_area(
                "Opal JSON",
                height=200,
                placeholder='{"invoice_date": "2024-01-01", "vendor": "ACME Corp", "line_items": [{"item_description": "server install", "amount": 5000, "quantity": 1}]}',
                key="opal_input",
            )
    else:
        opal_json_text = st.text_area(
            "Opal JSON",
            height=200,
            placeholder='{"invoice_date": "2024-01-01", "vendor": "ACME Corp", "line_items": [{"item_description": "server install", "amount": 5000, "quantity": 1}]}',
            key="opal_input",
        )

# Classify button (for Opal JSON)
if st.button("Classify (Opal JSON)", type="primary", use_container_width=True, disabled=bool(uploaded_pdf)):
    if not opal_json_text.strip():
        st.error("Please enter Opal JSON")
    else:
        try:
            opal_json = json.loads(opal_json_text)
            st.session_state.initial_opal = opal_json.copy()
            
            # Call Cloud Run API
            classify_url = f"{service_url}/classify"
            payload = {"opal_json": opal_json}
            
            with st.spinner("Classifying..."):
                response = requests.post(
                    classify_url,
                    json=payload,
                    timeout=15,
                )
                response.raise_for_status()
                result_data = response.json()
            
            # Store result (preserve previous for comparison)
            if st.session_state.result:
                st.session_state.prev_result = st.session_state.result.copy()
            st.session_state.result = result_data
            st.session_state.answers = {}
            
            st.rerun()
            
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
        except requests.exceptions.Timeout:
            st.error("Request timeout (15s). Service may be slow.")
        except requests.exceptions.RequestException as e:
            error_detail = ""
            if hasattr(e, "response") and e.response is not None:
                # Handle 422 validation errors specifically
                if e.response.status_code == 422:
                    try:
                        error_body = e.response.json()
                        error_detail = f"Validation error (422): {json.dumps(error_body, indent=2, ensure_ascii=False)}"
                    except:
                        error_detail = f"Validation error (422): {e.response.text}"
                else:
                    try:
                        error_detail = e.response.text
                    except:
                        error_detail = str(e)
            else:
                error_detail = str(e)
            st.error(f"API request failed: {error_detail}")
        except Exception as e:
            st.error(f"Classification failed: {e}")

# PDF Classify button (if PDF uploaded)
if uploaded_pdf:
    if st.button("Classify PDF", type="primary", use_container_width=True):
        try:
            # Call Cloud Run API /classify_pdf
            classify_pdf_url = f"{service_url}/classify_pdf"
            
            # Reset file pointer
            uploaded_pdf.seek(0)
            
            with st.spinner("Classifying PDF..."):
                files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
                response = requests.post(
                    classify_pdf_url,
                    files=files,
                    timeout=30,  # PDF processing may take longer
                )
                response.raise_for_status()
                result_data = response.json()
            
            # Store result (same as Opal JSON flow)
            if st.session_state.result:
                st.session_state.prev_result = st.session_state.result.copy()
            st.session_state.result = result_data
            st.session_state.answers = {}
            
            st.rerun()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e.response, 'status_code') else None
            
            # Handle 404: endpoint not available (demo accident prevention)
            if status_code == 404:
                st.error("**This deployment does not have /classify_pdf endpoint yet.**\n\n"
                        "The PDF upload feature may not be deployed on this server. "
                        "Please use POST /classify with Opal JSON instead.")
                # Continue to next iteration (no return in Streamlit button handler)
            
            # Handle 400/503: feature disabled or service unavailable
            if status_code in (400, 503):
                try:
                    error_body = e.response.json()
                    error_detail = error_body.get("detail", {})
                    
                    # Machine-readable check: detail.error == "PDF_CLASSIFY_DISABLED"
                    if isinstance(error_detail, dict) and error_detail.get("error") == "PDF_CLASSIFY_DISABLED":
                        how_to_enable = error_detail.get("how_to_enable", "Set PDF_CLASSIFY_ENABLED=1 on server")
                        message = error_detail.get("message", "PDF classification is disabled on this server")
                        fallback = error_detail.get("fallback", "Use POST /classify with Opal JSON instead")
                        st.error(f"**Server-side PDF_CLASSIFY_ENABLED=1 is required (feature is OFF on server).**\n\n"
                                f"Server message: {message}\n\n"
                                f"How to enable: {how_to_enable}\n\n"
                                f"Fallback: {fallback}\n\n"
                                "Note: UI always shows PDF upload option. Server-side feature flag status is determined by API response.")
                    else:
                        # Other 400/503 errors
                        st.error(f"PDF classification failed (HTTP {status_code}): {json.dumps(error_body, indent=2, ensure_ascii=False)}")
                except:
                    # Fallback: if JSON parsing fails, show raw response
                    response_text = e.response.text if hasattr(e.response, 'text') else str(e)
                    st.error(f"PDF classification failed (HTTP {status_code}): {response_text}")
            else:
                # Other HTTP errors (500, etc.)
                try:
                    error_body = e.response.json()
                    error_detail = error_body.get("detail", {})
                    # Check if detail is dict and has error field (consistent with 400/503 handling)
                    if isinstance(error_detail, dict) and error_detail.get("error") == "PDF_CLASSIFY_ERROR":
                        message = error_detail.get("message", "PDF classification failed")
                        st.error(f"**PDF classification error (HTTP {status_code}):**\n\n{message}")
                    else:
                        st.error(f"PDF classification failed (HTTP {status_code}): {json.dumps(error_body, indent=2, ensure_ascii=False)}")
                except:
                    st.error(f"PDF classification failed (HTTP {status_code}): {str(e)}")
        except requests.exceptions.Timeout:
            st.error("Request timeout (30s). PDF processing may take longer.")
        except requests.exceptions.RequestException as e:
            st.error(f"PDF classification request failed: {str(e)}")
        except Exception as e:
            st.error(f"PDF classification failed: {e}")

# Output section
if st.session_state.result:
    result = st.session_state.result
    
    # Show DIFF card if this is a rerun (prev_result exists)
    # This implements "Step 5: 差分保存" from README.md Agentic definition
    if st.session_state.prev_result and st.session_state.prev_result != result:
        prev = st.session_state.prev_result
        st.markdown("## 🔄 Classification Updated (After Rerun)")
        st.success("The classification has been updated based on your answers. This demonstrates Step 5: 差分保存 (Diff Display).")
        
        st.markdown("### Comparison: Before → After")
        diff_col1, diff_col2, diff_col3, diff_col4 = st.columns(4)
        with diff_col1:
            prev_decision = prev.get("decision", "UNKNOWN")
            new_decision = result.get("decision", "UNKNOWN")
            st.write("**Decision**")
            st.write(f"`{prev_decision}` → `{new_decision}`")
            if prev_decision != new_decision:
                st.success("✓ Changed")
            else:
                st.info("No change")
        with diff_col2:
            prev_conf = prev.get("confidence", 0.0)
            new_conf = result.get("confidence", 0.0)
            st.write("**Confidence**")
            st.write(f"{prev_conf:.2f} → {new_conf:.2f}")
            if abs(prev_conf - new_conf) > 0.01:
                st.info("✓ Updated")
        with diff_col3:
            prev_trace = prev.get("trace", [])
            new_trace = result.get("trace", [])
            st.write("**Trace Steps**")
            st.write(f"{len(prev_trace)} → {len(new_trace)}")
            prev_trace_str = " → ".join(prev_trace)
            new_trace_str = " → ".join(new_trace)
            if prev_trace_str != new_trace_str:
                st.caption(f"Before: {prev_trace_str}")
                st.caption(f"After: {new_trace_str}")
                st.info("✓ Extended")
        with diff_col4:
            prev_citations = len(prev.get("citations", []))
            new_citations = len(result.get("citations", []))
            st.write("**Citations**")
            st.write(f"{prev_citations} → {new_citations}")
            if new_citations > prev_citations:
                st.info("✓ Added")
        
        st.markdown("---")
    
    st.markdown("## Results")
    
    # Decision badge with WIN+1 fields - prominent at top
    decision = result.get("decision", "UNKNOWN")
    decision_label = {
        "CAPITAL_LIKE": "CAPITAL_LIKE",
        "EXPENSE_LIKE": "EXPENSE_LIKE",
        "GUIDANCE": "GUIDANCE",
    }.get(decision, "UNKNOWN")
    
    # Large decision display
    st.markdown(f"### Decision: **{decision_label}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        confidence = result.get("confidence", 0.0)
        st.metric("Confidence", f"{confidence:.2f}")
    with col2:
        is_valid = result.get("is_valid_document", False)
        st.metric("Valid Document", "Yes" if is_valid else "No")
    with col3:
        trace = result.get("trace", [])
        if trace:
            st.metric("Steps", len(trace))
    
    # Trace
    if trace:
        st.caption(f"Trace: {' -> '.join(trace)}")
    
    # Evidence panel - evidence-first, prominent (moved before Reasons)
    evidence = result.get("evidence", [])
    if evidence:
        st.markdown("### Evidence")
        for i, ev in enumerate(evidence):
            with st.expander(f"Line {ev.get('line_no', '?')}: {ev.get('description', '')} (Confidence: {ev.get('confidence', 0.8):.2f})", expanded=(i == 0)):
                st.write(f"**Confidence:** {ev.get('confidence', 0.8):.2f}")
                if ev.get("source_text"):
                    st.write("**Source Text:**")
                    st.code(ev["source_text"], language="text")
                if ev.get("position_hint"):
                    st.caption(f"Position: {ev['position_hint']}")
    
    # Citations (Google Cloud: Vertex AI Search results)
    citations = result.get("citations", [])
    st.markdown("### Legal Citations (Google Cloud Search)")
    if citations:
        st.info("Relevant regulations and guidelines found via Vertex AI Search (VERTEX_SEARCH_ENABLED=1)")
        for i, citation in enumerate(citations):
            with st.expander(f"Citation {i+1}: {citation.get('title', 'Untitled')}", expanded=(i == 0)):
                if citation.get("snippet"):
                    st.write("**Excerpt:**")
                    st.code(citation["snippet"], language="text")
                if citation.get("uri"):
                    st.markdown(f"**Source:** [{citation['uri']}]({citation['uri']})")
                if citation.get("relevance_score"):
                    st.caption(f"Relevance: {citation['relevance_score']:.2f}")
    else:
        # Show OFF state when feature is disabled (consistent with DEMO.md)
        st.caption("Legal Citations: OFF (set VERTEX_SEARCH_ENABLED=1 to enable)")
    
    # Reasons
    reasons = result.get("reasons", [])
    if reasons:
        st.markdown("#### Reasons")
        for reason in reasons:
            st.write(f"- {reason}")
    
    # GUIDANCE: Questions and answers (agentic loop)
    if decision == "GUIDANCE":
        # Prominent "Agent needs info" panel at top
        st.markdown("---")
        st.markdown("### 🤖 Agent Needs Information")
        st.info("The classification system needs additional context to make a decision. Please provide the information below.")
        
        missing_fields = result.get("missing_fields", [])
        why_missing = result.get("why_missing_matters", [])
        
        # Missing fields as checklist
        if missing_fields:
            st.markdown("#### Missing Information (Checklist)")
            for i, mf in enumerate(missing_fields):
                checked = st.checkbox(
                    f"✓ {mf}",
                    value=mf in st.session_state.answers,
                    key=f"check_{i}",
                )
                if checked and mf not in st.session_state.answers:
                    st.session_state.answers[mf] = ""
        
        # Why missing matters (prominent)
        if why_missing:
            st.markdown("#### Why This Matters")
            for why in why_missing[:3]:  # Limit to top 3
                st.write(f"• {why}")
        
        # What you should answer
        st.markdown("#### What You Should Answer")
        st.caption("Provide context about: repair vs upgrade, quantity/units, asset location, or useful life")
        
        # Quick-pick buttons for common answers
        st.markdown("**Quick Picks:**")
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        with quick_col1:
            if st.button("Repair/Maintenance", key="quick_repair"):
                st.session_state.answers["purpose"] = "repair"
                st.rerun()
        with quick_col2:
            if st.button("Upgrade/New Asset", key="quick_upgrade"):
                st.session_state.answers["purpose"] = "upgrade"
                st.rerun()
        with quick_col3:
            if st.button("Clear All Answers", key="quick_clear"):
                st.session_state.answers = {}
                st.rerun()
        
        # Questions from API response + missing_fields as form inputs
        questions = result.get("questions", [])
        with st.form("guidance_answers", clear_on_submit=False):
            st.markdown("#### Provide Answers")
            
            # Build form inputs from missing_fields
            form_answers = {}
            for i, mf in enumerate(missing_fields):
                answer = st.text_input(
                    f"**{mf}**",
                    value=st.session_state.answers.get(mf, ""),
                    key=f"form_{i}",
                    help=why_missing[i] if i < len(why_missing) else "Provide additional context",
                )
                if answer:
                    form_answers[mf] = answer
            
            # Also show questions from API if available
            if questions:
                for i, question in enumerate(questions):
                    q_key = f"q_{i}"
                    answer = st.text_input(
                        f"Q{i+1}: {question}",
                        value=st.session_state.answers.get(q_key, ""),
                        key=f"question_{i}",
                    )
                    if answer:
                        form_answers[q_key] = answer
            
            submitted = st.form_submit_button("Re-run Classification with Answers", type="primary")
            
            if submitted:
                # Update session state with form answers
                st.session_state.answers.update(form_answers)
                
                if st.session_state.initial_opal is None:
                    st.error("Initial Opal JSON not found. Please classify again.")
                else:
                    try:
                        # Call Cloud Run API with answers
                        classify_url = f"{service_url}/classify"
                        payload = {
                            "opal_json": st.session_state.initial_opal,
                            "answers": st.session_state.answers,
                        }
                        
                        with st.spinner("Re-classifying with answers..."):
                            response = requests.post(
                                classify_url,
                                json=payload,
                                timeout=15,
                            )
                            response.raise_for_status()
                            result_data = response.json()
                        
                        # Store previous result for comparison
                        st.session_state.prev_result = st.session_state.result.copy()
                        st.session_state.result = result_data
                        
                        st.rerun()
                        
                    except requests.exceptions.Timeout:
                        st.error("Request timeout (15s). Service may be slow.")
                    except requests.exceptions.RequestException as e:
                        error_detail = ""
                        if hasattr(e, "response") and e.response is not None:
                            # Handle 422 validation errors specifically
                            if e.response.status_code == 422:
                                try:
                                    error_body = e.response.json()
                                    error_detail = f"Validation error (422): {json.dumps(error_body, indent=2, ensure_ascii=False)}"
                                except:
                                    error_detail = f"Validation error (422): {e.response.text}"
                            else:
                                try:
                                    error_detail = e.response.text
                                except:
                                    error_detail = str(e)
                        else:
                            error_detail = str(e)
                        st.error(f"API request failed: {error_detail}")
                    except Exception as e:
                        st.error(f"Re-classification failed: {e}")
    
    # Full result JSON (collapsible)
    with st.expander("Full Result JSON", expanded=False):
        st.json(result)
