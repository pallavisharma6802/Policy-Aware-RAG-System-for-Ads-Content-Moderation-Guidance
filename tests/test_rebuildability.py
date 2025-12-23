import pytest
import subprocess
import sys
import weaviate
from sqlalchemy import func
from db.session import SessionLocal
from db.models import PolicyChunk
from sentence_transformers import SentenceTransformer

def test_rebuildability():
    """
    Test that Weaviate index can be deleted and rebuilt from PostgreSQL.
    This validates that PostgreSQL is the canonical source.
    """
    db = SessionLocal()
    client = weaviate.Client("http://localhost:8080")
    
    try:
        pg_count_before = db.query(func.count(PolicyChunk.chunk_id)).scalar()
        assert pg_count_before > 0, "PostgreSQL must have chunks for this test"
        
        print(f"PostgreSQL chunks before deletion: {pg_count_before}")
        
        try:
            client.schema.delete_class("PolicyChunk")
            print("Weaviate schema deleted")
        except Exception as e:
            print(f"Schema deletion (expected if already deleted): {e}")
        
        result = subprocess.run(
            [sys.executable, "ingestion/embed.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"embed.py failed: {result.stderr}"
        print("Embedding pipeline re-run complete")
        
        result = client.query.aggregate("PolicyChunk").with_meta_count().do()
        wv_count_after = result['data']['Aggregate']['PolicyChunk'][0]['meta']['count']
        
        pg_count_after = db.query(func.count(PolicyChunk.chunk_id)).scalar()
        
        assert pg_count_before == pg_count_after, (
            f"PostgreSQL count changed during rebuild: {pg_count_before} -> {pg_count_after}"
        )
        
        assert wv_count_after == pg_count_after, (
            f"Rebuild failed: PostgreSQL has {pg_count_after} chunks, "
            f"Weaviate has {wv_count_after} vectors"
        )
        
        print(f"Rebuild successful: {wv_count_after} vectors restored")
        
    finally:
        db.close()

def test_retrieval_after_rebuild():
    """
    Test that semantic search still works after rebuilding Weaviate.
    """
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    client = weaviate.Client("http://localhost:8080")
    
    query = "Can I advertise alcohol?"
    query_vector = model.encode(query).tolist()
    
    result = client.query.get(
        "PolicyChunk",
        ["chunk_id", "policy_section", "policy_path"]
    ).with_near_vector({"vector": query_vector}).with_limit(1).do()
    
    chunks = result.get("data", {}).get("Get", {}).get("PolicyChunk", [])
    
    assert len(chunks) > 0, "Semantic search returned no results after rebuild"
    
    chunk = chunks[0]
    assert "alcohol" in chunk["policy_section"].lower() or "alcohol" in chunk["policy_path"].lower(), (
        f"Retrieved section '{chunk['policy_section']}' does not match query about alcohol"
    )
    
    print(f"Retrieval test passed: Retrieved '{chunk['policy_path']}'")
