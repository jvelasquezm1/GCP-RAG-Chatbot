variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for resources"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "rag-chatbot-api"
}

variable "firestore_collection" {
  description = "Firestore collection name for document chunks"
  type        = string
  default     = "document_chunks"
}

variable "service_account_name" {
  description = "Name of the service account for Cloud Run"
  type        = string
  default     = "rag-chatbot-sa"
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances (0 for free tier)"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cpu" {
  description = "CPU allocation for Cloud Run service"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation for Cloud Run service"
  type        = string
  default     = "512Mi"
}

variable "timeout" {
  description = "Request timeout for Cloud Run service (seconds)"
  type        = number
  default     = 300
}

variable "container_image" {
  description = "Container image URL for Cloud Run service"
  type        = string
  default     = ""
}

