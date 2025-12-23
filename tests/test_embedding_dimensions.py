import pytest
import weaviate
from sentence_transformers import SentenceTransformer

def test_embedding_dimensions():
    """
    Test that all vectors in Weaviate have the expected dimension (384 for all-MiniLM-L6-v2).
    """
    client = weaviate.Client("http://localhost:8080")
    
    result = client.query.get(
        "PolicyChunk",
        ["chunk_id", "_additional { vector }"]
    ).with_limit(100).do()
    
    chunks = result.get("data", {}).get("Get", {}).get("PolicyChunk", [])
    
    assert len(chunks) > 0, "No chunks found in Weaviate"
    
    for chunk in chunks:
        vector = chunk["_additional"]["vector"]
        assert len(vector) == 384, (
            f"Chunk {chunk['chunk_id']} has vector dimension {len(vector)}, expected 384"
        )

def test_model_dimension_matches():
    """
    Test that the embedding model produces vectors of expected dimension.
    """
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    test_text = "This is a test sentence for dimension verification."
    embedding = model.encode(test_text)
    
    assert len(embedding) == 384, (
        f"Model produced embedding of dimension {len(embedding)}, expected 384"
    )
