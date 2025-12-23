import pytest
from sqlalchemy.exc import IntegrityError
from db.session import SessionLocal
from db.models import PolicyChunk
import uuid
from datetime import datetime

def test_duplicate_doc_id_chunk_index_fails():
    """
    Test that inserting duplicate (doc_id, chunk_index) violates UNIQUE constraint.
    This ensures PostgreSQL enforces data integrity.
    """
    db = SessionLocal()
    try:
        chunk1 = PolicyChunk(
            chunk_id=str(uuid.uuid4()),
            doc_id="test_doc_2025-12-22",
            chunk_index=0,
            chunk_text="Test chunk",
            policy_source="google",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path="Test > Section",
            region="GLOBAL",
            content_type="GENERAL",
            doc_url="https://test.com"
        )
        db.add(chunk1)
        db.commit()
        
        chunk2 = PolicyChunk(
            chunk_id=str(uuid.uuid4()),
            doc_id="test_doc_2025-12-22",
            chunk_index=0,
            chunk_text="Different text",
            policy_source="google",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path="Test > Section",
            region="GLOBAL",
            content_type="GENERAL",
            doc_url="https://test.com"
        )
        db.add(chunk2)
        
        with pytest.raises(IntegrityError):
            db.commit()
        
    finally:
        db.rollback()
        db.query(PolicyChunk).filter_by(doc_id="test_doc_2025-12-22").delete()
        db.commit()
        db.close()

def test_uuid_primary_key_enforced():
    """
    Test that chunk_id is a valid UUID and serves as primary key.
    """
    db = SessionLocal()
    try:
        valid_uuid = str(uuid.uuid4())
        chunk = PolicyChunk(
            chunk_id=valid_uuid,
            doc_id="test_uuid_2025-12-22",
            chunk_index=0,
            chunk_text="Test chunk",
            policy_source="google",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path="Test > Section",
            region="GLOBAL",
            content_type="GENERAL",
            doc_url="https://test.com"
        )
        db.add(chunk)
        db.commit()
        
        retrieved = db.query(PolicyChunk).filter_by(chunk_id=valid_uuid).first()
        assert retrieved is not None
        assert str(retrieved.chunk_id) == valid_uuid
        
    finally:
        db.query(PolicyChunk).filter_by(doc_id="test_uuid_2025-12-22").delete()
        db.commit()
        db.close()

def test_duplicate_chunk_id_fails():
    """
    Test that duplicate chunk_id (primary key) fails.
    """
    db = SessionLocal()
    try:
        same_uuid = str(uuid.uuid4())
        
        chunk1 = PolicyChunk(
            chunk_id=same_uuid,
            doc_id="test_pk1_2025-12-22",
            chunk_index=0,
            chunk_text="Test chunk 1",
            policy_source="google",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path="Test > Section",
            region="GLOBAL",
            content_type="GENERAL",
            doc_url="https://test.com"
        )
        db.add(chunk1)
        db.commit()
        
        chunk2 = PolicyChunk(
            chunk_id=same_uuid,
            doc_id="test_pk2_2025-12-22",
            chunk_index=0,
            chunk_text="Test chunk 2",
            policy_source="google",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path="Test > Section",
            region="GLOBAL",
            content_type="GENERAL",
            doc_url="https://test.com"
        )
        db.add(chunk2)
        
        with pytest.raises(IntegrityError):
            db.commit()
        
    finally:
        db.rollback()
        db.query(PolicyChunk).filter(
            PolicyChunk.doc_id.in_(["test_pk1_2025-12-22", "test_pk2_2025-12-22"])
        ).delete(synchronize_session=False)
        db.commit()
        db.close()
