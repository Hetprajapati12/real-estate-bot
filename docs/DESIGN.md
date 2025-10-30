# Architecture & Design Document

## System Overview

The Real Estate RAG Chatbot is a production-grade, multimodal conversational AI system designed for real estate lead generation. It combines Retrieval-Augmented Generation (RAG) with intelligent lead scoring to provide accurate property information while naturally capturing and qualifying leads.

## Core Design Principles

1. **Zero Hallucinations**: Every factual claim must be grounded in the PDF document
2. **Multimodal First**: Images are core to the experience, not an afterthought
3. **Lead-Centric**: Every interaction is an opportunity for qualification
4. **Best Practices**: Professional, scalable, maintainable code
5. **Functional Design**: Stateless functions over classes for simplicity and testability

## Architecture Components

### 1. Data Ingestion Pipeline

**Purpose**: Transform unstructured data (PDF + images) into searchable vector embeddings.

#### PDF Processing Strategy

**Approach**: Page-level chunking with metadata preservation
```python
Page → Text Extraction → Chunking → Embedding → Vector Store
```

**Key Decisions:**

- **Chunk Size: 1000 characters** with 200-character overlap
  - *Rationale*: Balances context completeness with retrieval precision. Villa specifications typically span 300-800 characters.
  
- **Page-level metadata**: Every chunk retains its source page number
  - *Rationale*: Enables accurate citations and villa-to-page mapping

- **Sentence boundary chunking**: Breaks at periods/newlines when possible
  - *Rationale*: Preserves semantic coherence of property descriptions

#### Image Processing Strategy

**Approach**: Metadata-based retrieval with page number mapping
```python
Image → Page Number Extraction → Description Generation → Embedding → Vector Store
```

**Key Decisions:**

- **No image-to-text OCR**: Relies on PDF text for content, images for visual confirmation
  - *Rationale*: Floorplans are complex diagrams; OCR would be unreliable and expensive
  
- **Filename-based page mapping**: Extract page numbers from `Rev11-N.webp` format
  - *Rationale*: Reliable 1:1 mapping between images and PDF pages

- **Generated descriptions**: Create searchable text from page mappings
  - *Rationale*: Enables semantic search for images (e.g., "4BR with pool" → page 7 image)

**Image Description Template:**
```
"[X]BR [VILLA_TYPE] Type [A/B] floorplan - Ground and first floor layout [with/without pool]"
```

### 2. Vector Store Architecture

**Technology**: ChromaDB with HuggingFace embeddings (free) or OpenAI embeddings

**Schema Design:**
```python
{
  "collection": "al_badia_villas",
  "documents": [
    {
      "content": "text or image description",
      "metadata": {
        "source_type": "floorplans_pdf" | "floorplan_image",
        "page": int,
        "filename": str,  # for images
        "path": str,      # for images
        "chunk_id": str,  # for text
      }
    }
  ]
}
```

**Separation of Concerns:**
- Text and images share the same collection but are differentiated by `source_type`
- Enables filtered retrieval: `get_pdf_documents()` vs `get_image_documents()`

**Why ChromaDB?**
- Simple deployment (embedded database)
- Persistent storage
- Fast similarity search
- Metadata filtering support

### 3. Retrieval Strategy (RAG)

**Multi-stage retrieval pipeline:**
```
User Query → Embedding → Vector Search → Filtering → Ranking → Context Formation
```

#### Stage 1: Dual Retrieval

**PDF Retrieval** (Priority 1):
```python
query → embed → similarity_search(source_type="floorplans_pdf", k=5)
```

**Image Retrieval** (Priority 2):
```python
query → embed → similarity_search(source_type="floorplan_image", k=3)
```

#### Stage 2: Relevance Ranking

**PDF Ranking**: Based on cosine similarity scores
- Threshold: 0.7 similarity minimum
- Prioritizes exact matches over semantic similarity

**Image Ranking**: Custom scoring algorithm
```python
score = 0
if image.page in mentioned_pdf_pages: score += 10
if bedroom_count_matches_query: score += 5
if pool_requirement_matches: score += 3
```

*Rationale*: Images should align with retrieved PDF content for coherence

#### Stage 3: Context Assembly

**For LLM Prompt:**
```python
context = """
[Source: Floorplans PDF, Page 7]
4BR SHADEA Type B villa specifications...
---
[Source: Floorplans PDF, Page 8]
5BR MODEA villa specifications...
"""
```

**For Response:**
```python
images = [
  {
    "path": "data/WebP/...-7.webp",
    "description": "4BR SHADEA Type B with pool",
    "relevance": "floorplan"
  }
]
```

### 4. LLM Integration & Prompt Engineering

**Model**: GPT-3.5-turbo (configurable)

**System Prompt Architecture:**
```python
system_prompt = """
Role: Expert real estate advisor
Mission: Provide accurate info + qualify leads
Rules: [Critical constraints]
Knowledge: [Villa types available]
Approach: [Lead generation strategy]
Style: [Conversational tone]
"""
```

**Key Prompt Engineering Techniques:**

1. **Explicit Constraints**: "NEVER invent pricing or availability"
   - *Rationale*: Prevents hallucinations through clear boundaries

2. **Citation Requirements**: "Always cite the page number"
   - *Rationale*: Enforces grounding in source material

3. **Lead-Aware Context**: Include detected signals in prompt
   - *Rationale*: LLM can tailor responses to lead stage

4. **Conversational History**: Last 6 messages included
   - *Rationale*: Maintains context while avoiding token bloat

**User Prompt Structure:**
```
1. Retrieved Context (from PDF)
2. Conversation History (last 6 messages)
3. Lead Context (captured info + signals)
4. Current Query
5. Instructions
```

### 5. Lead Generation System

**Philosophy**: Natural qualification, not interrogation

#### Buying Signal Detection

**9 Signal Types:**

1. **Budget Mention**: Regex patterns for currency and amounts
2. **Specific Requirements**: Bedroom count, features, dimensions
3. **Timeline**: "soon", "by June", "this year"
4. **Location Preference**: "Dubai Festival City", "near golf"
5. **Luxury Interest**: "premium", "high-end", "pool"
6. **Comparison Intent**: "versus", "which is better"
7. **Purchase Questions**: "how to buy", "financing"
8. **Viewing Interest**: "see", "tour", "schedule"
9. **Current Situation**: "currently renting", "selling property"

**Implementation**: Regex-based pattern matching

*Rationale*: Deterministic, fast, no ML required for these clear signals

#### Intent Scoring Algorithm
```python
intent_score = sum(signal_weights) + engagement_bonus
```

**Signal Weights:**
- viewing_interest: 0.20 (highest)
- budget/timeline/purchase: 0.15 each
- specific_requirements/comparison: 0.10-0.12
- luxury/location/situation: 0.08-0.10

**Engagement Bonus**: +0.02 per message (capped at +0.15)

**Intent Classification:**
- Low: < 0.3
- Medium: 0.3 - 0.6
- High: > 0.6

*Rationale*: Weighted scoring reflects real lead qualification criteria from real estate sales

#### Action Recommendation Engine
```python
def recommend_action(intent, signals):
    if intent == "high" and "viewing_interest" in signals:
        return "schedule_viewing_immediately"
    elif intent == "high":
        return "capture_contact_and_schedule_callback"
    elif intent == "medium" and "specific_requirements" in signals:
        return "show_floorplans_and_qualify"
    # ... etc
```

**Actions drive follow-up prompts:**
- High intent → Request phone number for viewing
- Medium intent → Offer detailed floorplans via email
- Low intent → Educational content to build interest

### 6. Multimodal Response Assembly

**Image Inclusion Logic:**
```python
include_images = (
    should_include_images(query) OR
    len(properties_mentioned) > 0
)
```

**Conditions for image inclusion:**
1. Query contains visual keywords ("floorplan", "layout", "show")
2. Response mentions specific villa types
3. Always include for comparison requests

**Image Selection (Top 3):**
1. Rank by relevance score
2. Prefer images matching retrieved PDF pages
3. Match bedroom count and features to query

*Rationale*: Every villa discussion should have visual support, but limit to 3 to avoid overwhelming response

### 7. Guardrails & Safety

**Critical Rules:**

1. **No Pricing Hallucinations**
```python
   if "price" in query and "price" not in pdf_context:
       response += "Pricing requires agent confirmation"
```

2. **No Availability Hallucinations**
   - PDF doesn't contain availability → never claim units are available

3. **Page Citation Verification**
   - Only mention features explicitly in floorplans

**Implementation**: Prompt engineering + response validation

### 8. Session Management

**Session Data Structure:**
```python
{
  "session_id": str,
  "created_at": datetime,
  "updated_at": datetime,
  "messages": [{"role": str, "content": str, "timestamp": str}],
  "properties_viewed": [str],
  "lead_info": {"name": str, "email": str, "phone": str},
  "lead_status": "new" | "qualified" | "hot" | "converted",
  "buying_signals": [str]
}
```

**Storage**: In-memory dictionary (production: Redis)

**Lifecycle**:
- Created on first message
- Updated on each interaction
- Expired after 24 hours of inactivity

*Rationale*: Maintains conversation context while preventing unbounded memory growth

## Data Flow Diagram
```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Session Management                 │
│  - Load history                     │
│  - Detect signals                   │
│  - Extract contact info             │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Retrieval (RAG)                    │
│  - PDF search (top 5)               │
│  - Image search (top 3)             │
│  - Rank by relevance                │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  LLM Generation                     │
│  - Format context                   │
│  - Build prompt                     │
│  - Generate response                │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Response Assembly                  │
│  - Extract citations                │
│  - Identify properties              │
│  - Select images                    │
│  - Calculate intent                 │
│  - Generate follow-up               │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────┐
│  Response   │
└─────────────┘
```

## Performance Considerations

### Bottlenecks

1. **LLM API Latency**: 1-3 seconds per request (GPT-3.5-turbo)
   - *Mitigation*: Fast enough for real-time chat
   
2. **Vector Search**: 50-200ms for similarity search
   - *Mitigation*: Acceptable; can add caching for common queries

3. **Session Storage**: O(n) lookup in dictionary
   - *Mitigation*: Use Redis with indexed keys in production

### Optimization Strategies

1. **Embedding Caching**: Cache embeddings for common queries
2. **Context Pruning**: Limit conversation history to last 6 messages
3. **Batch Processing**: Process multiple sessions concurrently
4. **Connection Pooling**: Reuse OpenAI client connections

## Scalability

**Current Limitations** (Single Server):
- 10-20 concurrent users
- In-memory sessions (lost on restart)
- Single vector store instance

**Production Scaling Path**:

1. **Horizontal Scaling**:
```
   Load Balancer → [App Server 1, App Server 2, ...]
                    ↓
                    Redis (shared sessions)
                    ↓
                    ChromaDB
```

2. **Async Processing**: Use FastAPI's async capabilities
3. **CDN for Images**: Serve floorplans from CDN
4. **Database**: Move to PostgreSQL for lead storage

## Conclusion

This architecture prioritizes **accuracy over creativity**, **lead generation over information retrieval**, and **maintainability over complexity**. Every design decision traces back to the core mission: help users find their ideal villa while capturing qualified leads for the sales team.