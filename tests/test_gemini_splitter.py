# -*- coding: utf-8 -*-
"""
Tests for gemini_splitter module.
"""
import json
import os
import pytest
from unittest.mock import MagicMock, patch


class TestParseBoundaryResponse:
    """Test _parse_boundary_response function."""

    def test_parse_valid_single_document(self):
        """Single document should be parsed correctly."""
        from api.gemini_splitter import _parse_boundary_response

        response = json.dumps({
            "documents": [
                {"start_page": 1, "end_page": 5, "type": "見積書"}
            ]
        })

        result = _parse_boundary_response(response, total_pages=5)

        assert len(result) == 1
        assert result[0]["document_id"] == 1
        assert result[0]["start_page"] == 1
        assert result[0]["end_page"] == 5
        assert result[0]["doc_type"] == "見積書"

    def test_parse_valid_multiple_documents(self):
        """Multiple documents should be parsed and sorted correctly."""
        from api.gemini_splitter import _parse_boundary_response

        response = json.dumps({
            "documents": [
                {"start_page": 4, "end_page": 5, "type": "請求書"},
                {"start_page": 1, "end_page": 3, "type": "見積書"},
            ]
        })

        result = _parse_boundary_response(response, total_pages=5)

        assert len(result) == 2
        # Should be sorted by start_page
        assert result[0]["start_page"] == 1
        assert result[0]["end_page"] == 3
        assert result[0]["doc_type"] == "見積書"
        assert result[0]["document_id"] == 1

        assert result[1]["start_page"] == 4
        assert result[1]["end_page"] == 5
        assert result[1]["doc_type"] == "請求書"
        assert result[1]["document_id"] == 2

    def test_parse_unknown_doc_type_becomes_other(self):
        """Unknown document types should become 'その他'."""
        from api.gemini_splitter import _parse_boundary_response

        response = json.dumps({
            "documents": [
                {"start_page": 1, "end_page": 3, "type": "レポート"}
            ]
        })

        result = _parse_boundary_response(response, total_pages=3)

        assert result[0]["doc_type"] == "その他"

    def test_parse_invalid_json_returns_default(self):
        """Invalid JSON should return default single document."""
        from api.gemini_splitter import _parse_boundary_response

        result = _parse_boundary_response("not valid json", total_pages=5)

        assert len(result) == 1
        assert result[0]["start_page"] == 1
        assert result[0]["end_page"] == 5
        assert "error" in result[0]

    def test_parse_json_with_extra_text(self):
        """JSON embedded in text should be extracted."""
        from api.gemini_splitter import _parse_boundary_response

        response = 'Here is the result: {"documents": [{"start_page": 1, "end_page": 2, "type": "納品書"}]}'

        result = _parse_boundary_response(response, total_pages=2)

        assert len(result) == 1
        assert result[0]["doc_type"] == "納品書"

    def test_parse_empty_documents_returns_default(self):
        """Empty documents array should return default."""
        from api.gemini_splitter import _parse_boundary_response

        response = json.dumps({"documents": []})

        result = _parse_boundary_response(response, total_pages=3)

        assert len(result) == 1
        assert result[0]["start_page"] == 1
        assert result[0]["end_page"] == 3

    def test_parse_end_page_exceeds_total_is_capped(self):
        """End page exceeding total_pages should be capped."""
        from api.gemini_splitter import _parse_boundary_response

        response = json.dumps({
            "documents": [
                {"start_page": 1, "end_page": 100, "type": "見積書"}
            ]
        })

        result = _parse_boundary_response(response, total_pages=5)

        assert result[0]["end_page"] == 5

    def test_parse_result_as_array_directly(self):
        """Result that is directly an array should be handled."""
        from api.gemini_splitter import _parse_boundary_response

        response = json.dumps([
            {"start_page": 1, "end_page": 2, "type": "契約書"}
        ])

        result = _parse_boundary_response(response, total_pages=2)

        assert len(result) == 1
        assert result[0]["doc_type"] == "契約書"

    def test_parse_with_doc_type_key(self):
        """Support both 'type' and 'doc_type' keys."""
        from api.gemini_splitter import _parse_boundary_response

        response = json.dumps({
            "documents": [
                {"start_page": 1, "end_page": 2, "doc_type": "領収書"}
            ]
        })

        result = _parse_boundary_response(response, total_pages=2)

        assert result[0]["doc_type"] == "領収書"


class TestDetectDocumentBoundaries:
    """Test detect_document_boundaries function."""

    def test_no_api_key_returns_default(self):
        """Without API key, should return default document."""
        from api.gemini_splitter import detect_document_boundaries

        # Ensure no API key
        with patch.dict(os.environ, {}, clear=True):
            # Remove GOOGLE_API_KEY if it exists
            os.environ.pop("GOOGLE_API_KEY", None)

            result = detect_document_boundaries(b"fake image bytes", total_pages=3)

        assert len(result) == 1
        assert result[0]["start_page"] == 1
        assert result[0]["end_page"] == 3
        assert "error" in result[0]
        assert "GOOGLE_API_KEY" in result[0]["error"]

    @patch("api.gemini_splitter.genai", create=True)
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    def test_api_call_success(self, mock_genai):
        """Successful API call should return parsed documents."""
        # This test requires mocking the entire genai module
        # Skip in unit tests, test in integration tests
        pytest.skip("Requires live API or complex mocking")


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("api.gemini_splitter.detect_document_boundaries")
    def test_detect_boundaries_from_base64(self, mock_detect):
        """Base64 function should decode and call main function."""
        from api.gemini_splitter import detect_boundaries_from_base64
        import base64

        mock_detect.return_value = [{"document_id": 1}]

        # Create base64 encoded test data
        test_bytes = b"test image data"
        b64_data = base64.b64encode(test_bytes).decode()

        result = detect_boundaries_from_base64(b64_data, total_pages=5)

        mock_detect.assert_called_once()
        call_args = mock_detect.call_args
        assert call_args[0][0] == test_bytes
        assert call_args[0][1] == 5

    @patch("api.gemini_splitter.detect_document_boundaries")
    def test_detect_boundaries_from_base64_with_data_uri(self, mock_detect):
        """Base64 with data URI prefix should be handled."""
        from api.gemini_splitter import detect_boundaries_from_base64
        import base64

        mock_detect.return_value = [{"document_id": 1}]

        test_bytes = b"test image data"
        b64_data = "data:image/png;base64," + base64.b64encode(test_bytes).decode()

        result = detect_boundaries_from_base64(b64_data)

        mock_detect.assert_called_once()
        call_args = mock_detect.call_args
        assert call_args[0][0] == test_bytes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
