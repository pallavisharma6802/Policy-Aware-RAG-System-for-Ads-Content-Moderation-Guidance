import pytest
import subprocess
import sys
from sqlalchemy import func
from db.session import SessionLocal
from db.models import PolicyChunk

def test_idempotent_ingestion():
    """
    Test that running load_to_db.py twice does not increase row count.
    This validates the idempotent loading fix.
    """
    db = SessionLocal()
    try:
        initial_count = db.query(func.count(PolicyChunk.chunk_id)).scalar()
        
        result = subprocess.run(
            [sys.executable, "ingestion/load_to_db.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"load_to_db.py failed: {result.stderr}"
        
        final_count = db.query(func.count(PolicyChunk.chunk_id)).scalar()
        
        assert final_count == initial_count, (
            f"Idempotent check failed: count changed from {initial_count} to {final_count}. "
            f"Running load_to_db.py should not create duplicates."
        )
        
    finally:
        db.close()

def test_no_duplicate_chunks_exist():
    """
    Test that no duplicate (doc_id, chunk_index) combinations exist in database.
    """
    db = SessionLocal()
    try:
        duplicates = db.query(
            PolicyChunk.doc_id,
            PolicyChunk.chunk_index,
            func.count(PolicyChunk.chunk_id).label('count')
        ).group_by(
            PolicyChunk.doc_id,
            PolicyChunk.chunk_index
        ).having(
            func.count(PolicyChunk.chunk_id) > 1
        ).all()
        
        assert len(duplicates) == 0, (
            f"Found {len(duplicates)} duplicate (doc_id, chunk_index) combinations: {duplicates}"
        )
        
    finally:
        db.close()
