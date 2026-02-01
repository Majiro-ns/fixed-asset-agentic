# -*- coding: utf-8 -*-
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

from core.adapter import adapt_opal_to_v1
from core.classifier import classify_document
from core.pdf_extract import extract_pdf, extraction_to_opal
from core.policy import load_policy

# 耐用年数判定（フラグ制御）
try:
    from api.useful_life_estimator import estimate_useful_life
    USEFUL_LIFE_AVAILABLE = True
except ImportError:
    USEFUL_LIFE_AVAILABLE = False
    def estimate_useful_life(*args, **kwargs):
        return {"useful_life_years": 0, "source": "not_available"}

# Optional: Vertex AI Search integration (feature-flagged)
try:
    from api.vertex_search import get_citations_for_guidance
    VERTEX_SEARCH_AVAILABLE = True
except ImportError:
    VERTEX_SEARCH_AVAILABLE = False
    def get_citations_for_guidance(*args, **kwargs):
        return []

# Optional: Gemini classification integration (feature-flagged)
# Enabled with GEMINI_ENABLED=1
GEMINI_ENABLED = os.environ.get("GEMINI_ENABLED", "0") == "1"
try:
    from api.gemini_classifier import classify_with_gemini, classify_line_items
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    def classify_with_gemini(*args, **kwargs):
        return {"decision": "GUIDANCE", "confidence": 0.0, "reasoning": "Gemini未インストール", "flags": ["not_installed"]}
    def classify_line_items(*args, **kwargs):
        return []


def _bool_env(name: str, default: bool = False) -> bool:
    """Check environment variable for boolean flag."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


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
    # Google Cloud: Legal citations (Vertex AI Search)
    citations: List[Dict[str, Any]] = []
    # 耐用年数判定（CAPITAL_LIKEの場合のみ）
    useful_life: Optional[Dict[str, Any]] = None
    # 明細一覧（UIで金額・内容を表示用）
    line_items: List[Dict[str, Any]] = []


def _format_classify_response(
    doc: Dict[str, Any],
    trace_steps: Optional[List[str]] = None,
    citations: Optional[List[Dict[str, Any]]] = None,
    useful_life: Optional[Dict[str, Any]] = None,
) -> ClassifyResponse:
    """
    Convert pipeline output to API response format.
    Maps existing classifier/pipeline outputs to decision/reasons/evidence/questions/metadata.
    """
    line_items = doc.get("line_items", [])

    # decision: aggregate classifications
    # ルール: 明確な判定（CAPITAL_LIKE/EXPENSE_LIKE）が過半数あればそちらを採用
    #        GUIDANCEのみ or 明確判定が拮抗している場合はGUIDANCE
    classifications = []
    guidance_items = []
    for item in line_items:
        if isinstance(item, dict):
            cls = item.get("classification")
            if cls:
                classifications.append(cls)
                if cls == "GUIDANCE":
                    guidance_items.append(item)

    if not classifications:
        decision = "UNKNOWN"
    else:
        # カウント集計
        capital_count = sum(1 for c in classifications if c == "CAPITAL_LIKE")
        expense_count = sum(1 for c in classifications if c == "EXPENSE_LIKE")
        guidance_count = sum(1 for c in classifications if c == "GUIDANCE")
        total = len(classifications)

        # 明確判定（資産 or 費用）が過半数かつ競合していない場合はそちらを採用
        if capital_count > 0 and expense_count > 0:
            # 両方ある場合 = 競合 → GUIDANCE
            decision = "GUIDANCE"
        elif capital_count >= total / 2:
            # 資産寄りが半数以上
            decision = "CAPITAL_LIKE"
        elif expense_count >= total / 2:
            # 費用寄りが半数以上
            decision = "EXPENSE_LIKE"
        elif capital_count > expense_count:
            # 資産寄りの方が多い
            decision = "CAPITAL_LIKE"
        elif expense_count > capital_count:
            # 費用寄りの方が多い
            decision = "EXPENSE_LIKE"
        else:
            # それ以外はGUIDANCE
            decision = "GUIDANCE"
    
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
                # confidenceはclassifierで計算されたitemのconfidenceを優先
                item_confidence = item.get("confidence", 0.8)
                evidence_item = {
                    "line_no": item.get("line_no"),
                    "description": item.get("description"),
                    "source_text": ev.get("source_text", ""),
                    "position_hint": ev.get("position_hint", ""),
                    "confidence": item_confidence,
                }
                # Include snippets if available
                snippets = ev.get("snippets")
                if snippets:
                    evidence_item["snippets"] = snippets
                # Surface tax_rule flags in evidence (rule IDs for 10/20/30/60万)
                tax_rules = [f for f in item.get("flags", []) if isinstance(f, str) and f.startswith("tax_rule:")]
                if tax_rules:
                    evidence_item["tax_rules"] = tax_rules
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

    # Calculate confidence: 決定に貢献した明細の確信度を使う
    # - CAPITAL_LIKE/EXPENSE_LIKE: その分類の明細の最大確信度
    # - GUIDANCE: GUIDANCE明細の平均確信度
    if decision in ("CAPITAL_LIKE", "EXPENSE_LIKE"):
        matching_confidences = [
            item.get("confidence", 0.8)
            for item in line_items
            if isinstance(item, dict) and item.get("classification") == decision
        ]
        confidence = max(matching_confidences) if matching_confidences else 0.7
    else:
        # GUIDANCE: 平均を使う
        confidences = [e.get("confidence", 0.8) for e in evidence]
        confidence = sum(confidences) / len(confidences) if confidences else 0.5
    
    # missing_fields and why_missing_matters: only for GUIDANCE
    missing_fields: List[str] = []
    why_missing_matters: List[str] = []
    # 技術的なフラグはユーザーに見せない
    _internal_flags = {"api_error", "parse_error", "no_keywords", "conflicting_keywords"}
    if decision == "GUIDANCE":
        # Extract missing field hints from flags and questions
        for item in guidance_items:
            flags = item.get("flags", [])
            desc = item.get("description", "")
            # Heuristic: flags often indicate missing info (技術的フラグは除外)
            user_flags = [f for f in flags if isinstance(f, str) and f not in _internal_flags and not f.startswith("policy:") and not f.startswith("tax_rule:")]
            if user_flags:
                missing_fields.extend([f"{desc}:{f}" for f in user_flags])
                why_missing_matters.append(f"'{desc}' の追加情報があれば判定できる可能性があります")
        # Deduplicate
        missing_fields = list(set(missing_fields))
        why_missing_matters = list(set(why_missing_matters))
        # 何も情報がない場合はデフォルトメッセージ
        if not missing_fields:
            missing_fields = ["この支出の目的（修繕 or 新規購入）"]
            why_missing_matters = ["支出目的により固定資産か経費かの判断が変わります"]

    # trace: execution steps
    if trace_steps is None:
        trace_steps = ["extract", "parse", "rules", "format"]
    
    # citations: legal/regulation references (from Vertex AI Search if enabled)
    if citations is None:
        citations = []
    
    # line_items for UI display (description, amount)
    formatted_line_items: List[Dict[str, Any]] = []
    for item in line_items:
        if isinstance(item, dict):
            formatted_item = {
                "description": item.get("description", ""),
                "amount": item.get("amount"),
                "classification": item.get("classification"),
            }
            formatted_line_items.append(formatted_item)

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
        citations=citations,
        useful_life=useful_life,
        line_items=formatted_line_items,
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

    Gemini Integration (GEMINI_ENABLED=1):
    - First attempts classification with Gemini API
    - Falls back to rule-based classifier on failure
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

        # Classify: Gemini or rule-based
        classified = None
        gemini_used = False

        if GEMINI_ENABLED and GEMINI_AVAILABLE:
            try:
                # Try Gemini classification for each line item
                trace_steps.append("gemini")
                line_items = normalized.get("line_items", [])
                doc_info = normalized.get("document_info", {})
                context = {
                    "vendor": doc_info.get("vendor"),
                    "date": doc_info.get("date"),
                }

                # Classify each line item with Gemini
                for item in line_items:
                    description = item.get("description", "")
                    amount = item.get("amount", 0) or 0

                    gemini_result = classify_with_gemini(description, amount, context)

                    # Apply Gemini result to item
                    item["classification"] = gemini_result.get("decision", "GUIDANCE")
                    item["label_ja"] = {
                        "CAPITAL_LIKE": "資産寄り",
                        "EXPENSE_LIKE": "費用寄り",
                        "GUIDANCE": "要確認（判定しません）"
                    }.get(item["classification"], "要確認")
                    item["rationale_ja"] = gemini_result.get("reasoning", "")
                    item["flags"] = gemini_result.get("flags", [])
                    item["gemini_confidence"] = gemini_result.get("confidence", 0.0)

                classified = normalized
                gemini_used = True
                trace_steps.append("gemini_success")

            except Exception:
                # Gemini failed - fall back to rule-based
                trace_steps.append("gemini_fallback")
                classified = None

        # Rule-based classification (default or fallback)
        if classified is None:
            classified = classify_document(normalized, policy)
            trace_steps.append("rules")
        
        # Format initial response
        initial_response = _format_classify_response(classified, trace_steps=trace_steps.copy())
        
        # Google Cloud: Vertex AI Search for legal citations (if GUIDANCE and feature enabled)
        citations: List[Dict[str, Any]] = []
        if initial_response.decision == "GUIDANCE" and VERTEX_SEARCH_AVAILABLE:
            # Collect context from guidance items
            guidance_items = [item for item in classified.get("line_items", []) 
                            if isinstance(item, dict) and item.get("classification") == "GUIDANCE"]
            if guidance_items:
                # Use first guidance item for search context
                item = guidance_items[0]
                citations = get_citations_for_guidance(
                    description=item.get("description", ""),
                    missing_fields=initial_response.missing_fields,
                    flags=item.get("flags", []),
                )
                if citations:
                    trace_steps.append("law_search")
                    # Update response with citations
                    initial_response = _format_classify_response(
                        classified,
                        trace_steps=trace_steps.copy(),
                        citations=citations,
                    )
        
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
                # Preserve citations in rerun response
                return _format_classify_response(enhanced_classified, trace_steps=trace_steps, citations=citations)
        
        trace_steps.append("format")
        return initial_response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception:
        raise HTTPException(status_code=500, detail="Classification failed. Please check input format.")


@app.post("/classify_pdf", response_model=ClassifyResponse)
async def classify_pdf(
    file: UploadFile = File(...),
    policy_path: Optional[str] = None,
    use_gemini_vision: Optional[str] = None,
    estimate_useful_life_flag: Optional[str] = None,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
) -> ClassifyResponse:
    """
    Classify fixed asset items from uploaded PDF file.

    Feature-flagged: Only active when PDF_CLASSIFY_ENABLED=1.
    When disabled, returns 400 with clear message (no crash).

    Query Parameters:
        use_gemini_vision: "1" to force Gemini Vision extraction (requires GEMINI_PDF_ENABLED=1)
        estimate_useful_life_flag: "1" to estimate useful life for CAPITAL_LIKE items
        start_page: 開始ページ番号（1始まり、オプショナル）
        end_page: 終了ページ番号（1始まり、オプショナル）
    """
    # Feature flag check
    if not _bool_env("PDF_CLASSIFY_ENABLED", False):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PDF_CLASSIFY_DISABLED",
                "message": "PDF classification is disabled on this server",
                "how_to_enable": "Set PDF_CLASSIFY_ENABLED=1 on server",
                "fallback": "Use POST /classify with Opal JSON instead",
            },
        )
    
    try:
        trace_steps = ["pdf_upload"]

        # Save uploaded PDF to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_path = Path(tmp_file.name)
            content = await file.read()
            tmp_path.write_bytes(content)

        # ページ範囲が指定された場合、該当ページのみを抽出
        extracted_pdf_path: Optional[Path] = None
        if start_page is not None or end_page is not None:
            try:
                import fitz  # PyMuPDF

                doc = fitz.open(tmp_path)
                total_pages = len(doc)

                # デフォルト値の設定（1始まり → 0始まりに変換）
                actual_start = (start_page - 1) if start_page is not None else 0
                actual_end = (end_page - 1) if end_page is not None else (total_pages - 1)

                # バリデーション
                if actual_start < 0:
                    doc.close()
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "INVALID_PAGE_RANGE",
                            "message": "start_page must be >= 1",
                        },
                    )
                if actual_end >= total_pages:
                    doc.close()
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "INVALID_PAGE_RANGE",
                            "message": f"end_page ({end_page}) exceeds total pages ({total_pages})",
                        },
                    )
                if actual_start > actual_end:
                    doc.close()
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "INVALID_PAGE_RANGE",
                            "message": "start_page must be <= end_page",
                        },
                    )

                # 指定ページのみを含む新しいPDFを作成
                new_doc = fitz.open()
                for page_num in range(actual_start, actual_end + 1):
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

                # 一時ファイルに保存
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as extracted_tmp:
                    extracted_pdf_path = Path(extracted_tmp.name)
                    new_doc.save(str(extracted_pdf_path))

                new_doc.close()
                doc.close()

                trace_steps.append(f"page_extract:{start_page or 1}-{end_page or total_pages}")

            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "PYMUPDF_NOT_INSTALLED",
                        "message": "PyMuPDF (fitz) is required for page range extraction",
                    },
                )

        # 処理対象のPDFパスを決定
        pdf_to_process = extracted_pdf_path if extracted_pdf_path else tmp_path

        try:
            # Extract PDF using core functions (core/* not modified, only imported)
            # Pass use_gemini_vision flag if requested via query param
            force_gemini = use_gemini_vision == "1"
            extraction = extract_pdf(pdf_to_process, use_gemini_vision=force_gemini)
            trace_steps.append("extract_gemini" if force_gemini else "extract")
            
            # Convert extraction to Opal-like format
            opal_like = extraction_to_opal(extraction)
            trace_steps.append("extraction_to_opal")
            
            # Normalize using adapter
            normalized = adapt_opal_to_v1(opal_like)
            trace_steps.append("parse")
            
            # Load policy
            if not policy_path:
                default_policy = PROJECT_ROOT / "policies" / "company_default.json"
                if default_policy.exists():
                    policy_path = str(default_policy)
            
            policy = load_policy(policy_path)
            
            # Classify
            classified = classify_document(normalized, policy)
            trace_steps.append("rules")
            
            # Add warnings from extraction
            warnings = extraction.get("meta", {}).get("warnings", [])
            if warnings:
                if "warnings" not in classified:
                    classified["warnings"] = []
                classified["warnings"].extend(warnings)
            
            # Format response (same as /classify)
            initial_response = _format_classify_response(classified, trace_steps=trace_steps.copy())
            
            # Vertex AI Search citations (if enabled, same as /classify)
            citations: List[Dict[str, Any]] = []
            if initial_response.decision == "GUIDANCE" and VERTEX_SEARCH_AVAILABLE:
                guidance_items = [item for item in classified.get("line_items", []) 
                                if isinstance(item, dict) and item.get("classification") == "GUIDANCE"]
                if guidance_items:
                    item = guidance_items[0]
                    citations = get_citations_for_guidance(
                        description=item.get("description", ""),
                        missing_fields=initial_response.missing_fields,
                        flags=item.get("flags", []),
                    )
                    if citations:
                        trace_steps.append("law_search")
                        initial_response = _format_classify_response(
                            classified,
                            trace_steps=trace_steps.copy(),
                            citations=citations,
                        )
            
            # 耐用年数判定（CAPITAL_LIKEの場合のみ、フラグ有効時）
            useful_life_result: Optional[Dict[str, Any]] = None
            should_estimate = (
                estimate_useful_life_flag == "1" or
                _bool_env("USEFUL_LIFE_ENABLED", False)
            )
            if should_estimate and USEFUL_LIFE_AVAILABLE:
                # 判定結果を先に取得
                temp_response = _format_classify_response(classified, trace_steps=trace_steps.copy())
                if temp_response.decision == "CAPITAL_LIKE":
                    # 最初のCAPITAL_LIKE明細のdescriptionで耐用年数を判定
                    capital_items = [
                        item for item in classified.get("line_items", [])
                        if isinstance(item, dict) and item.get("classification") == "CAPITAL_LIKE"
                    ]
                    if capital_items:
                        desc = capital_items[0].get("description", "")
                        useful_life_result = estimate_useful_life(desc)
                        if useful_life_result and useful_life_result.get("useful_life_years", 0) > 0:
                            trace_steps.append("useful_life")

            trace_steps.append("format")
            return _format_classify_response(
                classified,
                trace_steps=trace_steps,
                citations=citations,
                useful_life=useful_life_result,
            )
        
        finally:
            # Clean up temporary files
            if tmp_path.exists():
                tmp_path.unlink()
            if extracted_pdf_path and extracted_pdf_path.exists():
                extracted_pdf_path.unlink()

    except HTTPException:
        # Re-raise HTTPException (validation errors) without wrapping
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PDF_CLASSIFY_ERROR",
                "message": f"Invalid PDF: {str(e)}",
                "how_to_enable": None,
            },
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PDF_CLASSIFY_ERROR",
                "message": "PDF classification failed. Please check file format.",
                "how_to_enable": None,
            },
        )


class BatchResultItem(BaseModel):
    """一括処理の個別結果"""
    filename: str
    success: bool
    decision: Optional[str] = None
    confidence: Optional[float] = None
    reasons: List[str] = []
    error: Optional[str] = None


class BatchResponse(BaseModel):
    """一括処理のレスポンス"""
    results: List[BatchResultItem]
    total: int
    success: int
    failed: int


@app.post("/classify_batch", response_model=BatchResponse)
async def classify_batch(
    files: List[UploadFile] = File(...),
    policy_path: Optional[str] = None,
    use_gemini_vision: Optional[str] = None,
    estimate_useful_life_flag: Optional[str] = None,
) -> BatchResponse:
    """
    Classify multiple PDF files in batch.

    複数のPDFファイルを一括でアップロードし、順次処理する。
    エラーが発生したファイルはスキップして続行する。

    Feature-flagged: Only active when PDF_CLASSIFY_ENABLED=1.

    Query Parameters:
        policy_path: Path to policy file (optional)
        use_gemini_vision: "1" to force Gemini Vision extraction
        estimate_useful_life_flag: "1" to estimate useful life for CAPITAL_LIKE items

    Returns:
        BatchResponse with results for each file and summary counts
    """
    import asyncio

    # Feature flag check (same as classify_pdf)
    if not _bool_env("PDF_CLASSIFY_ENABLED", False):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PDF_CLASSIFY_DISABLED",
                "message": "PDF classification is disabled on this server",
                "how_to_enable": "Set PDF_CLASSIFY_ENABLED=1 on server",
                "fallback": "Use POST /classify with Opal JSON instead",
            },
        )

    results: List[BatchResultItem] = []
    success_count = 0
    failed_count = 0

    for upload_file in files:
        filename = upload_file.filename or "unknown.pdf"

        try:
            # タイムアウト30秒で処理
            result = await asyncio.wait_for(
                _process_single_pdf(
                    upload_file,
                    policy_path,
                    use_gemini_vision,
                    estimate_useful_life_flag,
                ),
                timeout=30.0,
            )

            results.append(BatchResultItem(
                filename=filename,
                success=True,
                decision=result.decision,
                confidence=result.confidence,
                reasons=result.reasons[:3],  # 最初の3つの理由のみ
            ))
            success_count += 1

        except asyncio.TimeoutError:
            results.append(BatchResultItem(
                filename=filename,
                success=False,
                error="処理がタイムアウトしました（30秒）",
            ))
            failed_count += 1

        except HTTPException as e:
            # HTTPExceptionの詳細メッセージを抽出
            error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
            results.append(BatchResultItem(
                filename=filename,
                success=False,
                error=error_msg,
            ))
            failed_count += 1

        except Exception as e:
            results.append(BatchResultItem(
                filename=filename,
                success=False,
                error=f"処理中にエラーが発生: {str(e)}",
            ))
            failed_count += 1

    return BatchResponse(
        results=results,
        total=len(files),
        success=success_count,
        failed=failed_count,
    )


async def _process_single_pdf(
    file: UploadFile,
    policy_path: Optional[str],
    use_gemini_vision: Optional[str],
    estimate_useful_life_flag: Optional[str],
) -> ClassifyResponse:
    """
    単一PDFファイルを処理する内部関数。
    classify_pdf と同じロジックを使用。
    """
    trace_steps = ["pdf_upload"]

    # Save uploaded PDF to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_path = Path(tmp_file.name)
        content = await file.read()
        tmp_path.write_bytes(content)

    try:
        # Extract PDF using core functions
        force_gemini = use_gemini_vision == "1"
        extraction = extract_pdf(tmp_path, use_gemini_vision=force_gemini)
        trace_steps.append("extract_gemini" if force_gemini else "extract")

        # Convert extraction to Opal-like format
        opal_like = extraction_to_opal(extraction)
        trace_steps.append("extraction_to_opal")

        # Normalize using adapter
        normalized = adapt_opal_to_v1(opal_like)
        trace_steps.append("parse")

        # Load policy
        actual_policy_path = policy_path
        if not actual_policy_path:
            default_policy = PROJECT_ROOT / "policies" / "company_default.json"
            if default_policy.exists():
                actual_policy_path = str(default_policy)

        policy = load_policy(actual_policy_path)

        # Classify
        classified = classify_document(normalized, policy)
        trace_steps.append("rules")

        # Add warnings from extraction
        warnings = extraction.get("meta", {}).get("warnings", [])
        if warnings:
            if "warnings" not in classified:
                classified["warnings"] = []
            classified["warnings"].extend(warnings)

        # Format response
        initial_response = _format_classify_response(classified, trace_steps=trace_steps.copy())

        # Vertex AI Search citations (if enabled)
        citations: List[Dict[str, Any]] = []
        if initial_response.decision == "GUIDANCE" and VERTEX_SEARCH_AVAILABLE:
            guidance_items = [item for item in classified.get("line_items", [])
                            if isinstance(item, dict) and item.get("classification") == "GUIDANCE"]
            if guidance_items:
                item = guidance_items[0]
                citations = get_citations_for_guidance(
                    description=item.get("description", ""),
                    missing_fields=initial_response.missing_fields,
                    flags=item.get("flags", []),
                )
                if citations:
                    trace_steps.append("law_search")
                    initial_response = _format_classify_response(
                        classified,
                        trace_steps=trace_steps.copy(),
                        citations=citations,
                    )

        # 耐用年数判定（CAPITAL_LIKEの場合のみ）
        useful_life_result: Optional[Dict[str, Any]] = None
        should_estimate = (
            estimate_useful_life_flag == "1" or
            _bool_env("USEFUL_LIFE_ENABLED", False)
        )
        if should_estimate and USEFUL_LIFE_AVAILABLE:
            temp_response = _format_classify_response(classified, trace_steps=trace_steps.copy())
            if temp_response.decision == "CAPITAL_LIKE":
                capital_items = [
                    item for item in classified.get("line_items", [])
                    if isinstance(item, dict) and item.get("classification") == "CAPITAL_LIKE"
                ]
                if capital_items:
                    desc = capital_items[0].get("description", "")
                    useful_life_result = estimate_useful_life(desc)
                    if useful_life_result and useful_life_result.get("useful_life_years", 0) > 0:
                        trace_steps.append("useful_life")

        trace_steps.append("format")
        return _format_classify_response(
            classified,
            trace_steps=trace_steps,
            citations=citations,
            useful_life=useful_life_result,
        )

    finally:
        # Clean up temporary file
        if tmp_path.exists():
            tmp_path.unlink()
