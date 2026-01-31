# -*- coding: utf-8 -*-
"""
Vertex AI Search (Discovery Engine) integration for legal/regulation citations.
Feature-flagged: Only active when VERTEX_SEARCH_ENABLED=1 and credentials configured.
"""
import os
from typing import Any, Dict, List, Optional


def _bool_env(name: str, default: bool = False) -> bool:
    """Check environment variable for boolean flag."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def search_legal_citations(
    query: str,
    project_id: Optional[str] = None,
    location: str = "global",
    data_store_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for legal/regulation citations using Vertex AI Search (Discovery Engine).
    
    Returns list of citation dicts with:
    - title: str
    - snippet: str
    - uri: str (optional)
    - relevance_score: float (optional)
    
    If feature is disabled or unavailable, returns empty list (graceful degradation).
    """
    # Feature flag check
    if not _bool_env("VERTEX_SEARCH_ENABLED", False):
        return []
    
    # Check if required env vars are set
    if not project_id:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        return []  # Graceful skip if not configured
    
    if not data_store_id:
        data_store_id = os.getenv("DISCOVERY_ENGINE_DATA_STORE_ID")
    if not data_store_id:
        return []  # Graceful skip if not configured
    
    try:
        # Import only when feature is enabled (avoids dependency if not used)
        from google.cloud import discoveryengine
        
        # Initialize client
        client = discoveryengine.SearchServiceClient()
        
        # Build search request
        serving_config = client.serving_config_path(
            project=project_id,
            location=location,
            data_store=data_store_id,
            serving_config="default_search",
        )
        
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=3,  # Limit to top 3 results
        )
        
        # Execute search
        response = client.search(request=request)
        
        # Format results
        citations: List[Dict[str, Any]] = []
        for result in response.results:
            doc = result.document
            citation = {
                "title": getattr(doc, "title", "Untitled"),
                "snippet": getattr(doc, "snippet", ""),
            }
            # Add URI if available
            if hasattr(doc, "struct_data") and isinstance(doc.struct_data, dict):
                uri = doc.struct_data.get("uri") or doc.struct_data.get("link")
                if uri:
                    citation["uri"] = uri
            # Add relevance score if available
            if hasattr(result, "relevance_score"):
                citation["relevance_score"] = float(result.relevance_score)
            
            citations.append(citation)
        
        return citations
        
    except ImportError:
        # google-cloud-discoveryengine not installed
        return []
    except Exception:
        # Any other error: graceful degradation
        return []


def get_citations_for_guidance(
    description: str,
    missing_fields: List[str],
    flags: List[str],
) -> List[Dict[str, Any]]:
    """
    Generate search query from GUIDANCE context and return citations.
    
    Args:
        description: Line item description
        missing_fields: List of missing field hints
        flags: Classification flags
    
    Returns:
        List of citation dicts
    """
    # Build search query from context
    query_parts = []
    
    # Add description keywords
    if description:
        # Extract key terms (simple heuristic: non-stopwords)
        words = description.split()
        # Filter common stopwords (Japanese)
        stopwords = {"の", "を", "に", "は", "が", "と", "で", "など", "及び"}
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        if keywords:
            query_parts.extend(keywords[:3])  # Top 3 keywords
    
    # Add tax/accounting context
    query_parts.append("固定資産 判定")
    if "mixed_keyword" in str(flags):
        query_parts.append("修繕費 資本的支出")
    if any("amount" in str(f) for f in flags):
        query_parts.append("金額基準 20万円 60万円")
    
    # Combine into query
    query = " ".join(query_parts[:5])  # Limit query length
    
    # Search
    return search_legal_citations(query)
