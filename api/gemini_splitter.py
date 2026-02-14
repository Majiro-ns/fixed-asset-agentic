# -*- coding: utf-8 -*-
"""
Gemini Vision API integration for PDF document boundary detection.

This module analyzes grid images (thumbnails of PDF pages) to detect
where one document ends and another begins within a multi-document PDF.

Feature-flagged: Only active when API key is configured.
"""
import base64
import json
import os
import re
from typing import Any, Dict, List, Optional


def _bool_env(name: str, default: bool = False) -> bool:
    """Check environment variable for boolean flag."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_model_name() -> str:
    """Get model name from env or use default (flash for speed)."""
    return os.getenv("GEMINI_SPLITTER_MODEL", "gemini-2.0-flash")


# System prompt for document boundary detection
BOUNDARY_DETECTION_PROMPT = """この画像はPDFの各ページをサムネイル化してグリッド表示したものです。
左上から右へ、上から下へページ番号が振られています（1から始まる）。

このPDFには複数の書類が含まれている可能性があります。
各書類の境界を特定し、以下のJSON形式で回答してください:

{
  "documents": [
    {"start_page": 1, "end_page": 3, "type": "見積書"},
    {"start_page": 4, "end_page": 5, "type": "請求書"}
  ]
}

【書類の種類】
以下から選択してください:
- 見積書
- 請求書
- 納品書
- 契約書
- 注文書
- 領収書
- その他

【判定のヒント】
- 新しい書類の開始は、ヘッダーやタイトルの変化で判断
- 会社ロゴ、日付、書類番号の変化に注目
- 「見積書」「請求書」などのタイトルを探す
- 書類が1つしかない場合も正しくJSON形式で返す
- 全ページ数が正しく網羅されているか確認

【重要】
- 必ずJSON形式のみで回答してください
- 説明文は不要です
- start_page と end_page は1から始まるページ番号です
"""


def detect_document_boundaries(
    grid_image: bytes,
    total_pages: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Detect document boundaries from a grid image of PDF thumbnails.

    This function sends a grid image (containing thumbnails of all PDF pages)
    to Gemini Vision API to identify where documents begin and end.

    Args:
        grid_image: PNG/JPEG image bytes of the grid thumbnail
        total_pages: Optional total number of pages (for validation)

    Returns:
        List of document boundary info:
        [
            {"document_id": 1, "start_page": 1, "end_page": 3, "doc_type": "見積書"},
            {"document_id": 2, "start_page": 4, "end_page": 5, "doc_type": "請求書"},
        ]

        On error, returns a single document covering all pages:
        [{"document_id": 1, "start_page": 1, "end_page": total_pages, "doc_type": "その他", "error": "..."}]
    """
    # Default fallback (treat entire PDF as one document)
    default_response = [
        {
            "document_id": 1,
            "start_page": 1,
            "end_page": total_pages or 1,
            "doc_type": "その他",
        }
    ]

    try:
        # Import only when needed
        from google import genai
        from google.genai import types
        from PIL import Image
        import io

        # Configure API (Vertex AI or AI Studio)
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true":
            client = genai.Client()
        elif api_key:
            client = genai.Client(api_key=api_key)
        else:
            default_response[0]["error"] = "認証情報が未設定"
            return default_response

        # Get model
        model_name = _get_model_name()

        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(grid_image))

        # Build prompt with page count hint if available
        prompt = BOUNDARY_DETECTION_PROMPT
        if total_pages:
            prompt += f"\n\n【参考情報】このPDFは全{total_pages}ページです。"

        # Generate response with JSON output
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,  # Low temperature for consistent results
            ),
        )

        # Parse response
        return _parse_boundary_response(response.text, total_pages)

    except ImportError as e:
        default_response[0]["error"] = f"ライブラリ未インストール: {str(e)}"
        return default_response

    except json.JSONDecodeError as e:
        default_response[0]["error"] = f"JSONパースエラー: {str(e)}"
        return default_response

    except Exception as e:
        default_response[0]["error"] = f"API エラー: {str(e)}"
        return default_response


def _parse_boundary_response(
    response_text: str,
    total_pages: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Parse the Gemini API response and convert to standardized format.

    Args:
        response_text: JSON string from Gemini
        total_pages: Optional total pages for validation

    Returns:
        List of document boundary dictionaries
    """
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response if it contains extra text
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                result = json.loads(json_match.group())
            except json.JSONDecodeError:
                return [
                    {
                        "document_id": 1,
                        "start_page": 1,
                        "end_page": total_pages or 1,
                        "doc_type": "その他",
                        "error": f"JSONパースエラー: {response_text[:100]}",
                    }
                ]
        else:
            return [
                {
                    "document_id": 1,
                    "start_page": 1,
                    "end_page": total_pages or 1,
                    "doc_type": "その他",
                    "error": f"JSON形式が見つかりません: {response_text[:100]}",
                }
            ]

    # Handle case where result is the array itself
    if isinstance(result, list):
        documents = result
    else:
        # Extract documents array
        documents = result.get("documents", [])

    # If no documents found, return default
    if not documents:
        return [
            {
                "document_id": 1,
                "start_page": 1,
                "end_page": total_pages or 1,
                "doc_type": "その他",
            }
        ]

    # Normalize and validate documents
    normalized: List[Dict[str, Any]] = []
    valid_types = {"見積書", "請求書", "納品書", "契約書", "注文書", "領収書", "その他"}

    for idx, doc in enumerate(documents):
        if not isinstance(doc, dict):
            continue

        start_page = doc.get("start_page")
        end_page = doc.get("end_page")

        # Validate page numbers
        if not isinstance(start_page, int) or not isinstance(end_page, int):
            continue
        if start_page < 1 or end_page < start_page:
            continue
        if total_pages and end_page > total_pages:
            end_page = total_pages

        # Normalize document type
        doc_type = doc.get("type", doc.get("doc_type", "その他"))
        if doc_type not in valid_types:
            doc_type = "その他"

        normalized.append({
            "document_id": idx + 1,
            "start_page": start_page,
            "end_page": end_page,
            "doc_type": doc_type,
        })

    # If normalization resulted in empty list, return default
    if not normalized:
        return [
            {
                "document_id": 1,
                "start_page": 1,
                "end_page": total_pages or 1,
                "doc_type": "その他",
            }
        ]

    # Sort by start_page
    normalized.sort(key=lambda x: x["start_page"])

    # Re-number document_id after sorting
    for idx, doc in enumerate(normalized):
        doc["document_id"] = idx + 1

    return normalized


def detect_boundaries_from_file(
    grid_image_path: str,
    total_pages: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to detect boundaries from an image file path.

    Args:
        grid_image_path: Path to the grid image file
        total_pages: Optional total number of pages

    Returns:
        List of document boundary dictionaries
    """
    with open(grid_image_path, "rb") as f:
        image_bytes = f.read()
    return detect_document_boundaries(image_bytes, total_pages)


def detect_boundaries_from_base64(
    base64_image: str,
    total_pages: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to detect boundaries from base64-encoded image.

    Args:
        base64_image: Base64-encoded image string
        total_pages: Optional total number of pages

    Returns:
        List of document boundary dictionaries
    """
    # Remove data URI prefix if present
    if "," in base64_image:
        base64_image = base64_image.split(",", 1)[1]

    image_bytes = base64.b64decode(base64_image)
    return detect_document_boundaries(image_bytes, total_pages)


# Alias for backward compatibility
detect_pdf_boundaries = detect_document_boundaries
