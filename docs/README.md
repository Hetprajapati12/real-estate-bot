# Real Estate RAG Chatbot

An intelligent real estate chatbot for Al Badia Villas using Retrieval-Augmented Generation (RAG) with multimodal capabilities (text + images) and intelligent lead generation.

## Features

- **Accurate Property Information**: Retrieves facts from floorplans PDF with zero hallucinations
- **Multimodal Responses**: Returns relevant floorplan images alongside text responses
- **Intelligent Lead Generation**: Detects buying signals and captures lead information naturally
- **Citation-Based Responses**: Every claim is backed by PDF page references
- **Conversation Continuity**: Session management maintains context across interactions
- **Smart Guardrails**: Never invents pricing or availability - only provides documented facts

## Architecture
```
├── config.py                 # Configuration management
├── app.py                    # FastAPI application
├── ingest_data.py           # Data ingestion script
│
├── ingestion/               # Document processing
│   ├── pdf_processor.py     # PDF extraction and chunking
│   └── image_processor.py   # Image indexing and mapping
│
├── retrieval/               # RAG implementation
│   ├── vector_store.py      # ChromaDB management
│   └── rag.py              # Retrieval and ranking logic
│
├── lead/                    # Lead generation
│   └── detector.py          # Buying signal detection
│
├── services/                # Core services
│   ├── llm.py              # LLM interaction
│   └── chat.py             # Chat orchestration
│
└── utils/                   # Utilities
    ├── logger.py            # Logging configuration
    └── session.py           # Session management
```

## Prerequisites

- Python 3.10+
- OpenAI API key
- Al Badia Villas PDF and images

## Installation

### 1. Clone and Setup Virtual Environment
```bash
# Create project directory
mkdir real-estate-chatbot
cd real-estate-chatbot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Required Configuration:**
```env
OPENAI_API_KEY=your_openai_api_key_here
PDF_PATH=./data/ABVFinalFloorplans.pdf
IMAGES_DIR=./data/WebP
LLM_MODEL=gpt-3.5-turbo
```

### 3. Data Setup

Create the data directory structure:
```bash
mkdir -p data/WebP
```

Place your files:
- `data/ABVFinalFloorplans.pdf` - The floorplans PDF
- `data/WebP/*.webp` - Floorplan images (Rev11 versions)

**Directory structure:**
```
data/
├── ABVFinalFloorplans.pdf
└── WebP/
    ├── AlBadia_Floorplans_A3_Rev11-4.webp
    ├── AlBadia_Floorplans_A3_Rev11-5.webp
    ├── AlBadia_Floorplans_A3_Rev11-6.webp
    ├── AlBadia_Floorplans_A3_Rev11-7.webp
    └── AlBadia_Floorplans_A3_Rev11-8.webp
```

### 4. Data Ingestion

Process the PDF and images into the vector database:
```bash
# First time setup (or to reset)
python ingest_data.py --reset

# Subsequent runs (adds to existing data)
python ingest_data.py
```

**Expected output:**
```
✅ Data ingestion completed successfully!
Vector store location: ./data/chroma_db
```

### 5. Start the Server
```bash
python app.py
```

The API will be available at `http://localhost:8000`

## API Usage

### POST /chat

Send a message and receive an AI response with images and lead insights.

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am looking for a 4-bedroom villa with a pool",
    "session_id": "user-123",
    "context": {
      "previous_properties_viewed": [],
      "lead_status": "new"
    }
  }'
```

**Response:**
```json
{
  "response": "Great choice! Al Badia Villas offers 4-bedroom SHADEA villas with swimming pool options. The 4BR Type B with pool has 344 SQM total built-up area across ground and first floors...",
  "properties_mentioned": ["4BR-SHADEA-TYPE-B"],
  "citations": [
    {
      "source": "floorplans_pdf",
      "page": 7,
      "villa_type": "4BR SHADEA Type B with Pool"
    }
  ],
  "images": [
    {
      "path": "data/WebP/AlBadia_Floorplans_A3_Rev11-7.webp",
      "description": "4BR SHADEA Type B floorplan - Ground and first floor layout with swimming pool",
      "relevance": "floorplan"
    }
  ],
  "lead_signals": {
    "intent": "medium",
    "intent_score": 0.62,
    "signals_detected": ["specific_requirements", "location_preference", "luxury_feature_interest"],
    "recommended_action": "show_floorplans_and_qualify"
  },
  "follow_up_prompt": "I can send you detailed floor plans and arrange a site visit. What's your preferred timeline for moving?"
}
```

### GET /health

Check service health:
```bash
curl "http://localhost:8000/health"
```

## Testing

### Sample Conversations

**Test 1: Property Inquiry**
```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{
  "message": "Tell me about 3-bedroom villas",
  "session_id": "test-001"
}'
```

**Test 2: Specific Requirements**
```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{
  "message": "I need a villa with at least 400 sqm and a swimming pool",
  "session_id": "test-002"
}'
```

**Test 3: High Intent Lead**
```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{
  "message": "I am interested in viewing the 5-bedroom villa this weekend. My budget is around 5 million AED",
  "session_id": "test-003"
}'
```

### Run Test Suite
```bash
pytest tests/test_chat.py -v
```

## Configuration Options

Edit `.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `LLM_MODEL` | GPT model to use | gpt-3.5-turbo |
| `EMBEDDING_MODEL` | Embedding model | text-embedding-3-small |
| `CHUNK_SIZE` | Text chunk size | 1000 |
| `TOP_K_RESULTS` | Results per query | 5 |
| `TEMPERATURE` | LLM creativity | 0.7 |
| `APP_PORT` | Server port | 8000 |

## Logging

Logs are written to:
- **Console**: Real-time output
- **Files**: `logs/app_YYYY-MM-DD.log` (rotated daily, kept for 30 days)

## Troubleshooting

### Vector store not found
```
RuntimeError: Vector store not found. Please run 'python ingest_data.py' first.
```
**Solution:** Run data ingestion: `python ingest_data.py --reset`

### No images in responses
- Verify images are in `data/WebP/` directory
- Ensure filenames match pattern `*Rev11*.webp`
- Check logs for image processing errors

### Import errors
```
ModuleNotFoundError: No module named 'X'
```
**Solution:** Reinstall dependencies: `pip install -r requirements.txt`

### OpenAI API errors
- Verify `OPENAI_API_KEY` in `.env`
- Check API key validity
- Ensure sufficient credits

## Performance Optimization

For production deployment:

1. **Use Redis for sessions** instead of in-memory storage
2. **Enable caching** for frequently accessed chunks
3. **Optimize chunk size** based on your documents (test 500-1500)
4. **Add rate limiting** on `/chat` endpoint
5. **Deploy with Gunicorn** + multiple workers

## Security Considerations

- Never commit `.env` file to version control
- Use environment-specific API keys
- Implement authentication for production
- Add input sanitization
- Enable HTTPS in production

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/chat` | POST | Main chat endpoint |
| `/docs` | GET | Interactive API docs |
| `/admin/cleanup-sessions` | POST | Clean expired sessions |

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Verify data files and configuration
3. Test with sample conversations
4. Review DESIGN.md for architecture details

## License

Proprietary - Al Badia Villas Real Estate
