# -*- coding: utf-8 -*-
import json
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Structured Logging Setup ---
class _JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        return json.dumps(log_entry, ensure_ascii=False)

_handler = logging.StreamHandler()
_handler.setFormatter(_JSONFormatter())
logger = logging.getLogger("fixed_asset_api")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)

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


# --- C-01: API Key Authentication ---
_API_KEY = os.environ.get("FIXED_ASSET_API_KEY")
if not _API_KEY:
    logger.warning("FIXED_ASSET_API_KEY not set. Running in local dev mode (no auth).")


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Verify API key from X-API-Key header. Skip if key not configured (dev mode)."""
    if not _API_KEY:
        return
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# --- C-02: Path Traversal Prevention ---
def _validate_policy_path(policy_path: Optional[str]) -> Optional[str]:
    """Validate and sanitize policy_path to prevent path traversal."""
    if policy_path is None:
        return None
    if ".." in policy_path or "/" in policy_path or "\\" in policy_path:
        raise HTTPException(
            status_code=400,
            detail="Invalid policy_path: directory traversal not allowed",
        )
    safe_name = os.path.basename(policy_path)
    resolved = (PROJECT_ROOT / "policies" / safe_name).resolve()
    policies_dir = (PROJECT_ROOT / "policies").resolve()
    if not str(resolved).startswith(str(policies_dir)):
        raise HTTPException(
            status_code=400,
            detail="Invalid policy_path: must be within policies directory",
        )
    return str(resolved)


# --- C-03: Upload Validation ---
_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
_MAX_BATCH_FILES = 20


async def _validate_pdf_upload(file: UploadFile) -> bytes:
    """Validate PDF upload: MIME type, magic bytes, size limit."""
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only application/pdf is allowed.",
        )
    content = await file.read()
    if len(content) > _MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(content)} bytes. Maximum is 50MB.",
        )
    if not content[:4] == b"%PDF":
        raise HTTPException(
            status_code=400,
            detail="Invalid file: not a valid PDF (magic bytes check failed).",
        )
    return content


def _get_guidance_citations(
    classified: Dict[str, Any],
    missing_fields: List[str],
    gemini_used: bool = False,
) -> List[Dict[str, Any]]:
    """
    Fetch legal/regulation citations via Vertex AI Search for GUIDANCE cases.

    Pattern 5: GCP複数サービス活用 — Gemini + Vertex AI Search連携。
    GUIDANCE判定時に関連法令・通達を自動検索し、citationsに追加する。

    Returns empty list if:
    - VERTEX_SEARCH_AVAILABLE is False (library not installed)
    - VERTEX_SEARCH_ENABLED=0 (feature disabled, default)
    - No GUIDANCE items found
    """
    if not VERTEX_SEARCH_AVAILABLE:
        return []

    guidance_items = [
        item for item in classified.get("line_items", [])
        if isinstance(item, dict) and item.get("classification") == "GUIDANCE"
    ]
    if not guidance_items:
        return []

    # Combine descriptions from ALL guidance items (not just the first)
    descriptions = [
        item.get("description", "")
        for item in guidance_items
        if item.get("description")
    ]
    combined_desc = " ".join(descriptions[:3])

    # Enrich with Gemini's document-level reasons for better search relevance
    if gemini_used:
        gemini_reasons = classified.get("gemini_reasons", [])
        if gemini_reasons:
            combined_desc = f"{combined_desc} {' '.join(gemini_reasons[:2])}"

    # Collect flags from all guidance items
    all_flags: List[str] = []
    for item in guidance_items:
        flags = item.get("flags", [])
        if isinstance(flags, list):
            all_flags.extend(flags)

    return get_citations_for_guidance(
        description=combined_desc,
        missing_fields=missing_fields,
        flags=all_flags,
    )

app = FastAPI(title="Fixed Asset Classification API", version="1.0.0")

# --- CORS Middleware ---
_cors_origins_str = os.environ.get("CORS_ORIGINS", "http://localhost:8501")
_cors_origins = [o.strip() for o in _cors_origins_str.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# --- Rate Limiting (slowapi) ---
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    _RATE_LIMIT_AVAILABLE = True
except ImportError:
    _RATE_LIMIT_AVAILABLE = False
    logger.warning("slowapi not installed. Rate limiting is disabled.")

# Dummy limiter for when slowapi is not available (no-op decorator)
if not _RATE_LIMIT_AVAILABLE:
    class _DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    limiter = _DummyLimiter()


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
    # 免責事項
    disclaimer: str = "この判定結果はAIによる参考情報です。最終的な判断は税理士等の専門家にご確認ください。"


# ---------------------------------------------------------------------------
# AI参考判定: GUIDANCE明細にGeminiの参考判定を付与
# ---------------------------------------------------------------------------
_AI_HINT_LABEL = {
    "CAPITAL_LIKE": "資産寄り",
    "EXPENSE_LIKE": "費用寄り",
    "GUIDANCE": "判定困難",
}


def _add_ai_hints_for_guidance(
    classified: Dict[str, Any],
    trace_steps: List[str],
) -> None:
    """GUIDANCE明細にAI参考判定(ai_hint)を付与する（in-place更新）。

    Phase 1: Gemini APIで参考判定を取得（15秒タイムアウト）。
    Phase 2 (fallback): flagsからヒューリスティックに推定。
    """
    line_items = classified.get("line_items", [])
    guidance_items = [
        item for item in line_items
        if isinstance(item, dict) and item.get("classification") == "GUIDANCE"
    ]
    if not guidance_items:
        return

    # Phase 1: Gemini APIで参考判定
    gemini_succeeded = False
    if GEMINI_ENABLED and GEMINI_AVAILABLE:
        try:
            from google import genai
            from google.genai import types

            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true":
                client = genai.Client(http_options=types.HttpOptions(timeout=8_000))
            elif api_key:
                client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=8_000))
            else:
                client = None

            if client:
                items_text = "\n".join(
                    f"- {item.get('description', '')} ({item.get('amount', 0):,}円)"
                    for item in guidance_items
                )
                prompt = (
                    "以下の明細について、固定資産(CAPITAL_LIKE)か経費(EXPENSE_LIKE)か参考判定してください。\n"
                    "各明細をJSON配列で返してください。\n"
                    f"```\n{items_text}\n```\n"
                    '返却形式: [{"description":"...","suggestion":"CAPITAL_LIKE or EXPENSE_LIKE","confidence":0.0-1.0,"reasoning":"理由"}]'
                )
                model_name = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                hints = json.loads(response.text)
                if not isinstance(hints, list):
                    hints = [hints]

                hints_by_desc = {h.get("description", ""): h for h in hints if isinstance(h, dict)}
                for i, item in enumerate(guidance_items):
                    h = None
                    if i < len(hints) and isinstance(hints[i], dict):
                        h = hints[i]
                    elif item.get("description") and item["description"] in hints_by_desc:
                        h = hints_by_desc[item["description"]]

                    if h:
                        suggestion = h.get("suggestion", "GUIDANCE")
                        item["ai_hint"] = {
                            "suggestion": suggestion,
                            "suggestion_label": _AI_HINT_LABEL.get(suggestion, "不明"),
                            "confidence": h.get("confidence", 0.5),
                            "reasoning": h.get("reasoning", ""),
                        }
                gemini_succeeded = True
                trace_steps.append("ai_hint")
        except Exception as e:
            logger.warning("AI hint (Gemini) failed, using heuristic fallback: %s", e)

    # Phase 2: フラグベースのヒューリスティック推定（Gemini失敗時のフォールバック）
    if not gemini_succeeded:
        from core import schema
        # 既にclassify_line_itemで分析されたflagsから推定
        _EXPENSE_FLAGS = {"撤去", "廃棄", "処分", "解体", "除却", "原状回復"}
        _CAPITAL_FLAGS = {"新設", "設置", "導入", "構築", "整備", "購入", "増設", "改修"}
        for item in guidance_items:
            if item.get("ai_hint"):
                continue  # Already set by Gemini
            desc = item.get("description", "")
            flags = item.get("flags", [])
            # flagsからキーワード推定
            has_expense_kw = any(kw in desc for kw in _EXPENSE_FLAGS)
            has_capital_kw = any(kw in desc for kw in _CAPITAL_FLAGS)
            if has_expense_kw and not has_capital_kw:
                item["ai_hint"] = {
                    "suggestion": schema.EXPENSE_LIKE,
                    "suggestion_label": "費用寄り",
                    "confidence": 0.6,
                    "reasoning": f"「{'・'.join(kw for kw in _EXPENSE_FLAGS if kw in desc)}」を含むため費用の可能性",
                }
            elif has_capital_kw and not has_expense_kw:
                item["ai_hint"] = {
                    "suggestion": schema.CAPITAL_LIKE,
                    "suggestion_label": "資産寄り",
                    "confidence": 0.6,
                    "reasoning": f"「{'・'.join(kw for kw in _CAPITAL_FLAGS if kw in desc)}」を含むため資産の可能性",
                }
            elif has_expense_kw and has_capital_kw:
                item["ai_hint"] = {
                    "suggestion": "GUIDANCE",
                    "suggestion_label": "判定困難",
                    "confidence": 0.3,
                    "reasoning": "資産・費用の両方のキーワードが混在",
                }
            # キーワードなしの場合はai_hintなし（情報不足）
        if any(item.get("ai_hint") for item in guidance_items):
            trace_steps.append("ai_hint_heuristic")


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

    # Collect classifications and guidance items
    classifications = []
    guidance_items = []
    for item in line_items:
        if isinstance(item, dict):
            cls = item.get("classification")
            if cls:
                classifications.append(cls)
                if cls == "GUIDANCE":
                    guidance_items.append(item)

    # decision: always aggregate from individual line item classifications
    # (gemini_decision is kept as reference only, not used for final decision)
    gemini_decision = doc.get("gemini_decision")
    if not classifications:
        decision = "UNKNOWN"
    else:
        capital_count = sum(1 for c in classifications if c == "CAPITAL_LIKE")
        expense_count = sum(1 for c in classifications if c == "EXPENSE_LIKE")
        guidance_count = sum(1 for c in classifications if c == "GUIDANCE")

        # 金額ベースの集計（件数だけでなく金額比率も考慮）
        capital_amount = sum(
            (item.get("amount") or 0) for item in line_items
            if isinstance(item, dict) and item.get("classification") == "CAPITAL_LIKE"
        )
        expense_amount = sum(
            (item.get("amount") or 0) for item in line_items
            if isinstance(item, dict) and item.get("classification") == "EXPENSE_LIKE"
        )
        guidance_amount = sum(
            (item.get("amount") or 0) for item in line_items
            if isinstance(item, dict) and item.get("classification") == "GUIDANCE"
        )
        total_amount = capital_amount + expense_amount + guidance_amount

        if capital_count > 0 and expense_count > 0:
            # Mixed: both capital and expense items present
            decision = "GUIDANCE"
        elif guidance_count == len(classifications):
            decision = "GUIDANCE"
        elif capital_count > 0 and guidance_count > 0:
            # CAPITAL + GUIDANCE混在: 金額ベースでCAPITALが過半数なら CAPITAL_LIKE
            if total_amount > 0 and capital_amount > total_amount * 0.5:
                decision = "CAPITAL_LIKE"
            elif capital_count > guidance_count:
                decision = "CAPITAL_LIKE"
            else:
                decision = "GUIDANCE"
        elif expense_count > 0 and guidance_count > 0:
            # EXPENSE + GUIDANCE混在: 金額ベースでEXPENSEが過半数なら EXPENSE_LIKE
            if total_amount > 0 and expense_amount > total_amount * 0.5:
                decision = "EXPENSE_LIKE"
            elif expense_count > guidance_count:
                decision = "EXPENSE_LIKE"
            else:
                decision = "GUIDANCE"
        elif capital_count > 0:
            decision = "CAPITAL_LIKE"
        elif expense_count > 0:
            decision = "EXPENSE_LIKE"
        else:
            decision = "GUIDANCE"
    
    # reasons: use Gemini document-level reasons if available
    gemini_reasons = doc.get("gemini_reasons")
    reasons: List[str] = []
    if gemini_reasons:
        reasons = list(gemini_reasons)
    else:
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
                item_confidence = item.get("confidence", 0.0)
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
    # 取得価額算出: CAPITAL_LIKE明細 + asset_inclusion明細の合計
    acquisition_cost_total = sum(
        (item.get("amount") or 0) for item in line_items
        if isinstance(item, dict) and item.get("classification") == "CAPITAL_LIKE"
    )
    expense_total_calc = sum(
        (item.get("amount") or 0) for item in line_items
        if isinstance(item, dict) and item.get("classification") == "EXPENSE_LIKE"
    )
    guidance_total_calc = sum(
        (item.get("amount") or 0) for item in line_items
        if isinstance(item, dict) and item.get("classification") == "GUIDANCE"
    )
    metadata["acquisition_cost_total"] = acquisition_cost_total
    metadata["expense_total"] = expense_total_calc
    metadata["guidance_total"] = guidance_total_calc

    # Add Gemini acquisition cost breakdown if available (overrides rule-based)
    if doc.get("gemini_acquisition_cost_total") is not None:
        metadata["acquisition_cost_total"] = doc["gemini_acquisition_cost_total"]
        metadata["excluded_total"] = doc.get("gemini_excluded_total", 0)
        metadata["expense_total"] = doc.get("gemini_expense_total", 0)
        metadata["estimated_useful_life_years"] = doc.get("gemini_estimated_useful_life_years", 0)
        metadata["useful_life_basis"] = doc.get("gemini_useful_life_basis", "")
        metadata["asset_category"] = doc.get("gemini_asset_category", "")
        metadata["reasoning"] = doc.get("gemini_reasoning", "")
    # Preserve Gemini document-level decision as reference (not used for final decision)
    if gemini_decision:
        metadata["gemini_decision_document"] = gemini_decision
        metadata["gemini_confidence_document"] = doc.get("gemini_confidence_document", 0.0)
    
    # WIN+1: additive fields
    is_valid_document = bool(doc.get("document_info")) and len(line_items) > 0

    # confidence: aggregate from per-item confidences (not document-level)
    if decision in ("CAPITAL_LIKE", "EXPENSE_LIKE"):
        matching_confidences = [
            item.get("confidence", 0.0)
            for item in line_items
            if isinstance(item, dict) and item.get("classification") == decision
        ]
        confidence = max(matching_confidences) if matching_confidences else 0.7
    else:
        confidences = [e.get("confidence", 0.0) for e in evidence]
        confidence = sum(confidences) / len(confidences) if confidences else 0.5
    
    # missing_fields and why_missing_matters: use Gemini results if available
    gemini_missing = doc.get("gemini_missing_fields")
    gemini_why = doc.get("gemini_why_missing_matters")
    if gemini_missing is not None:
        missing_fields = list(gemini_missing)
        why_missing_matters = list(gemini_why) if gemini_why else []
    else:
        missing_fields = []
        why_missing_matters = []
        _internal_flags = {"api_error", "parse_error", "no_keywords", "conflicting_keywords"}
        if decision == "GUIDANCE":
            for item in guidance_items:
                flags = item.get("flags", [])
                desc = item.get("description", "")
                user_flags = [f for f in flags if isinstance(f, str) and f not in _internal_flags and not f.startswith("policy:") and not f.startswith("tax_rule:")]
                if user_flags:
                    missing_fields.extend([f"{desc}:{f}" for f in user_flags])
                    why_missing_matters.append(f"'{desc}' の追加情報があれば判定できる可能性があります")
            missing_fields = list(set(missing_fields))
            why_missing_matters = list(set(why_missing_matters))
            if not missing_fields:
                missing_fields = ["この支出の目的（修繕 or 新規購入）"]
                why_missing_matters = ["支出目的により固定資産か経費かの判断が変わります"]

    # trace: execution steps
    if trace_steps is None:
        trace_steps = ["extract", "parse", "rules", "format"]
    
    # citations: legal/regulation references (from Vertex AI Search if enabled)
    if citations is None:
        citations = []
    
    # line_items for UI display (description, amount, classification, etc.)
    formatted_line_items: List[Dict[str, Any]] = []
    for item in line_items:
        if isinstance(item, dict):
            formatted_item = {
                "line_no": item.get("line_no"),
                "description": item.get("description", ""),
                "amount": item.get("amount"),
                "classification": item.get("classification"),
                "confidence": item.get("confidence"),
                "label_ja": item.get("label_ja", ""),
            }
            if "included_in_acquisition_cost" in item:
                formatted_item["included_in_acquisition_cost"] = item["included_in_acquisition_cost"]
            if item.get("rationale_ja"):
                formatted_item["reason"] = item["rationale_ja"]
            if item.get("flags"):
                formatted_item["flags"] = item["flags"]
            if item.get("ai_hint"):
                formatted_item["ai_hint"] = item["ai_hint"]
            formatted_line_items.append(formatted_item)

    # 免責表示
    disclaimer = "この判定結果はAIによる参考情報です。最終的な判断は税理士等の専門家にご確認ください。"
    if confidence > 0.9:
        disclaimer += " 高確信度の判定ですが、必ず専門家の確認を受けてください。"

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
        disclaimer=disclaimer,
    )



# --- RISK-006: Gemini Connection State ---
_gemini_connection_ok: bool = False
_gemini_connection_error: Optional[str] = None


@app.on_event("startup")
async def startup_gemini_check():
    """Test Gemini API connectivity at startup."""
    global _gemini_connection_ok, _gemini_connection_error
    if not GEMINI_ENABLED or not GEMINI_AVAILABLE:
        logger.info("Gemini disabled or unavailable, skipping startup connection test")
        return
    try:
        from google import genai
        client = genai.Client()
        list(client.models.list(config={"page_size": 1}))
        _gemini_connection_ok = True
        logger.info("Startup Gemini connection test: SUCCESS")
    except Exception as e:
        _gemini_connection_ok = False
        _gemini_connection_error = str(e)
        logger.warning("Startup Gemini connection test FAILED: %s", e)


@app.get("/healthz")
@app.get("/health")
@limiter.limit("30/minute")
async def healthz(request: Request) -> Dict[str, Any]:
    """Health check endpoint. Cloud Run reserves /healthz, so /health also works."""
    return {
        "ok": True,
        "gemini_available": GEMINI_AVAILABLE,
        "gemini_enabled": GEMINI_ENABLED,
        "gemini_connected": _gemini_connection_ok,
    }

@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request) -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "Fixed Asset Classification API", "version": "1.0.0"}


@app.post("/classify", response_model=ClassifyResponse)
@limiter.limit("10/minute")
async def classify(request: Request, body: ClassifyRequest, _auth: None = Depends(verify_api_key)) -> ClassifyResponse:
    """
    Classify fixed asset items from Opal JSON.

    Uses existing core.adapter and core.classifier functions.
    WIN+1: Supports agentic loop with answers for GUIDANCE cases.

    Gemini Integration (GEMINI_ENABLED=1):
    - First attempts classification with Gemini API
    - Falls back to rule-based classifier on failure
    """
    req_id = str(uuid.uuid4())[:8]
    logger.info("POST /classify start", extra={"request_id": req_id})
    try:
        trace_steps = ["extract"]
        # Use existing pipeline functions
        opal_json = body.opal_json

        # Normalize using adapter
        normalized = adapt_opal_to_v1(opal_json)
        trace_steps.append("parse")

        # Load policy (default to company_default.json if not provided)
        policy_path = _validate_policy_path(body.policy_path)
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
                trace_steps.append("gemini")
                line_items = normalized.get("line_items", [])
                doc_info = normalized.get("document_info", {})

                # Build context string with document metadata
                # NOTE: 合計金額は渡さない（個別明細の金額で判定させるため）
                title = doc_info.get("title", "")
                vendor = doc_info.get("vendor", "")
                context_parts = []
                if title:
                    context_parts.append(f"書類タイトル: {title}")
                if vendor:
                    context_parts.append(f"取引先: {vendor}")
                context_parts.append(f"明細件数: {len(line_items)}")
                context_str = "\n".join(context_parts)

                # Single batch call to Gemini (new SDK: list input)
                gemini_result = classify_with_gemini(
                    line_items,
                    context_str,
                    document_info={"title": title, "vendor": vendor},
                )

                # Merge line_item_analysis into line_items
                lia = gemini_result.get("line_item_analysis", [])
                # Build description-based lookup for fallback matching
                lia_by_desc = {}
                for a in lia:
                    if isinstance(a, dict) and a.get("description"):
                        lia_by_desc[a["description"]] = a

                doc_confidence = gemini_result.get("confidence", 0.0)
                doc_flags = gemini_result.get("flags", [])
                for i, item in enumerate(line_items):
                    # Index-based match first, description-based fallback
                    analysis = None
                    if i < len(lia) and isinstance(lia[i], dict):
                        analysis = lia[i]
                    elif item.get("description") and item["description"] in lia_by_desc:
                        analysis = lia_by_desc[item["description"]]

                    if analysis:
                        item["classification"] = analysis.get("classification", "GUIDANCE")
                        item["included_in_acquisition_cost"] = analysis.get("included_in_acquisition_cost", False)
                        item["rationale_ja"] = analysis.get("reason", "")
                        # Per-item confidence/flags, fallback to document-level
                        item["confidence"] = analysis.get("confidence", doc_confidence)
                        item["flags"] = analysis.get("flags", doc_flags)
                    else:
                        item["classification"] = "GUIDANCE"
                        item["rationale_ja"] = ""
                        item["confidence"] = doc_confidence
                        item["flags"] = doc_flags
                    item["label_ja"] = {
                        "CAPITAL_LIKE": "資産寄り",
                        "EXPENSE_LIKE": "費用寄り",
                        "GUIDANCE": "要確認（判定しません）",
                    }.get(item["classification"], "要確認")

                # Store Gemini document-level results (reference only, not used for final decision)
                normalized["gemini_decision"] = gemini_result.get("decision", "GUIDANCE")
                normalized["gemini_confidence_document"] = gemini_result.get("confidence", 0.0)
                normalized["gemini_reasons"] = gemini_result.get("reasons", [])
                normalized["gemini_missing_fields"] = gemini_result.get("missing_fields", [])
                normalized["gemini_why_missing_matters"] = gemini_result.get("why_missing_matters", [])
                normalized["gemini_acquisition_cost_total"] = gemini_result.get("acquisition_cost_total", 0)
                normalized["gemini_excluded_total"] = gemini_result.get("excluded_total", 0)
                normalized["gemini_expense_total"] = gemini_result.get("expense_total", 0)
                normalized["gemini_estimated_useful_life_years"] = gemini_result.get("estimated_useful_life_years", 0)
                normalized["gemini_useful_life_basis"] = gemini_result.get("useful_life_basis", "")
                normalized["gemini_asset_category"] = gemini_result.get("asset_category", "")
                normalized["gemini_reasoning"] = gemini_result.get("reasoning", "")

                classified = normalized
                gemini_used = True
                trace_steps.append("gemini_success")

            except Exception as e:
                # Gemini failed - fall back to rule-based
                logger.exception("Gemini classification failed, falling back to rule-based: %s", e)
                trace_steps.append("gemini_fallback")
                classified = None

        # Rule-based classification (default or fallback)
        if classified is None:
            classified = classify_document(normalized, policy)
            trace_steps.append("rules")

            # AI参考判定: GUIDANCE明細がある場合、Geminiで参考判定を取得
            _add_ai_hints_for_guidance(classified, trace_steps)

        # Format initial response
        initial_response = _format_classify_response(classified, trace_steps=trace_steps.copy())
        
        # Google Cloud: Vertex AI Search for legal citations (GUIDANCE時に法令検索)
        citations: List[Dict[str, Any]] = []
        if initial_response.decision == "GUIDANCE":
            citations = _get_guidance_citations(
                classified,
                missing_fields=initial_response.missing_fields,
                gemini_used=gemini_used,
            )
            if citations:
                trace_steps.append("vertex_search")
                initial_response = _format_classify_response(
                    classified,
                    trace_steps=trace_steps.copy(),
                    citations=citations,
                )
        
        # WIN+1: Minimal agentic loop - if GUIDANCE and answers provided, try rerun
        if initial_response.decision == "GUIDANCE" and body.answers and initial_response.missing_fields:
            # Check if answers cover missing fields
            answered_fields = set(body.answers.keys())
            missing_set = set(initial_response.missing_fields)
            # Simple heuristic: if answers match any missing field pattern
            if answered_fields and any(k in str(mf).lower() for mf in missing_set for k in answered_fields):
                trace_steps.append("rerun_with_answers")
                # Apply answers to opal_json (merge into line items or document_info)
                enhanced_opal = opal_json.copy()
                # Simple merge: add answers to document_info context
                if "document_info" not in enhanced_opal:
                    enhanced_opal["document_info"] = {}
                enhanced_opal["document_info"]["user_answers"] = body.answers
                
                # Rerun classification
                enhanced_normalized = adapt_opal_to_v1(enhanced_opal)
                enhanced_classified = classify_document(enhanced_normalized, policy)
                trace_steps.append("format")
                # Preserve citations in rerun response
                return _format_classify_response(enhanced_classified, trace_steps=trace_steps, citations=citations)
        
        trace_steps.append("format")
        logger.info("POST /classify done decision=%s", initial_response.decision, extra={"request_id": req_id})
        return initial_response

    except ValueError as e:
        logger.error("POST /classify ValueError: %s", e, extra={"request_id": req_id})
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        logger.exception("POST /classify unexpected error: %s", e, extra={"request_id": req_id})
        raise HTTPException(status_code=500, detail="Classification failed. Please check input format.")


@app.post("/classify_pdf", response_model=ClassifyResponse)
@limiter.limit("10/minute")
async def classify_pdf(
    request: Request,
    file: UploadFile = File(...),
    policy_path: Optional[str] = None,
    use_gemini_vision: Optional[str] = None,
    estimate_useful_life_flag: Optional[str] = None,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    _auth: None = Depends(verify_api_key),
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
    req_id = str(uuid.uuid4())[:8]
    logger.info("POST /classify_pdf start file=%s", file.filename, extra={"request_id": req_id})

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

        # Validate and save uploaded PDF to temporary file
        content = await _validate_pdf_upload(file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_path = Path(tmp_file.name)
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
            validated_policy_path = _validate_policy_path(policy_path)
            if not validated_policy_path:
                default_policy = PROJECT_ROOT / "policies" / "company_default.json"
                if default_policy.exists():
                    validated_policy_path = str(default_policy)

            policy = load_policy(validated_policy_path)
            
            # Classify
            classified = classify_document(normalized, policy)
            trace_steps.append("rules")

            # AI参考判定: GUIDANCE明細がある場合、Geminiで参考判定を取得
            _add_ai_hints_for_guidance(classified, trace_steps)

            # Add warnings from extraction
            warnings = extraction.get("meta", {}).get("warnings", [])
            if warnings:
                if "warnings" not in classified:
                    classified["warnings"] = []
                classified["warnings"].extend(warnings)
            
            # Format response (same as /classify)
            initial_response = _format_classify_response(classified, trace_steps=trace_steps.copy())
            
            # Google Cloud: Vertex AI Search citations (GUIDANCE時に法令検索)
            citations: List[Dict[str, Any]] = []
            if initial_response.decision == "GUIDANCE":
                citations = _get_guidance_citations(
                    classified,
                    missing_fields=initial_response.missing_fields,
                )
                if citations:
                    trace_steps.append("vertex_search")
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
            response = _format_classify_response(
                classified,
                trace_steps=trace_steps,
                citations=citations,
                useful_life=useful_life_result,
            )
            logger.info("POST /classify_pdf done decision=%s file=%s", response.decision, file.filename, extra={"request_id": req_id})
            return response

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
        logger.error("POST /classify_pdf ValueError: %s", e, extra={"request_id": req_id})
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PDF_CLASSIFY_ERROR",
                "message": f"Invalid PDF: {str(e)}",
                "how_to_enable": None,
            },
        )
    except Exception as e:
        logger.exception("POST /classify_pdf unexpected error: %s", e, extra={"request_id": req_id})
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
@limiter.limit("5/minute")
async def classify_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    policy_path: Optional[str] = None,
    use_gemini_vision: Optional[str] = None,
    estimate_useful_life_flag: Optional[str] = None,
    _auth: None = Depends(verify_api_key),
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

    # File count limit (C-03)
    if len(files) > _MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files: {len(files)}. Maximum is {_MAX_BATCH_FILES}.",
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
            logger.exception("Batch item '%s' failed unexpectedly: %s", filename, e)
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

    # Validate and save uploaded PDF to temporary file
    content = await _validate_pdf_upload(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_path = Path(tmp_file.name)
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
        actual_policy_path = _validate_policy_path(policy_path)
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

        # Google Cloud: Vertex AI Search citations (GUIDANCE時に法令検索)
        citations: List[Dict[str, Any]] = []
        if initial_response.decision == "GUIDANCE":
            citations = _get_guidance_citations(
                classified,
                missing_fields=initial_response.missing_fields,
            )
            if citations:
                trace_steps.append("vertex_search")
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
