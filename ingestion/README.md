# Document Ingestion

Scripts for ingesting documents into Firestore for the RAG chatbot.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (create `.env` file in project root):
```
GEMINI_API_KEY=your_api_key
GCP_PROJECT_ID=your-project-id
FIRESTORE_COLLECTION=document_chunks
```

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


