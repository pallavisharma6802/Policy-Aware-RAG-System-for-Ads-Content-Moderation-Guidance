import pytest
import weaviate
from sqlalchemy import func
from db.session import SessionLocal
from db.models import PolicyChunk

def test_embedding_coverage():
    """
    Test that every PostgreSQL chunk has exactly one vector in Weaviate.
    """
    db = SessionLocal()
    client = weaviate.Client("http://localhost:8080")
    
    try:
        pg_count = db.query(func.count(PolicyChunk.chunk_id)).scalar()
        
        result = client.query.aggregate("PolicyChunk").with_meta_count().do()
        wv_count = result['data']['Aggregate']['PolicyChunk'][0]['meta']['count']
        
        assert pg_count == wv_count, (
            f"Embedding coverage mismatch: PostgreSQL has {pg_count} chunks, "
            f"Weaviate has {wv_count} vectors"
        )
        
    finally:
        db.close()

def test_no_missing_embeddings():
    """
    Test that no chunks are missing embeddings.
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
        
        missing_embeddings = pg_chunk_ids - wv_chunk_ids
        
        assert len(missing_embeddings) == 0, (
            f"{len(missing_embeddings)} chunks missing embeddings: {list(missing_embeddings)[:10]}"
        )
        
    finally:
        db.close()

def test_no_duplicate_vectors():
    """
    Test that no chunk has multiple vectors in Weaviate.
    """
    client = weaviate.Client("http://localhost:8080")
    
    result = client.query.aggregate("PolicyChunk").with_meta_count().do()
    wv_count = result['data']['Aggregate']['PolicyChunk'][0]['meta']['count']
    
    result = client.query.get("PolicyChunk", ["chunk_id"]).with_limit(wv_count).do()
    wv_chunks = result.get("data", {}).get("Get", {}).get("PolicyChunk", [])
    
    chunk_id_counts = {}
    for chunk in wv_chunks:
        chunk_id = chunk["chunk_id"]
        chunk_id_counts[chunk_id] = chunk_id_counts.get(chunk_id, 0) + 1
    
    duplicates = {cid: count for cid, count in chunk_id_counts.items() if count > 1}
    
    assert len(duplicates) == 0, (
        f"Found {len(duplicates)} chunks with duplicate vectors: {duplicates}"
    )
