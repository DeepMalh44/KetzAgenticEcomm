# ============================================================================
# KetzAgenticEcomm - Terraform Variables
# ============================================================================

variable "location" {
  description = "Azure region for resource deployment"
  type        = string
  default     = "eastus2"
}

variable "openai_location" {
  description = "Azure region for OpenAI (GPT-4o Realtime available regions)"
  type        = string
  default     = "eastus2"

  validation {
    condition     = contains(["eastus2", "swedencentral", "westus3"], var.openai_location)
    error_message = "GPT-4o Realtime is only available in eastus2, swedencentral, or westus3."
  }
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "enable_acs_phone" {
  description = "Whether to purchase a phone number for ACS (additional cost)"
  type        = bool
  default     = false
}

variable "container_app_replicas_min" {
  description = "Minimum number of container app replicas"
  type        = number
  default     = 1
}

variable "container_app_replicas_max" {
  description = "Maximum number of container app replicas"
  type        = number
  default     = 5
}

variable "search_sku" {
  description = "Azure AI Search SKU (standard required for vector search)"
  type        = string
  default     = "standard"

  validation {
    condition     = contains(["standard", "standard2", "standard3"], var.search_sku)
    error_message = "Search SKU must be standard, standard2, or standard3 for vector search."
  }
}
