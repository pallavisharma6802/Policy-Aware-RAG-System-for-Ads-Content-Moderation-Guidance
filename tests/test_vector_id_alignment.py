import pytest
import weaviate
from db.session import SessionLocal
from db.models import PolicyChunk

def test_vector_id_alignment():
    """
    Test that Weaviate object IDs match PostgreSQL chunk_ids.
    This ensures both systems can be joined on chunk_id.
    """
    db = SessionLocal()
    client = weaviate.Client("http://localhost:8080")
    
    try:
        pg_chunk_ids = set(
            str(chunk_id) for (chunk_id,) in db.query(PolicyChunk.chunk_id).all()
        )
        
        result = client.query.aggregate("PolicyChunk").with_meta_count().do()
        wv_count = result['data']['Aggregate']['PolicyChunk'][0]['meta']['count']
        
        result = client.query.get("PolicyChunk", ["chunk_id"]).with_limit(wv_count).do()
        wv_chunks = result.get("data", {}).get("Get", {}).get("PolicyChunk", [])
        wv_chunk_ids = set(chunk["chunk_id"] for chunk in wv_chunks)
        
        missing_in_weaviate = pg_chunk_ids - wv_chunk_ids
        extra_in_weaviate = wv_chunk_ids - pg_chunk_ids
        
        assert len(missing_in_weaviate) == 0, (
            f"{len(missing_in_weaviate)} chunk_ids in PostgreSQL but not in Weaviate: "
            f"{list(missing_in_weaviate)[:5]}"
        )
        
        assert len(extra_in_weaviate) == 0, (
            f"{len(extra_in_weaviate)} chunk_ids in Weaviate but not in PostgreSQL: "
            f"{list(extra_in_weaviate)[:5]}"
        )
        
        assert pg_chunk_ids == wv_chunk_ids, "chunk_id sets must match exactly"
        
    finally:
        db.close()

def test_no_regenerated_ids():
    """
    Test that chunk_ids are preserved during embedding ingestion.
    Re-running embed.py should not generate new UUIDs.
    """
    db = SessionLocal()
    client = weaviate.Client("http://localhost:8080")
    
    try:
        pg_chunks = db.query(PolicyChunk.chunk_id, PolicyChunk.chunk_text).limit(5).all()
        
        for pg_chunk_id, pg_text in pg_chunks:
            result = client.query.get(
                "PolicyChunk",
                ["chunk_id", "chunk_text"]
            ).with_where({
                "path": ["chunk_id"],
                "operator": "Equal",
                "valueText": str(pg_chunk_id)
            }).do()
            
            wv_chunks = result.get("data", {}).get("Get", {}).get("PolicyChunk", [])
            
            assert len(wv_chunks) == 1, (
                f"Expected 1 Weaviate object for chunk_id {pg_chunk_id}, found {len(wv_chunks)}"
            )
            
            assert wv_chunks[0]["chunk_id"] == str(pg_chunk_id), (
                f"chunk_id mismatch: PostgreSQL has {pg_chunk_id}, "
                f"Weaviate has {wv_chunks[0]['chunk_id']}"
            )
            
    finally:
        db.close()
