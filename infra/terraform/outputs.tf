# ============================================================================
# KetzAgenticEcomm - Terraform Outputs
# ============================================================================

# ============================================================================
# AZD REQUIRED OUTPUTS - These are used by Azure Developer CLI
# ============================================================================

output "AZURE_CONTAINER_REGISTRY_ENDPOINT" {
  description = "Container Registry endpoint for azd"
  value       = azurerm_container_registry.main.login_server
}

output "AZURE_CONTAINER_REGISTRY_NAME" {
  description = "Container Registry name for azd"
  value       = azurerm_container_registry.main.name
}

output "AZURE_RESOURCE_GROUP" {
  description = "Resource group name for azd"
  value       = azurerm_resource_group.main.name
}

output "AZURE_CONTAINER_ENVIRONMENT_NAME" {
  description = "Container Apps Environment name for azd"
  value       = azurerm_container_app_environment.main.name
}

# Service-specific outputs for azd (must match service names in azure.yaml)
output "SERVICE_BACKEND_NAME" {
  description = "Backend Container App name"
  value       = azurerm_container_app.backend.name
}

output "SERVICE_BACKEND_ENDPOINT_URL" {
  description = "Backend Container App URL"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "SERVICE_BACKEND_WS_URL" {
  description = "Backend WebSocket URL"
  value       = "wss://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "SERVICE_FRONTEND_NAME" {
  description = "Frontend Container App name"
  value       = azurerm_container_app.frontend.name
}

output "SERVICE_FRONTEND_ENDPOINT_URL" {
  description = "Frontend Container App URL"
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

# Environment variables for services (used by azd env)
output "AZURE_OPENAI_ENDPOINT" {
  description = "Azure OpenAI endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "AZURE_OPENAI_REALTIME_DEPLOYMENT" {
  description = "GPT-4o Realtime deployment name"
  value       = "gpt-4o-realtime"
}

output "AZURE_SEARCH_ENDPOINT" {
  description = "Azure AI Search endpoint"
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "AZURE_COSMOS_DATABASE" {
  description = "Cosmos DB database name"
  value       = azurerm_cosmosdb_mongo_database.main.name
}

output "AZURE_STORAGE_ACCOUNT_NAME" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "AZURE_STORAGE_CONTAINER" {
  description = "Storage container name"
  value       = azurerm_storage_container.product_images.name
}

# ============================================================================
# ADDITIONAL OUTPUTS
# ============================================================================

# Resource Group
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
}

# Azure OpenAI
output "openai_endpoint" {
  description = "Azure OpenAI endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_realtime_deployment" {
  description = "GPT-4o Realtime deployment name (must be created manually in Azure Portal)"
  value       = "gpt-4o-realtime"
}

# Azure AI Vision
output "vision_endpoint" {
  description = "Azure AI Vision endpoint"
  value       = azurerm_cognitive_account.vision.endpoint
}

# Azure AI Search
output "search_endpoint" {
  description = "Azure AI Search endpoint"
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "search_index" {
  description = "Azure AI Search index name"
  value       = "products"
}

# Cosmos DB
output "cosmos_endpoint" {
  description = "Cosmos DB endpoint"
  value       = azurerm_cosmosdb_account.main.endpoint
}

output "cosmos_database" {
  description = "Cosmos DB database name"
  value       = azurerm_cosmosdb_mongo_database.main.name
}

# Storage
output "storage_account" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "storage_images_url" {
  description = "Blob storage URL for product images"
  value       = "https://${azurerm_storage_account.main.name}.blob.core.windows.net/${azurerm_storage_container.product_images.name}"
}

# Azure Communication Services
output "acs_name" {
  description = "Azure Communication Services resource name"
  value       = azurerm_communication_service.main.name
}

# Container Apps
output "backend_url" {
  description = "Backend Container App URL"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "frontend_url" {
  description = "Frontend Container App URL"
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

# Container Registry
output "container_registry" {
  description = "Container Registry login server"
  value       = azurerm_container_registry.main.login_server
}

# Application Insights
output "app_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

# Key Vault
output "key_vault_name" {
  description = "Key Vault name"
  value       = azurerm_key_vault.main.name
}

# Virtual Network
output "vnet_name" {
  description = "Virtual Network name"
  value       = azurerm_virtual_network.main.name
}

output "vnet_id" {
  description = "Virtual Network ID"
  value       = azurerm_virtual_network.main.id
}

output "subnet_container_apps_id" {
  description = "Container Apps subnet ID"
  value       = azurerm_subnet.container_apps.id
}

output "subnet_private_endpoints_id" {
  description = "Private Endpoints subnet ID"
  value       = azurerm_subnet.private_endpoints.id
}

# Private Endpoint
output "cosmos_private_endpoint_name" {
  description = "Cosmos DB private endpoint name"
  value       = azurerm_private_endpoint.cosmos.name
}

output "cosmos_private_ip" {
  description = "Cosmos DB private IP address"
  value       = azurerm_private_endpoint.cosmos.private_service_connection[0].private_ip_address
}

# Environment Variables for Local Development
output "env_file_content" {
  description = "Content for .env file (sensitive values masked)"
  sensitive   = true
  value       = <<-EOT
    # KetzAgenticEcomm Environment Variables
    # Generated by Terraform
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT=${azurerm_cognitive_account.openai.endpoint}
    AZURE_OPENAI_API_KEY=<from-key-vault>
    AZURE_OPENAI_REALTIME_DEPLOYMENT=gpt-4o-realtime
    AZURE_OPENAI_DEPLOYMENT=${azurerm_cognitive_deployment.gpt4o.name}
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=${azurerm_cognitive_deployment.embedding.name}
    
    # Azure AI Vision
    AZURE_VISION_ENDPOINT=${azurerm_cognitive_account.vision.endpoint}
    AZURE_VISION_KEY=<from-key-vault>
    
    # Azure AI Search
    AZURE_SEARCH_ENDPOINT=https://${azurerm_search_service.main.name}.search.windows.net
    AZURE_SEARCH_KEY=<from-key-vault>
    AZURE_SEARCH_INDEX=products
    
    # Cosmos DB
    AZURE_COSMOS_CONNECTION_STRING=<from-key-vault>
    AZURE_COSMOS_DATABASE=${azurerm_cosmosdb_mongo_database.main.name}
    
    # Blob Storage
    AZURE_STORAGE_CONNECTION_STRING=<from-key-vault>
    AZURE_STORAGE_CONTAINER=${azurerm_storage_container.product_images.name}
    
    # Azure Communication Services
    ACS_CONNECTION_STRING=<from-key-vault>
    
    # Application Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING=${azurerm_application_insights.main.connection_string}
    
    # App URLs
    VITE_BACKEND_URL=https://${azurerm_container_app.backend.ingress[0].fqdn}
    VITE_WS_URL=wss://${azurerm_container_app.backend.ingress[0].fqdn}
  EOT
}
