# Project Structure

Complete directory structure for the Real Estate RAG Chatbot project.
```
real-estate-chatbot/
│
├── .env                          # Environment variables (create from .env.example)
├── .env.example                  # Example environment configuration
├── .gitignore                    # Git ignore file
├── requirements.txt              # Python dependencies
├── README.md                     # Setup and usage guide
├── DESIGN.md                     # Architecture documentation
├── PROJECT_STRUCTURE.md          # This file
├── QUICKSTART.md                 # Quick start guide
│
├── config.py                     # Configuration management
├── app.py                        # FastAPI application (main entry point)
├── ingest_data.py               # Data ingestion script
│
├── data/                         # Data directory
│   ├── ABVFinalFloorplans.pdf   # Floorplans PDF (not in repo)
│   ├── WebP/                     # Floorplan images (not in repo)
│   │   ├── AlBadia_Floorplans_A3_Rev11-4.webp
│   │   ├── AlBadia_Floorplans_A3_Rev11-5.webp
│   │   ├── AlBadia_Floorplans_A3_Rev11-6.webp
│   │   ├── AlBadia_Floorplans_A3_Rev11-7.webp
│   │   └── AlBadia_Floorplans_A3_Rev11-8.webp
│   └── chroma_db/                # Vector store (created by ingestion)
│
├── logs/                         # Application logs (auto-created)
│   └── app_YYYY-MM-DD.log
│
├── ingestion/                    # Document processing
│   ├── __init__.py
│   ├── pdf_processor.py          # PDF extraction and chunking
│   └── image_processor.py        # Image indexing and mapping
│
├── retrieval/                    # RAG implementation
│   ├── __init__.py
│   ├── vector_store.py           # ChromaDB management
│   └── rag.py                    # Retrieval and ranking logic
│
├── lead/                         # Lead generation
│   ├── __init__.py
│   └── detector.py               # Buying signal detection and scoring
│
├── services/                     # Core services
│   ├── __init__.py
│   ├── llm.py                    # LLM interaction (OpenAI)
│   └── chat.py                   # Chat orchestration
│
├── utils/                        # Utilities
│   ├── __init__.py
│   ├── logger.py                 # Logging configuration
│   └── session.py                # Session management
│
└── tests/                        # Test suite
    ├── __init__.py
    └── test_chat.py              # Comprehensive API tests
```

## File Descriptions

### Root Level

- **`.env`**: Environment variables (API keys, paths, config)
- **`config.py`**: Centralized configuration using Pydantic Settings
- **`app.py`**: FastAPI application with `/chat` endpoint
- **`ingest_data.py`**: Script to process PDF and images into vector store

### Ingestion Module

- **`pdf_processor.py`**: 
  - Extract text from PDF
  - Identify villa types on pages
  - Create chunks with metadata
  - Functions: `extract_pdf_pages()`, `create_chunks_with_metadata()`

- **`image_processor.py`**:
  - Index floorplan images
  - Map images to villa types
  - Generate searchable descriptions
  - Functions: `get_image_files()`, `map_images_to_villa_types()`

### Retrieval Module

- **`vector_store.py`**:
  - ChromaDB initialization and management
  - Document addition and search
  - Filtered retrieval (PDF vs images)
  - Functions: `initialize_vector_store()`, `search_vectorstore()`

- **`rag.py`**:
  - Dual retrieval (text + images)
  - Context formatting for LLM
  - Citation extraction
  - Image ranking
  - Functions: `retrieve_context()`, `rank_images_by_relevance()`

### Lead Module

- **`detector.py`**:
  - 9 types of buying signal detection
  - Intent score calculation
  - Action recommendations
  - Contact info extraction
  - Functions: `detect_buying_signals()`, `calculate_intent_score()`

### Services Module

- **`llm.py`**:
  - OpenAI client initialization
  - Prompt engineering
  - Response generation
  - Follow-up prompt creation
  - Functions: `generate_response()`, `build_system_prompt()`

- **`chat.py`**:
  - Orchestrates complete chat flow
  - Combines RAG + lead detection + LLM
  - Response assembly
  - Main function: `process_chat_message()`

### Utils Module

- **`logger.py`**:
  - Loguru configuration
  - Console and file logging
  - Log rotation

- **`session.py`**:
  - In-memory session storage
  - Conversation history
  - Lead info tracking
  - Functions: `get_session()`, `add_message()`

### Tests Module

- **`test_chat.py`**:
  - API endpoint tests
  - RAG accuracy tests
  - Multimodal response tests
  - Lead generation tests
  - Guardrail tests
  - Run with: `pytest tests/test_chat.py -v`

## Data Flow Through Modules
```
User Request → app.py (FastAPI)
              ↓
        services/chat.py (orchestration)
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
retrieval/rag.py    lead/detector.py
    ↓                   ↓
retrieval/          utils/session.py
vector_store.py         
    ↓                   
services/llm.py (generate response)
    ↓
Response Assembly & Return
```

## Setup Sequence

1. Install dependencies: `pip install -r requirements.txt`
2. Configure: Copy `.env.example` to `.env` and add API keys
3. Add data files to `data/` directory
4. Run ingestion: `python ingest_data.py --reset`
5. Start server: `python app.py`
6. Run tests: `pytest tests/test_chat.py -v`

## Module Dependencies
```
app.py
├── config.py
├── retrieval/vector_store.py
├── services/chat.py
│   ├── retrieval/rag.py
│   │   └── retrieval/vector_store.py
│   ├── lead/detector.py
│   ├── services/llm.py
│   │   └── config.py
│   └── utils/session.py
└── utils/logger.py

ingest_data.py
├── config.py
├── ingestion/pdf_processor.py
├── ingestion/image_processor.py
├── retrieval/vector_store.py
└── utils/logger.py
```

## Key Design Principles

1. **Functional Programming**: All modules use pure functions, no classes
2. **Single Responsibility**: Each module has one clear purpose
3. **Dependency Injection**: Functions receive dependencies as parameters
4. **Configuration-Driven**: All settings in `config.py`
5. **Logging Everywhere**: Every module logs important actions
6. **Type Hints**: All functions have proper type annotations

## Files NOT in Repository

The following should be in `.gitignore`:
```
.env
data/ABVFinalFloorplans.pdf
data/WebP/*.webp
data/chroma_db/
logs/
__pycache__/
*.pyc
.pytest_cache/
venv/
.DS_Store
```

## Production Considerations

For production deployment, modify:

1. **`utils/session.py`**: Replace dict with Redis
2. **`config.py`**: Add database URLs, Redis config
3. **`app.py`**: Add authentication, rate limiting
4. **Deploy**: Use Gunicorn with multiple workers
5. **Monitoring**: Add Prometheus metrics

## Getting Help

- **Setup issues**: See README.md
- **Architecture questions**: See DESIGN.md
- **API usage**: See `/docs` endpoint (Swagger UI)
- **Testing**: See `tests/test_chat.py`