import json
from pathlib import Path
from sqlalchemy.orm import Session
import sys

sys.path.append(str(Path(__file__).parent.parent))

from db.session import SessionLocal
from db.models import PolicyChunk, PolicySource

def load_chunks_to_db():
    db = SessionLocal()
    
    try:
        chunks_dir = Path(__file__).parent.parent / "data" / "processed_chunks"
        chunk_files = list(chunks_dir.glob("*_chunks.json"))
        
        if not chunk_files:
            print("No chunk files found")
            return
        
        print(f"Found {len(chunk_files)} chunk files")
        
        total_loaded = 0
        
        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            print(f"\nLoading {chunk_file.name}: {len(chunks)} chunks")
            
            for chunk_data in chunks:
                exists = db.query(PolicyChunk).filter_by(
                    doc_id=chunk_data["doc_id"],
                    chunk_index=chunk_data["chunk_index"]
                ).first()
                
                if exists:
                    continue
                
                chunk = PolicyChunk(
                    chunk_id=chunk_data['chunk_id'],
                    doc_id=chunk_data['doc_id'],
                    chunk_index=chunk_data['chunk_index'],
                    chunk_text=chunk_data['chunk_text'],
                    policy_source=PolicySource.GOOGLE,
                    policy_section=chunk_data['policy_section'],
                    policy_section_level=chunk_data['policy_section_level'],
                    policy_path=chunk_data['policy_path'],
                    doc_url=chunk_data['doc_url']
                )
                db.add(chunk)
            
            total_loaded += len(chunks)
        
        db.commit()
        print(f"\nTotal chunks loaded: {total_loaded}")
        
        count = db.query(PolicyChunk).count()
        print(f"Chunks in database: {count}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    load_chunks_to_db()
