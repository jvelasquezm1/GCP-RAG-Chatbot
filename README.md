## Quick Start

### Backend

```bash
cd backend

# Create virtual environment (if not already created)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (includes Gemini API client)
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and GCP_PROJECT_ID

# Run the server
uvicorn app.main:app --reload --port 8000
```


Backend will be available at `http://localhost:8000`

### Document Ingestion

Before using RAG, you need to ingest documents into Firestore from the frontend or with the ingestion service:

```bash
cd ingestion

# Install dependencies
pip install -r requirements.txt

# Ingest a single document
python ingest_docs.py path/to/document.pdf

# Ingest a directory of documents
python ingest_docs.py path/to/documents/ --recursive

# Ingest with custom options
python ingest_docs.py docs/ --recursive --pattern "*.md" --chunk-size 1000
```

See `ingestion/README.md` for detailed usage instructions.

### Frontend

```bash
cd frontend

# Install dependencies (if not already installed)
npm install

# Run dev server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Test the Chat

1. Start backend (port 8000) with `GEMINI_API_KEY` set
2. Start frontend (port 5173)
3. Open browser to `http://localhost:5173`
4. Type a message and press Enter or click Send
5. You should see your message and an AI-generated response from Gemini

### Test with curl

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is artificial intelligence?"}'
```

Expected response:

```json
{
  "answer": "Artificial intelligence (AI) is...",
  "message": "What is artificial intelligence?"
}
```
### RAG Flow

1. User sends a message
2. Generate query embedding using Gemini embedding model
3. Search Firestore for similar document chunks using cosine similarity
4. Retrieve top K most relevant chunks
5. Build context from retrieved documents
6. Generate response using Gemini with context


## Backend deployment

```bash
cd backend
gcloud run deploy rag-backend \
  --source . \
  --platform managed \
  --allow-unauthenticated \
  --region us-central1 \
  --env-vars-file env.yaml
```

