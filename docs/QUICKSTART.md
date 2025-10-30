# Quick Start Guide

Get the Real Estate RAG Chatbot running in 5 minutes.

## Prerequisites

- Python 3.10+
- OpenAI API key
- PDF and image files

## Setup (3 steps)

### 1. Automated Setup
```bash
# Make setup script executable (Linux/Mac)
chmod +x setup.sh

# Run setup
./setup.sh
```

Or manually:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create package structure
touch ingestion/__init__.py retrieval/__init__.py lead/__init__.py \
      services/__init__.py utils/__init__.py tests/__init__.py

# Create directories
mkdir -p data/WebP logs
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit and add your OpenAI API key
nano .env
```

**Required settings:**
```env
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-3.5-turbo
```

### 3. Add Data Files
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

## Run (2 steps)

### 1. Ingest Data
```bash
python ingest_data.py --reset
```

**Expected output:**
```
Data ingestion completed successfully!
Vector store location: ./data/chroma_db
```

### 2. Start Server
```bash
python app.py
```

Server starts at: `http://localhost:8000`

---

## Test

### Using curl:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me 4-bedroom villas with pool",
    "session_id": "test-123"
  }'
```

### Using Python:
```python
import requests

response = requests.post("http://localhost:8000/chat", json={
    "message": "Tell me about Al Badia Villas",
    "session_id": "user-001"
})

print(response.json())
```

### Using Browser:

Go to: `http://localhost:8000/docs`

Click "Try it out" on POST /chat endpoint.

### Using tests:
```bash
pytest tests/test_chat.py -v
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send message, get AI response |
| `/health` | GET | Check service health |
| `/docs` | GET | Interactive API docs |
| `/` | GET | API information |

---

## Sample Request/Response

**Request:**
```json
{
  "message": "I need a 4BR villa with pool",
  "session_id": "user-123"
}
```

**Response:**
```json
{
  "response": "Great choice! Al Badia Villas offers 4BR SHADEA Type B with swimming pool...",
  "properties_mentioned": ["4BR-SHADEA-TYPE-B"],
  "citations": [{"source": "floorplans_pdf", "page": 7}],
  "images": [{
    "path": "data/WebP/AlBadia_Floorplans_A3_Rev11-7.webp",
    "description": "4BR SHADEA Type B with pool",
    "relevance": "floorplan"
  }],
  "lead_signals": {
    "intent": "medium",
    "signals_detected": ["specific_requirements", "luxury_feature_interest"]
  },
  "follow_up_prompt": "I can send you detailed floor plans..."
}
```

---

## Common Issues

### "Vector store not found"
```bash
# Run ingestion first
python ingest_data.py --reset
```

### "OpenAI API key not set"
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY
```

### "No module named 'X'"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "No images in response"
```bash
# Verify images exist
ls -la data/WebP/*Rev11*.webp
```

### "Embeddings mismatch / 0 results"
```bash
# Delete vector store and re-ingest
rmdir /s /q data\chroma_db  # Windows
rm -rf data/chroma_db       # Linux/Mac

python ingest_data.py --reset
```

---

## Next Steps

- **Production deployment**: See README.md
- **Architecture details**: See DESIGN.md
- **File structure**: See PROJECT_STRUCTURE.md
- **API documentation**: Visit `/docs` when server is running

---

## Development Workflow
```bash
# Activate venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Make changes to code

# Run tests
pytest tests/test_chat.py -v

# Restart server (if running)
# Ctrl+C to stop, then:
python app.py
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | OpenAI API key |
| `LLM_MODEL` | gpt-3.5-turbo | GPT model |
| `EMBEDDING_MODEL` | text-embedding-3-small | Embedding model |
| `APP_PORT` | 8000 | Server port |
| `CHUNK_SIZE` | 1000 | Text chunk size |
| `TOP_K_RESULTS` | 5 | Retrieval results |
| `TEMPERATURE` | 0.7 | LLM creativity |

---

## Project Structure (Minimal View)
```
.
├── app.py                # Start server
├── ingest_data.py        # Process data
├── config.py             # Configuration
├── requirements.txt      # Dependencies
├── .env                  # Your settings
│
├── data/                 # Your data files
├── ingestion/            # PDF & image processing
├── retrieval/            # RAG implementation
├── lead/                 # Lead detection
├── services/             # LLM & chat
├── utils/                # Helpers
└── tests/                # Test suite
```

---

## Cost Estimation

### Using GPT-3.5-turbo:

**Per Query:**
- Embeddings: ~$0.00002
- LLM Generation: ~$0.001-0.002
- **Total: ~$0.001-0.002 per query**

**With $5 credit:**
- ~2,500-5,000 queries
- Perfect for testing and small deployments

### Using Free HuggingFace Embeddings:

**Per Query:**
- Embeddings: $0 (free, local)
- LLM Generation: ~$0.001-0.002
- **Total: ~$0.001-0.002 per query**

**Ingestion (one-time):**
- Text embeddings: ~$0.0005 (or free with HuggingFace)
- Total ingestion: < $0.001

---

## Quick Demo

**In your browser, go to:** `http://localhost:8000/docs`

**Try this test:**

1. Expand **POST /chat**
2. Click **Try it out**
3. Paste:
```json
{
  "message": "I'm looking for a luxury villa with 4 bedrooms and a pool. My budget is around 5 million AED and I need to move by next month. Can you show me options?",
  "session_id": "demo-001"
}
```
4. Click **Execute**
5. See the magic!

You'll get:
- Detailed villa information
- Floorplan images
- PDF citations
- High intent score (0.8+)
- Recommended action: "schedule_viewing_immediately"

---

## Troubleshooting Tips

### Server won't start
```bash
# Check if port 8000 is already in use
# Windows:
netstat -ano | findstr :8000
# Linux/Mac:
lsof -i :8000

# Use different port
# Edit .env:
APP_PORT=8001
```

### Slow responses
```bash
# Using GPT-4? Switch to GPT-3.5 for faster responses
# Edit .env:
LLM_MODEL=gpt-3.5-turbo
```

### Out of OpenAI credits
```bash
# Option 1: Add credits at https://platform.openai.com/account/billing
# Option 2: Use free HuggingFace embeddings (see DESIGN.md)
```

---

## Support

- Check logs: `tail -f logs/app_*.log`
- Test health: `curl http://localhost:8000/health`
- View docs: `http://localhost:8000/docs`

---

## Ready in 3 Commands
```bash
# 1. Setup
pip install -r requirements.txt && cp .env.example .env
# (Edit .env to add API key)

# 2. Ingest
python ingest_data.py --reset

# 3. Run
python app.py
```

Then visit: **http://localhost:8000/docs** 

---

## What You've Built

**RAG System** with ChromaDB  
**Multimodal AI** (text + images)  
**Lead Detection** with 9 signal types  
**Zero Hallucinations** (citation-based)  
**Session Management**  
**RESTful API** with FastAPI  
**Production-Ready Code**  

---

**Need help?** Check README.md for detailed documentation or DESIGN.md for architecture details.

**Ready to deploy?** See README.md "Performance Optimization" section for production deployment guidelines.