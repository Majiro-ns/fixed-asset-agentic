#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate classifier against golden test set."""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import _format_classify_response
from core.adapter import adapt_opal_to_v1
from core.classifier import classify_document
from core.policy import load_policy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = PROJECT_ROOT / "data" / "golden"


def load_golden_case(case_num: int) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Load request and expected files for a case."""
    request_path = GOLDEN_DIR / f"case{case_num:02d}_request.json"
    expected_path = GOLDEN_DIR / f"case{case_num:02d}_expected.json"
    
    if not request_path.exists() or not expected_path.exists():
        return None, None
    
    with open(request_path, "r", encoding="utf-8") as f:
        request = json.load(f)
    
    with open(expected_path, "r", encoding="utf-8") as f:
        expected = json.load(f)
    
    return request, expected


def check_reasons_contains(actual_reasons: List[str], expected_keywords: List[str]) -> bool:
    """Check if any reason contains expected keywords."""
    if not expected_keywords:
        return True
    
    actual_text = " ".join(actual_reasons).lower()
    return any(kw.lower() in actual_text for kw in expected_keywords)


def evaluate_case(case_num: int) -> tuple[bool, str]:
    """Evaluate a single golden case. Returns (passed, message)."""
    request, expected = load_golden_case(case_num)
    
    if request is None or expected is None:
        return False, f"Case {case_num:02d}: Files not found"
    
    try:
        # Load policy
        policy_path = request.get("policy_path")
        if not policy_path:
            default_policy = PROJECT_ROOT / "policies" / "company_default.json"
            if default_policy.exists():
                policy_path = str(default_policy)
        policy = load_policy(policy_path)
        
        # Process through pipeline
        opal_json = request["opal_json"]
        normalized = adapt_opal_to_v1(opal_json)
        classified = classify_document(normalized, policy)
        response = _format_classify_response(classified)
        
        # Check decision
        if response.decision != expected["decision"]:
            return False, (
                f"Case {case_num:02d}: Decision mismatch - "
                f"expected {expected['decision']}, got {response.decision}"
            )
        
        # Check is_valid_document
        if response.is_valid_document != expected["is_valid_document"]:
            return False, (
                f"Case {case_num:02d}: is_valid_document mismatch - "
                f"expected {expected['is_valid_document']}, got {response.is_valid_document}"
            )
        
        # Check reasons keywords if specified
        if "reasons_contains" in expected:
            if not check_reasons_contains(response.reasons, expected["reasons_contains"]):
                return False, (
                    f"Case {case_num:02d}: Reasons don't contain expected keywords - "
                    f"expected any of {expected['reasons_contains']}, got {response.reasons}"
                )
        
        return True, f"Case {case_num:02d}: PASS"
        
    except Exception as e:
        return False, f"Case {case_num:02d}: Error - {str(e)}"


def main() -> None:
    """Run evaluation on all golden cases."""
    print("=" * 60)
    print("Golden Set Evaluation")
    print("=" * 60)
    print()
    
    results: List[tuple[int, bool, str]] = []
    
    # Evaluate cases 1-10
    for case_num in range(1, 11):
        passed, message = evaluate_case(case_num)
        results.append((case_num, passed, message))
        
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {message}")
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    accuracy = (passed_count / total_count * 100) if total_count > 0 else 0.0
    
    print(f"Total cases: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Accuracy: {accuracy:.1f}%")
    print()
    
    if passed_count == total_count:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
