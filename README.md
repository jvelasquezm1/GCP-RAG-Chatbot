# GCP RAG Chatbot - Step 4: Firestore Integration

A minimal RAG chatbot project - currently at **Step 4: Firestore Integration**.

## Current Status

✅ **Step 4 Complete**: Firestore integration for document storage

- Backend: FastAPI with `/chat` POST endpoint using Gemini API
- Frontend: React chat interface with message history
- AI Integration: Real AI responses via Google Gemini API
- Document Storage: Firestore client for storing and retrieving documents
- Configuration: Environment-based settings with Pydantic

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

**Get your Gemini API Key:**

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file: `GEMINI_API_KEY=your_key_here`

**Set up Firestore:**

1. Create a GCP project (or use an existing one)
2. Enable Firestore API in the GCP Console
3. Create a Firestore database in Native mode
4. For local development, authenticate: `gcloud auth application-default login`
5. Add to your `.env` file: `GCP_PROJECT_ID=your-project-id`

Backend will be available at `http://localhost:8000`

**API Endpoints:**

- `GET /` - Root endpoint
- `GET /health` - Health check (includes Gemini and Firestore status)
- `POST /chat` - Chat endpoint with AI responses (accepts `{"message": "your text"}`)

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

## What's New in Step 4

### Backend Changes

- ✅ Integrated Firestore for document storage
- ✅ Created `FirestoreClient` service module
- ✅ Firestore configuration (project ID, collection name)
- ✅ Health check includes Firestore connection status
- ✅ Document storage and retrieval capabilities

## Previous Steps

### Step 3: Gemini API Integration

- ✅ Integrated Gemini API for AI responses
- ✅ Created `GeminiClient` service module
- ✅ Configuration management with `pydantic-settings`
- ✅ Environment variable support (`.env` file)
- ✅ System prompt configuration
- ✅ Error handling for API failures
- ✅ Health check includes Gemini status

### Configuration

Create a `.env` file in the `backend/` directory:

```env
# Gemini API
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.7
SYSTEM_PROMPT=You are a helpful AI assistant...

# Firestore
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=global
FIRESTORE_COLLECTION=documents

# Application
DEBUG=false
```

### Project Structure

```
backend/
  app/
    main.py              # FastAPI app with /chat endpoint
    config.py            # Configuration management
    services/
      gemini_client.py   # Gemini API client
      firestore_client.py # Firestore client
  tests/
    test_main.py         # API endpoint tests
  requirements.txt       # Dependencies including google-generativeai, google-cloud-firestore
  .env.example          # Environment variables template

frontend/
  src/
    App.tsx              # Chat interface component
    components/
      Avatars.tsx        # Avatar components
    hooks/
      useAutoScroll.ts   # Auto-scroll hook
    types/
      chat.ts           # TypeScript types
  package.json
```

## Backend deployment

```bash
cd backend
gcloud run deploy rag-backend \
  --source . \
  --platform managed \
  --allow-unauthenticated \
  --region us-central1 \
  --env-vars-file .env.yaml
```

## Testing

Run backend tests:

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=xml --cov-report=term
```

Tests include:

- Endpoint validation
- Gemini API integration (mocked)
- Error handling
- Input validation

## Next Steps

We'll build incrementally:

- ✅ Step 1: Health check endpoint
- ✅ Step 2: Basic chat endpoint
- ✅ Step 3: Gemini API integration
- ✅ Step 4: Firestore integration (current)
- Step 5: Implement RAG retrieval
- Step 6: Add ingestion scripts

## Troubleshooting

**Gemini API errors?**

- Verify `GEMINI_API_KEY` is set in `.env` file
- Check API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Check API quota/limits
- Review backend logs for detailed error messages

**Firestore errors?**

- Verify `GCP_PROJECT_ID` is set in `.env` file
- Ensure Firestore API is enabled in your GCP project
- For local development, run: `gcloud auth application-default login`
- Check that Firestore database exists in Native mode
- Verify service account has `roles/datastore.user` permission (for Cloud Run)
- Review backend logs for detailed error messages

**503 Service Unavailable?**

- Gemini client not initialized - check `GEMINI_API_KEY` is set
- Firestore client not initialized - check `GCP_PROJECT_ID` is set
- Review backend startup logs

**CORS errors?**

- Make sure backend CORS is configured for `http://localhost:5173`
- Restart backend after any CORS config changes

**Messages not sending?**

- Check browser console for errors
- Verify backend is running on port 8000
- Check network tab for API call status
- Verify Gemini API key is configured

**Validation errors?**

- Message must be between 1-1000 characters
- Message cannot be empty or only whitespace
