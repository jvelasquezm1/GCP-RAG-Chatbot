# Document Ingestion

Scripts for ingesting documents into Firestore for the RAG chatbot.

## Setup

1. Install dependencies:

```bash
cd ingestion
pip install -r requirements.txt
```

2. Set up environment variables. You can either:

   - Create a `.env` file in the project root (shared with backend)
   - Create a `.env` file in the `ingestion/` directory
   - Or set environment variables directly

   To get started, copy the example file:

   ```bash
   cp .env.example .env
   # Then edit .env and add your actual values
   ```

Required variables:

```env
GEMINI_API_KEY=your_api_key
GCP_PROJECT_ID=your-project-id
FIRESTORE_COLLECTION=documents  # Optional, defaults to "documents"
GEMINI_EMBEDDING_MODEL=models/text-embedding-004  # Optional, has default
CHUNK_SIZE=1000  # Optional, has default
CHUNK_OVERLAP=200  # Optional, has default
```

3. Authenticate with GCP (for local development):

```bash
gcloud auth application-default login
```

**Note:** The ingestion script uses the same configuration as the backend, so if you've already set up the backend `.env` file, you're good to go!

## Usage

### Ingest a single file:

```bash
python ingest_docs.py path/to/document.pdf
```

### Ingest a directory:

```bash
python ingest_docs.py path/to/documents/ --recursive
```

### Options:

- `--recursive, -r`: Recursively process subdirectories
- `--pattern, -p`: File pattern to match (default: `*.{md,markdown,pdf,txt}`)
- `--chunk-size`: Chunk size in characters
- `--chunk-overlap`: Chunk overlap in characters
- `--metadata`: Additional metadata as JSON string
- `--clear`: Clear existing collection before ingestion (USE WITH CAUTION)

### Examples:

```bash
# Ingest all markdown files recursively
python ingest_docs.py docs/ --recursive --pattern "*.md"

# Ingest with custom chunk size
python ingest_docs.py document.pdf --chunk-size 500 --chunk-overlap 100

# Ingest with metadata
python ingest_docs.py docs/ --metadata '{"source": "user_manual", "version": "1.0"}'
```

## Supported Formats

- Markdown (`.md`, `.markdown`)
- PDF (`.pdf`)
- Plain text (`.txt`)

## How It Works

1. **Document Reading**: The script reads documents based on file extension
2. **Text Chunking**: Documents are split into overlapping chunks for better retrieval
3. **Embedding Generation**: Each chunk is converted to an embedding vector using Gemini's embedding model
4. **Firestore Storage**: Chunks are stored in Firestore with:
   - Original text content
   - Embedding vector
   - Metadata (source file, chunk index, etc.)
   - Timestamp

## Deployment

```bash
cd ingestion

# Set your project ID
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1
export SERVICE_NAME=rag-ingestion

# Build and deploy
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --service-account rag-chatbot-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --env-vars-file env.yaml \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10
```

## Troubleshooting

**"GEMINI_API_KEY is required" error?**

- Ensure `.env` file exists in project root with `GEMINI_API_KEY` set
- Or set environment variable: `export GEMINI_API_KEY=your_key`

**"GCP_PROJECT_ID is required" error?**

- Ensure `.env` file exists in project root with `GCP_PROJECT_ID` set
- Or set environment variable: `export GCP_PROJECT_ID=your-project-id`

**Firestore authentication errors?**

- Run: `gcloud auth application-default login`
- Verify Firestore API is enabled in your GCP project
- Check that your GCP project ID is correct

**PDF reading errors?**

- Ensure PyPDF2 is installed: `pip install PyPDF2`
- Some PDFs may have encoding issues - try converting to text first

**No files found?**

- Check that the file path is correct
- Verify file extensions match the pattern
- Try using `--pattern "*.md"` to be more specific

**Slow ingestion?**

- Large documents take time to process (embedding generation)
- Progress is logged every 10 chunks
- Consider processing files in smaller batches
