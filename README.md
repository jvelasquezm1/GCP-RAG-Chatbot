# GCP RAG Chatbot - Step 2: Basic Chat

A minimal RAG chatbot project - currently at **Step 2: Basic Chat Endpoint**.

## Current Status

✅ **Step 2 Complete**: Basic chat endpoint with UI

- Backend: FastAPI with `/chat` POST endpoint (echo response, no AI yet)
- Frontend: React chat interface with message history
- Pydantic models for request/response validation
- No external dependencies (no Gemini, no Firestore yet)

## Quick Start

### Backend

```bash
cd backend

# Create virtual environment (if not already created)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (includes Pydantic for Step 2)
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

**API Endpoints:**

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /chat` - Chat endpoint (accepts `{"message": "your text"}`)

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

1. Start backend (port 8000)
2. Start frontend (port 5173)
3. Open browser to `http://localhost:5173`
4. Type a message and press Enter or click Send
5. You should see your message and a response

### Test with curl

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

Expected response:

```json
{
  "answer": "You said: 'Hello!'. This is Step 2 - basic chat endpoint working! (RAG coming in next steps)",
  "message": "Hello!"
}
```

## What's New in Step 2

### Backend Changes

- ✅ Added `POST /chat` endpoint
- ✅ Pydantic models for request/response validation
- ✅ Input validation (min/max length, required fields)
- ✅ Error handling with proper HTTP status codes

### Frontend Changes

- ✅ Chat interface with message history
- ✅ User and assistant message bubbles
- ✅ Input field with Enter key support
- ✅ Loading states and error handling
- ✅ Responsive design

## Project Structure

```
backend/
  app/
    main.py          # FastAPI app with /chat endpoint
  requirements.txt   # fastapi, uvicorn, pydantic

frontend/
  src/
    App.tsx          # Chat interface component
    App.css          # Chat styling
    config.ts        # API configuration
    main.tsx
  package.json
```

## Next Steps

We'll build incrementally:

- ✅ Step 1: Health check endpoint
- ✅ Step 2: Basic chat endpoint (current)
- Step 3: Add Gemini API integration
- Step 4: Add Firestore for document storage
- Step 5: Implement RAG retrieval
- Step 6: Add ingestion scripts
- Step 7: Deploy to Cloud Run

## Troubleshooting

**CORS errors?**

- Make sure backend CORS is configured for `http://localhost:5173`
- Restart backend after any CORS config changes

**Messages not sending?**

- Check browser console for errors
- Verify backend is running on port 8000
- Check network tab for API call status

**Validation errors?**

- Message must be between 1-1000 characters
- Message cannot be empty or only whitespace
