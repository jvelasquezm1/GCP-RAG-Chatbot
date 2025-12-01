# GCP RAG Chatbot - Step 1: Health Check

A minimal RAG chatbot project - currently at **Step 1: Health Check Only**.

## Current Status

✅ **Step 1 Complete**: Basic health check endpoint

- Backend: FastAPI with `/health` endpoint
- Frontend: React app that displays health status
- No external dependencies (no Gemini, no Firestore yet)

## Quick Start

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install minimal dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Test Health Check

1. Start backend (port 8000)
2. Start frontend (port 5173)
3. Open browser to `http://localhost:5173`
4. You should see "healthy" status

Or test directly:
```bash
curl http://localhost:8000/health
```

## Next Steps

We'll build incrementally:
- Step 2: Add basic chat endpoint (no RAG yet)
- Step 3: Add Gemini API integration
- Step 4: Add Firestore for document storage
- Step 5: Implement RAG retrieval
- Step 6: Add ingestion scripts
- Step 7: Deploy to Cloud Run
