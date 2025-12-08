# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy ingestion code
COPY ingest_docs.py .
COPY .env.example .env.example

# Note: The ingestion script requires backend utilities
# We need to copy the backend app directory for shared utilities
# In a production setup, these could be packaged as a shared library
COPY ../backend/app ./backend/app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/backend

# The ingestion service can be run as a Cloud Run job or service
# For Cloud Run service, we'd need a web server (FastAPI)
# For Cloud Run job, we can use the CLI directly
# This Dockerfile supports both use cases

# Default command (can be overridden)
CMD ["python", "ingest_docs.py", "--help"]
