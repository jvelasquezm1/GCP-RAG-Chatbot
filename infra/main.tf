terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Service Account for Cloud Run
resource "google_service_account" "rag_chatbot_sa" {
  account_id   = var.service_account_name
  display_name = "RAG Chatbot Service Account"
  description  = "Service account for RAG Chatbot Cloud Run service"
}

# IAM roles for service account
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.rag_chatbot_sa.email}"
}

# Note: Firestore in Native mode is created automatically when first accessed
# We don't need to explicitly create it via Terraform, but we can document it

# Cloud Run Service
resource "google_cloud_run_service" "rag_chatbot_api" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.rag_chatbot_sa.email

      containers {
        image = var.container_image != "" ? var.container_image : "gcr.io/${var.project_id}/${var.service_name}:latest"

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "FIRESTORE_COLLECTION"
          value = var.firestore_collection
        }

        # Note: GEMINI_API_KEY should be set via Secret Manager in production
        # For now, it can be set as an environment variable or via Cloud Run UI
      }

      timeout_seconds = var.timeout
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = tostring(var.min_instances)
        "autoscaling.knative.dev/maxScale" = tostring(var.max_instances)
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.required_apis
  ]
}

# Allow unauthenticated access (optional - remove if you want authentication)
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.rag_chatbot_api.name
  location = google_cloud_run_service.rag_chatbot_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.rag_chatbot_api.status[0].url
}

output "service_account_email" {
  description = "Email of the service account"
  value       = google_service_account.rag_chatbot_sa.email
}

output "firestore_info" {
  description = "Information about Firestore setup"
  value = {
    collection_name = var.firestore_collection
    note            = "Firestore in Native mode is created automatically when first accessed. Ensure it's enabled in the GCP Console."
  }
}

