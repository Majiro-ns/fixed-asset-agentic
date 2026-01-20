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

# Initialize session state
if "result" not in st.session_state:
    st.session_state.result = None
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "initial_opal" not in st.session_state:
    st.session_state.initial_opal = None

# Input section
st.markdown("## Input")

# Load demo case if selected
opal_json_text = ""
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

# Classify button
if st.button("Classify", type="primary", use_container_width=True):
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
            
            # Store result
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
                try:
                    error_detail = e.response.text
                except:
                    error_detail = str(e)
            else:
                error_detail = str(e)
            st.error(f"API request failed: {error_detail}")
        except Exception as e:
            st.error(f"Classification failed: {e}")

# Output section
if st.session_state.result:
    result = st.session_state.result
    
    st.markdown("## Results")
    
    # Decision badge with WIN+1 fields
    decision = result.get("decision", "UNKNOWN")
    decision_label = {
        "CAPITAL_LIKE": "[CAPITAL_LIKE]",
        "EXPENSE_LIKE": "[EXPENSE_LIKE]",
        "GUIDANCE": "[GUIDANCE]",
    }.get(decision, "[UNKNOWN]")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"### Decision: **{decision_label}**")
    with col2:
        confidence = result.get("confidence", 0.0)
        st.metric("Confidence", f"{confidence:.2f}")
    with col3:
        is_valid = result.get("is_valid_document", False)
        st.metric("Valid Document", "Yes" if is_valid else "No")
    
    # Trace
    trace = result.get("trace", [])
    if trace:
        st.caption(f"Trace: {' -> '.join(trace)}")
    
    # Reasons
    reasons = result.get("reasons", [])
    if reasons:
        st.markdown("#### Reasons")
        for reason in reasons:
            st.write(f"- {reason}")
    
    # Evidence table
    evidence = result.get("evidence", [])
    if evidence:
        st.markdown("#### Evidence")
        evidence_data = []
        for ev in evidence:
            evidence_data.append({
                "Line": ev.get("line_no", "?"),
                "Description": ev.get("description", ""),
                "Confidence": f"{ev.get('confidence', 0.8):.2f}",
                "Source Text": ev.get("source_text", "")[:100] + "..." if len(ev.get("source_text", "")) > 100 else ev.get("source_text", ""),
            })
        st.dataframe(evidence_data, use_container_width=True)
    
    # GUIDANCE: Questions and answers (agentic loop)
    if decision == "GUIDANCE":
        st.markdown("#### Guidance Required")
        st.warning("This document requires manual review. Please answer the questions below.")
        
        # Show missing fields and why they matter
        missing_fields = result.get("missing_fields", [])
        why_missing = result.get("why_missing_matters", [])
        if missing_fields:
            with st.expander("Missing Fields", expanded=False):
                for i, (mf, why) in enumerate(zip(missing_fields, why_missing if len(why_missing) > i else [""] * len(missing_fields))):
                    st.write(f"**{mf}**: {why}")
        
        # Questions from API response
        questions = result.get("questions", [])
        if questions:
            for i, question in enumerate(questions):
                field_key = f"field_{i}"
                answer = st.text_input(
                    f"Q{i+1}: {question}",
                    value=st.session_state.answers.get(field_key, ""),
                    key=f"answer_{i}",
                )
                st.session_state.answers[field_key] = answer
        
        if st.button("Re-run Classification with Answers", type="primary"):
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
                    
                    # Update result
                    st.session_state.result = result_data
                    
                    st.success("Re-classified with answers!")
                    st.rerun()
                    
                except requests.exceptions.Timeout:
                    st.error("Request timeout (15s). Service may be slow.")
                except requests.exceptions.RequestException as e:
                    error_detail = ""
                    if hasattr(e, "response") and e.response is not None:
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
