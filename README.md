# Policy-Aware RAG System for Ads & Content Moderation Guidance

A customer-facing Retrieval-Augmented Generation (RAG) system that provides policy explanation and guidance for Google Ads content moderation. The system uses hybrid retrieval (semantic + SQL) to find relevant policy sections and generates grounded, citation-backed explanations.

## Core Features

- Hybrid retrieval: Vector similarity search (Weaviate) + SQL metadata filtering (PostgreSQL)
- Grounded generation: LLM responses cite source policies
- Refusal handling: System explicitly refuses when no policy applies
- Structured filtering: Filter by region, content type, policy section

## Technology Stack

### Data & Storage

- PostgreSQL: Structured metadata (region, content type, policy source)
- Weaviate: Vector database for semantic search
- SQLAlchemy: ORM for database interactions

### ML & RAG

- SentenceTransformers (all-MiniLM-L6-v2): Text embeddings
- Llama-3 8B Instruct (Q4): Local LLM for generation
- LangChain: RAG orchestration

### API & Deployment

- FastAPI: REST API endpoint
- Pydantic: Request/response validation
- Docker: Containerization
- AWS Lambda + API Gateway: Serverless deployment

## Project Structure

```
data/
├── raw_docs/          - Downloaded policy documents (HTML, Markdown, JSON metadata)
├── processed_chunks/  - Chunked policy text
└── metadata/          - Metadata seed files

ingestion/
├── load_docs.py       - Policy document downloader
├── chunk.py           - Chunking logic with structure preservation
└── embed.py           - Embedding generation and vector ingest

db/
├── models.py          - SQLAlchemy ORM models
├── session.py         - Database connection management
└── init.py            - Database initialization script

app/
├── main.py            - FastAPI application
├── schemas.py         - Pydantic request/response models
├── retrieval.py       - Hybrid retrieval implementation
├── generation.py      - LLM prompt construction and generation
└── citations.py       - Citation formatting

tests/
├── test_retrieval.py  - Retrieval correctness tests
├── test_sql_filters.py - Metadata filtering tests
├── test_grounding.py  - Citation validation tests
├── test_refusal.py    - Refusal behavior tests
└── test_api.py        - API endpoint tests

docker/
└── Dockerfile         - Container definition
```

## Setup Instructions

### 1. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. PostgreSQL Setup

```bash
# Install PostgreSQL (macOS)
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Create database
createdb ads_policy_rag

# Initialize schema
python -m db.init
```

### 3. Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://your_username@localhost:5432/ads_policy_rag
WEAVIATE_URL=http://localhost:8080
LLAMA_MODEL_PATH=./models/llama-3-8b-instruct.Q4_K_M.gguf
```

Replace `your_username` with your system username (run `whoami` to check).

## Implementation Steps

### Step 1: Data Collection (COMPLETED)

Download and structure policy documents from Google Ads.

**What we built:**

- `ingestion/load_docs.py`: Web scraper with structure preservation
- Extracted 5 Google Ads policy documents
- Preserved HTML hierarchy (headers, bullets, sections)
- Generated metadata (doc_id, platform, category, title, sections)

**Key concepts:**

- BeautifulSoup for HTML parsing
- Structure preservation for better chunking
- Metadata extraction for hybrid retrieval

**Output:**

- `.md` files: Structured policy text with section markers
- `_metadata.json`: Document metadata including section hierarchy
- `_raw.html`: Original HTML for reference

**Commands:**

```bash
python ingestion/load_docs.py
```

**Files created:**

```
data/raw_docs/
├── google_ads_base_hub.md
├── google_ads_base_hub_metadata.json
├── google_ads_misrepresentation.md
├── google_ads_misrepresentation_metadata.json
├── google_ads_restricted_products.md
├── google_ads_restricted_products_metadata.json
├── google_ads_prohibited_content.md
├── google_ads_prohibited_content_metadata.json
├── google_ads_editorial_technical.md
└── google_ads_editorial_technical_metadata.json
```

### Step 2: Metadata Design & PostgreSQL Schema (COMPLETED)

Define structured metadata schema and create PostgreSQL database.

**What we built:**

- `db/models.py`: SQLAlchemy ORM models with enums
- `db/session.py`: Database connection and session management
- `db/init.py`: Schema initialization script

**Schema design:**

```python
PolicyChunk:
  - chunk_id (UUID, primary key)
  - doc_id (string, indexed)
  - chunk_index (integer)
  - policy_source (enum: google)
  - policy_section (string, indexed)
  - region (enum: global, us, eu, uk)
  - content_type (enum: ad_text, image, video, landing_page, general)
  - effective_date (datetime, nullable)
  - doc_url (string)
  - created_at (datetime)
```

**Note:** `chunk_text` is stored in Weaviate (vector DB), not PostgreSQL. This maintains clean separation:
- PostgreSQL: Metadata and filtering constraints
- Weaviate: Text content and embeddings
- Join on `chunk_id` during retrieval

**Key concepts:**

- Enums for type safety (PolicySource, Region, ContentType)
- Indexes on filterable columns for query performance
- UUID for globally unique identifiers
- Nullable effective_date for version tracking

**Why hybrid retrieval:**

1. Vector search finds semantically similar chunks
2. SQL filters by region, content_type, policy_source
3. Combined: relevant + correctly filtered results

**Commands:**

```bash
# Create database
createdb ads_policy_rag

# Initialize schema
python -m db.init

# Verify table creation
psql ads_policy_rag -c "\d policy_chunks"
```

### Step 3: Chunking (TODO)

Split policy documents into semantically coherent chunks.

### Step 4: Embeddings & Vector Ingest (TODO)

Generate embeddings and store in Weaviate.

### Step 5: Hybrid Retrieval Logic (TODO)

Implement vector search + SQL filtering.

### Step 6: Generation Layer (TODO)

Build LLM prompts with grounding and citations.

### Step 7: API Layer (TODO)

Create FastAPI endpoint with validation.

### Step 8: Testing (TODO)

Implement comprehensive test suite.

### Step 9: Dockerization (TODO)

Package system in container.

### Step 10: README & Documentation (TODO)

Final documentation and example queries.

## Development Notes

### Database Schema Inspection

```bash
# List all tables
psql ads_policy_rag -c "\dt"

# Describe policy_chunks table
psql ads_policy_rag -c "\d policy_chunks"

# View enum types
psql ads_policy_rag -c "\dT+"
```

### Virtual Environment

```bash
# Activate (already active if in same session)
source venv/bin/activate

# Deactivate
deactivate
```

## Architecture Decisions

### Why PostgreSQL?

- ACID compliance for data integrity
- Complex filtering with multiple conditions
- Excellent JSON support for flexible metadata
- Industry standard, proven at scale

### Why Weaviate?

- Purpose-built for vector similarity search
- Fast approximate nearest neighbor search
- Scales to millions of vectors
- Production-ready with monitoring

### Why Hybrid Retrieval?

- Vector search alone: May return wrong region/type
- SQL search alone: Can't understand semantic meaning
- Hybrid: Best of both worlds

### Why Local LLM (Llama-3)?

- No API costs
- Data privacy (no external calls)
- Deterministic behavior
- Fast inference on M3 Mac

## License

MIT
