# Ingestion Service Deployment Guide

This guide explains how to deploy the ingestion service to Google Cloud Platform (GCP) using Cloud Run.

## Overview

The ingestion service can be deployed in two ways:

1. **Cloud Run Service** - A web service that accepts HTTP requests for document ingestion
2. **Cloud Run Job** - A batch job that processes documents on-demand or on a schedule

For this project, we'll deploy it as a **Cloud Run Service** that can be triggered via HTTP requests, or as a **Cloud Run Job** for batch processing.

## Prerequisites

1. **GCP Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed (for local testing)
4. **Required APIs enabled**:
   - Cloud Run API
   - Cloud Build API
   - Artifact Registry API
   - Firestore API

Enable APIs:

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable firestore.googleapis.com
```

## Option 1: Deploy as Cloud Run Service (HTTP API)

### Step 1: Build and Deploy

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

**Note:** The ingestion service requires access to backend utilities. You may need to:

- Copy the backend `app/` directory into the ingestion Dockerfile context, or
- Package shared utilities as a Python package

### Step 2: Configure Environment Variables

Create `env.yaml` (copy from `env.yaml.example`):

```yaml
GCP_PROJECT_ID: your-gcp-project-id
FIRESTORE_COLLECTION: documents
GEMINI_API_KEY: your-gemini-api-key
GEMINI_EMBEDDING_MODEL: models/text-embedding-004
CHUNK_SIZE: "1000"
CHUNK_OVERLAP: "200"
```

### Step 3: Set Up Service Account

The ingestion service needs a service account with Firestore access:

```bash
# Create service account (if not exists)
gcloud iam service-accounts create rag-chatbot-sa \
  --display-name="RAG Chatbot Service Account"

# Grant Firestore access
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:rag-chatbot-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

### Step 4: Test the Deployment

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"
```

## Monitoring and Logging

View logs:

```bash
gcloud run services logs read $SERVICE_NAME --region $REGION
```

Monitor in Cloud Console:

- Cloud Run → Services → rag-ingestion → Logs
- Cloud Run → Services → rag-ingestion → Metrics

