import pytest
from sqlalchemy.exc import IntegrityError
from db.session import SessionLocal
from db.models import PolicyChunk
import uuid

def test_chunk_text_not_null():
    """
    Test that chunk_text cannot be NULL.
    This ensures PostgreSQL is the canonical source of chunk text.
    """
    db = SessionLocal()
    try:
        chunk = PolicyChunk(
            chunk_id=str(uuid.uuid4()),
            doc_id="test_null_text_2025-12-22",
            chunk_index=0,
            chunk_text=None,
            policy_source="google",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path="Test > Section",
            region="GLOBAL",
            content_type="GENERAL",
            doc_url="https://test.com"
        )
        db.add(chunk)
        
        with pytest.raises(IntegrityError):
            db.commit()
        
    finally:
        db.rollback()
        db.close()

def test_policy_path_not_null():
    """
    Test that policy_path cannot be NULL.
    This ensures hierarchical citations are always available.
    """
    db = SessionLocal()
    try:
        chunk = PolicyChunk(
            chunk_id=str(uuid.uuid4()),
            doc_id="test_null_path_2025-12-22",
            chunk_index=0,
            chunk_text="Test chunk",
            policy_source="google",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path=None,
            region="GLOBAL",
            content_type="GENERAL",
            doc_url="https://test.com"
        )
        db.add(chunk)
        
        with pytest.raises(IntegrityError):
            db.commit()
        
    finally:
        db.rollback()
        db.close()

def test_policy_source_enum_enforced():
    """
    Test that policy_source only accepts valid enum values.
    """
    db = SessionLocal()
    try:
        chunk = PolicyChunk(
            chunk_id=str(uuid.uuid4()),
            doc_id="test_invalid_source_2025-12-22",
            chunk_index=0,
            chunk_text="Test chunk",
            policy_source="invalid_platform",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path="Test > Section",
            region="GLOBAL",
            content_type="GENERAL",
            doc_url="https://test.com"
        )
        db.add(chunk)
        
        from sqlalchemy.exc import DataError
        with pytest.raises((IntegrityError, ValueError, DataError)):
            db.commit()
        
    finally:
        db.rollback()
        db.close()

def test_region_enum_enforced():
    """
    Test that region only accepts valid enum values.
    """
    db = SessionLocal()
    try:
        chunk = PolicyChunk(
            chunk_id=str(uuid.uuid4()),
            doc_id="test_invalid_region_2025-12-22",
            chunk_index=0,
            chunk_text="Test chunk",
            policy_source="google",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path="Test > Section",
            region="INVALID_REGION",
            content_type="GENERAL",
            doc_url="https://test.com"
        )
        db.add(chunk)
        
        from sqlalchemy.exc import DataError
        with pytest.raises((IntegrityError, ValueError, DataError)):
            db.commit()
        
    finally:
        db.rollback()
        db.close()

def test_content_type_enum_enforced():
    """
    Test that content_type only accepts valid enum values.
    """
    db = SessionLocal()
    try:
        chunk = PolicyChunk(
            chunk_id=str(uuid.uuid4()),
            doc_id="test_invalid_content_type_2025-12-22",
            chunk_index=0,
            chunk_text="Test chunk",
            policy_source="google",
            policy_section="Test Section",
            policy_section_level="H2",
            policy_path="Test > Section",
            region="GLOBAL",
            content_type="INVALID_TYPE",
            doc_url="https://test.com"
        )
        db.add(chunk)
        
        from sqlalchemy.exc import DataError
        with pytest.raises((IntegrityError, ValueError, DataError)):
            db.commit()
        
    finally:
        db.rollback()
        db.close()
