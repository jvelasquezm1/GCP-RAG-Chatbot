# Infrastructure as Code

Terraform configuration for deploying the RAG Chatbot to Google Cloud Platform.

## Prerequisites

1. Install Terraform (>= 1.0)
2. Install Google Cloud SDK
3. Authenticate with GCP:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

## Setup

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your project details:
   ```hcl
   project_id = "your-gcp-project-id"
   region     = "us-central1"
   ```

3. Initialize Terraform:
   ```bash
   terraform init
   ```

4. Review the plan:
   ```bash
   terraform plan
   ```

5. Apply the configuration:
   ```bash
   terraform apply
   ```

## Resources Created

- **APIs Enabled**: Cloud Run, Firestore, Cloud Build, Artifact Registry
- **Service Account**: For Cloud Run service with Firestore access
- **Cloud Run Service**: Backend API service (configured for free tier)
- **IAM Bindings**: Service account permissions

## Firestore Setup

Firestore in Native mode is created automatically when first accessed. Ensure it's enabled in the GCP Console:
1. Go to Firestore in the GCP Console
2. Select "Native mode"
3. Choose a location (same as your region)

## Container Image

Before deploying, you need to build and push the container image:

```bash
# Build the image
cd backend
docker build -t gcr.io/YOUR_PROJECT_ID/rag-chatbot-api:latest .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/rag-chatbot-api:latest

# Update terraform.tfvars with the image URL
# Then run: terraform apply
```

## Environment Variables

Set sensitive environment variables (like `GEMINI_API_KEY`) via:
1. Cloud Run UI: Go to the service → Edit & Deploy → Variables & Secrets
2. Or use Secret Manager (recommended for production)

## Free Tier Considerations

- `min_instances = 0`: Service scales to zero when not in use
- `max_instances = 10`: Limits scaling to control costs
- Firestore: Free tier includes 1GB storage and 50K reads/day
- Cloud Run: Free tier includes 2 million requests/month

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

**Warning**: This will delete all resources including Firestore data!

