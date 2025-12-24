import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pytest
from app.generation import generate_policy_response


def test_generation_refuses_when_no_chunks():
    """
    Test that generation refuses when no relevant policy chunks are found.
    This prevents hallucination - the system must fail closed without sources.
    """
    response = generate_policy_response(
        query="quantum teleportation advertising regulations",
        limit=3
    )
    assert response.refused is True
    assert response.answer == ""
    assert response.refusal_reason is not None


def test_generation_refuses_low_confidence(mocker):
    """
    Test that generation refuses when retrieval confidence is below threshold.
    Even if chunks are returned, low similarity scores indicate weak matches.
    """
    mocker.patch(
        "app.generation.retrieve_policy_chunks",
        return_value=[{
            "chunk_id": "test-id",
            "chunk_text": "irrelevant text",
            "score": 0.01,
            "policy_path": "test",
            "doc_id": "test",
            "doc_url": "test"
        }]
    )
    
    response = generate_policy_response("random query")
    assert response.refused is True
    assert "Insufficient confidence" in response.refusal_reason


def test_generation_requires_valid_citations(mocker):
    """
    Test that generation refuses when LLM cites sources that weren't retrieved.
    This prevents citation hallucination - all citations must reference actual chunks.
    """
    mock_chunks = [{
        "chunk_id": "real-chunk-id",
        "chunk_text": "Alcohol advertising is restricted.",
        "score": 0.8,
        "policy_path": "Restricted content > Alcohol",
        "doc_id": "doc-1",
        "doc_url": "https://example.com"
    }]
    
    mocker.patch(
        "app.generation.retrieve_policy_chunks",
        return_value=mock_chunks
    )
    
    mocker.patch(
        "app.generation.extract_citations",
        return_value={"fake-citation-id", "another-fake-id"}
    )
    
    response = generate_policy_response("Can I advertise alcohol?")
    assert response.refused is True
    assert "citation validation" in response.refusal_reason


def test_generation_success_has_citations():
    """
    Test that successful generation includes at least one citation.
    This verifies the grounding requirement - answers must reference sources.
    """
    response = generate_policy_response(
        query="Can I advertise alcohol?",
        limit=5
    )
    
    assert response.refused is False
    assert len(response.citations) > 0
    assert response.answer != ""
    assert "[SOURCE:" in response.answer


def test_generation_includes_metrics():
    """
    Test that response includes performance metrics for monitoring.
    """
    response = generate_policy_response(
        query="Can I advertise alcohol?",
        limit=3
    )
    
    assert response.latency_ms is not None
    assert response.latency_ms > 0
    
    if not response.refused:
        assert response.num_tokens_generated is not None
        assert response.num_tokens_generated > 0
