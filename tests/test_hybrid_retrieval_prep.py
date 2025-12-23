import pytest
import weaviate
from db.session import SessionLocal
from db.models import PolicyChunk

def test_weaviate_object_id_equals_chunk_id():
    """
    Test that Weaviate object ID (UUID) equals PostgreSQL chunk_id.
    This is critical for hybrid retrieval join operations.
    """
    db = SessionLocal()
    client = weaviate.Client("http://localhost:8080")
    
    try:
        pg_chunks = db.query(PolicyChunk.chunk_id).limit(10).all()
        
        for (pg_chunk_id,) in pg_chunks:
            result = client.data_object.get_by_id(
                str(pg_chunk_id),
                class_name="PolicyChunk"
            )
            
            assert result is not None, (
                f"Weaviate object with ID {pg_chunk_id} not found"
            )
            
            assert result["id"] == str(pg_chunk_id), (
                f"Weaviate object ID mismatch: expected {pg_chunk_id}, got {result['id']}"
            )
            
            assert result["properties"]["chunk_id"] == str(pg_chunk_id), (
                f"chunk_id property mismatch: expected {pg_chunk_id}, "
                f"got {result['properties']['chunk_id']}"
            )
            
    finally:
        db.close()

def test_metadata_fields_stored():
    """
    Test that policy_source, region, content_type, and policy_section_level are stored in Weaviate.
    These fields are required for hybrid retrieval filtering and ranking.
    """
    client = weaviate.Client("http://localhost:8080")
    
    result = client.query.get(
        "PolicyChunk",
        ["chunk_id", "policy_source", "region", "content_type", "policy_section_level"]
    ).with_limit(1).do()
    
    chunks = result.get("data", {}).get("Get", {}).get("PolicyChunk", [])
    
    assert len(chunks) > 0, "No chunks found in Weaviate"
    
    chunk = chunks[0]
    
    assert "policy_source" in chunk, "policy_source field missing"
    assert "region" in chunk, "region field missing"
    assert "content_type" in chunk, "content_type field missing"
    assert "policy_section_level" in chunk, "policy_section_level field missing"
    
    assert chunk["policy_source"].lower() in ["google", "facebook", "twitter"], (
        f"Invalid policy_source: {chunk['policy_source']}"
    )
    assert chunk["region"].upper() in ["GLOBAL", "US", "EU", "UK"], (
        f"Invalid region: {chunk['region']}"
    )
    assert chunk["content_type"].upper() in ["AD_TEXT", "IMAGE", "VIDEO", "LANDING_PAGE", "GENERAL"], (
        f"Invalid content_type: {chunk['content_type']}"
    )
    assert chunk["policy_section_level"] in ["H2", "H3"], (
        f"Invalid policy_section_level: {chunk['policy_section_level']}"
    )

def test_filtering_by_metadata():
    """
    Test that we can filter chunks by region and content_type in Weaviate.
    This validates hybrid retrieval filtering capability.
    """
    client = weaviate.Client("http://localhost:8080")
    
    result = client.query.get(
        "PolicyChunk",
        ["chunk_id", "region", "content_type"]
    ).with_where({
        "operator": "And",
        "operands": [
            {
                "path": ["region"],
                "operator": "Equal",
                "valueText": "global"
            },
            {
                "path": ["content_type"],
                "operator": "Equal",
                "valueText": "general"
            }
        ]
    }).with_limit(10).do()
    
    chunks = result.get("data", {}).get("Get", {}).get("PolicyChunk", [])
    
    assert len(chunks) > 0, "No chunks found matching filter criteria"
    
    for chunk in chunks:
        assert chunk["region"].lower() == "global", f"Filter failed: got region {chunk['region']}"
        assert chunk["content_type"].lower() == "general", f"Filter failed: got content_type {chunk['content_type']}"
