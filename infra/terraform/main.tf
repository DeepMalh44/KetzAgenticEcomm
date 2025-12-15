# ============================================================================
# KetzAgenticEcomm - Terraform Infrastructure
# ============================================================================
# Deploys: VNet, Private Endpoints, AI Search, Cosmos DB, Blob Storage, 
#          Container Apps, Azure OpenAI, Azure AI Vision, ACS
# ============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~> 1.12"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
    cognitive_account {
      purge_soft_delete_on_destroy = true
    }
  }
  storage_use_azuread = true
}

provider "azapi" {}

# ============================================================================
# RANDOM SUFFIX FOR UNIQUE NAMES
# ============================================================================

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
  numeric = true
}

locals {
  resource_suffix = random_string.suffix.result
  resource_prefix = "ketzagentic"

  tags = {
    project     = "KetzAgenticEcomm"
    environment = var.environment
    managed_by  = "terraform"
  }
}

# ============================================================================
# RESOURCE GROUP
# ============================================================================

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.resource_prefix}-${local.resource_suffix}"
  location = var.location
  tags     = local.tags
}

# ============================================================================
# VIRTUAL NETWORK & SUBNETS
# ============================================================================

resource "azurerm_virtual_network" "main" {
  name                = "vnet-${local.resource_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = ["10.0.0.0/16"]
  tags                = local.tags
}

# Subnet for Container Apps (requires /23 minimum)
resource "azurerm_subnet" "container_apps" {
  name                 = "snet-containerapps"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.0.0/23"]

  delegation {
    name = "container-apps-delegation"
    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# Subnet for Private Endpoints
resource "azurerm_subnet" "private_endpoints" {
  name                 = "snet-privateendpoints"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]
}

# ============================================================================
# LOG ANALYTICS & APPLICATION INSIGHTS
# ============================================================================

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.resource_prefix}-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${local.resource_prefix}-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = local.tags
}

# ============================================================================
# AZURE OPENAI (GPT-4o Realtime)
# ============================================================================

resource "azurerm_cognitive_account" "openai" {
  name                  = "aoai-${local.resource_prefix}-${local.resource_suffix}"
  location              = var.openai_location
  resource_group_name   = azurerm_resource_group.main.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "aoai-${local.resource_prefix}-${local.resource_suffix}"
  local_auth_enabled    = true

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# GPT-4o for text (backup/tools)
resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = "gpt-4o"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o"
    version = "2024-08-06"
  }

  scale {
    type     = "Standard"
    capacity = 30
  }
}

# text-embedding-3-large for text embeddings
resource "azurerm_cognitive_deployment" "embedding" {
  name                 = "text-embedding-3-large"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-large"
    version = "1"
  }

  scale {
    type     = "Standard"
    capacity = 50
  }
}

# NOTE: GPT-4o Realtime deployment must be created manually via Azure Portal
# as it requires special access approval. The deployment name should be "gpt-4o-realtime"
# Once created, the backend will use it for voice conversations

# ============================================================================
# AZURE AI VISION (Florence for image embeddings)
# ============================================================================

resource "azurerm_cognitive_account" "vision" {
  name                  = "vision-${local.resource_prefix}-${local.resource_suffix}"
  location              = azurerm_resource_group.main.location
  resource_group_name   = azurerm_resource_group.main.name
  kind                  = "ComputerVision"
  sku_name              = "S1"
  custom_subdomain_name = "vision-${local.resource_prefix}-${local.resource_suffix}"
  local_auth_enabled    = true

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# ============================================================================
# AZURE AI SEARCH
# ============================================================================

resource "azurerm_search_service" "main" {
  name                = "search-${local.resource_prefix}-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = var.search_sku
  replica_count       = 1
  partition_count     = 1

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# ============================================================================
# COSMOS DB (MongoDB API)
# ============================================================================

resource "azurerm_cosmosdb_account" "main" {
  name                          = "cosmos-${local.resource_prefix}-${local.resource_suffix}"
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  offer_type                    = "Standard"
  kind                          = "MongoDB"
  public_network_access_enabled = false # Only allow private endpoint access

  capabilities {
    name = "EnableMongo"
  }

  capabilities {
    name = "EnableServerless"
  }

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  tags = local.tags
}

resource "azurerm_cosmosdb_mongo_database" "main" {
  name                = "ketzagenticecomm"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
}

resource "azurerm_cosmosdb_mongo_collection" "products" {
  name                = "products"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys = ["category", "subcategory"]
  }
}

resource "azurerm_cosmosdb_mongo_collection" "orders" {
  name                = "orders"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys = ["customer_id", "status"]
  }
}

resource "azurerm_cosmosdb_mongo_collection" "sessions" {
  name                = "sessions"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  index {
    keys   = ["_id"]
    unique = true
  }

  default_ttl_seconds = 86400 # 24 hours
}

# ============================================================================
# COSMOS DB PRIVATE ENDPOINT
# ============================================================================

resource "azurerm_private_dns_zone" "cosmos" {
  name                = "privatelink.mongo.cosmos.azure.com"
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "cosmos" {
  name                  = "cosmos-dns-link"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.cosmos.name
  virtual_network_id    = azurerm_virtual_network.main.id
  registration_enabled  = false
}

resource "azurerm_private_endpoint" "cosmos" {
  name                = "pe-cosmos-${local.resource_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints.id

  private_service_connection {
    name                           = "cosmos-privateserviceconnection"
    private_connection_resource_id = azurerm_cosmosdb_account.main.id
    subresource_names              = ["MongoDB"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "cosmos-dns-zone-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.cosmos.id]
  }

  tags = local.tags
}

# ============================================================================
# BLOB STORAGE (Product Images)
# ============================================================================

resource "azurerm_storage_account" "main" {
  name                            = "st${local.resource_prefix}${local.resource_suffix}"
  location                        = azurerm_resource_group.main.location
  resource_group_name             = azurerm_resource_group.main.name
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  shared_access_key_enabled       = true
  allow_nested_items_to_be_public = true  # Allow public access to product images

  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "HEAD", "OPTIONS"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }

  tags = local.tags
}

data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "deployer_storage_blob_data_owner" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_storage_container" "product_images" {
  name                  = "product-images"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"

  depends_on = [azurerm_role_assignment.deployer_storage_blob_data_owner]
}

resource "azurerm_storage_container" "uploads" {
  name                  = "uploads"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"

  depends_on = [azurerm_role_assignment.deployer_storage_blob_data_owner]
}

# ============================================================================
# AZURE COMMUNICATION SERVICES
# ============================================================================

resource "azurerm_communication_service" "main" {
  name                = "acs-${local.resource_prefix}-${local.resource_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  data_location       = "United States"

  tags = local.tags
}

# ============================================================================
# KEY VAULT
# ============================================================================

resource "azurerm_key_vault" "main" {
  name                      = "kv-${local.resource_prefix}-${local.resource_suffix}"
  location                  = azurerm_resource_group.main.location
  resource_group_name       = azurerm_resource_group.main.name
  tenant_id                 = data.azurerm_client_config.current.tenant_id
  sku_name                  = "standard"
  enable_rbac_authorization = true

  tags = local.tags
}

resource "azurerm_role_assignment" "deployer_kv_admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_key_vault_secret" "openai_key" {
  name         = "openai-key"
  value        = azurerm_cognitive_account.openai.primary_access_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.deployer_kv_admin]
}

resource "azurerm_key_vault_secret" "vision_key" {
  name         = "vision-key"
  value        = azurerm_cognitive_account.vision.primary_access_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.deployer_kv_admin]
}

resource "azurerm_key_vault_secret" "search_key" {
  name         = "search-key"
  value        = azurerm_search_service.main.primary_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.deployer_kv_admin]
}

resource "azurerm_key_vault_secret" "cosmos_connection" {
  name         = "cosmos-connection-string"
  value        = data.azurerm_cosmosdb_account.main.connection_strings[0]
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.deployer_kv_admin]
}

# Get Cosmos MongoDB connection string using data source
data "azurerm_cosmosdb_account" "main" {
  name                = azurerm_cosmosdb_account.main.name
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_key_vault_secret" "storage_connection" {
  name         = "storage-connection-string"
  value        = "DefaultEndpointsProtocol=https;AccountName=${azurerm_storage_account.main.name};EndpointSuffix=core.windows.net"
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.deployer_kv_admin]
}

resource "azurerm_key_vault_secret" "acs_connection" {
  name         = "acs-connection-string"
  value        = azurerm_communication_service.main.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.deployer_kv_admin]
}

# ============================================================================
# CONTAINER APPS ENVIRONMENT (WITH VNET INTEGRATION)
# ============================================================================

resource "azurerm_container_app_environment" "main" {
  name                           = "cae-${local.resource_prefix}-vnet"
  location                       = azurerm_resource_group.main.location
  resource_group_name            = azurerm_resource_group.main.name
  log_analytics_workspace_id     = azurerm_log_analytics_workspace.main.id
  infrastructure_subnet_id       = azurerm_subnet.container_apps.id
  internal_load_balancer_enabled = false

  tags = local.tags
}

# ============================================================================
# CONTAINER REGISTRY
# ============================================================================

resource "azurerm_container_registry" "main" {
  name                = "cr${local.resource_prefix}${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Basic"
  admin_enabled       = true

  tags = local.tags
}

# ============================================================================
# CONTAINER APPS
# ============================================================================

resource "azurerm_container_app" "backend" {
  name                         = "backend-vnet"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  template {
    min_replicas = var.container_app_replicas_min
    max_replicas = var.container_app_replicas_max

    container {
      name   = "backend-vnet"
      image  = "${azurerm_container_registry.main.login_server}/backend:latest"
      cpu    = 1.0
      memory = "2Gi"

      # Azure OpenAI
      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = azurerm_cognitive_account.openai.endpoint
      }

      # GPT-4o Realtime deployment (must be created manually in Azure Portal)
      env {
        name  = "AZURE_OPENAI_REALTIME_DEPLOYMENT"
        value = "gpt-4o-realtime"
      }

      env {
        name  = "AZURE_OPENAI_DEPLOYMENT"
        value = azurerm_cognitive_deployment.gpt4o.name
      }

      env {
        name  = "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        value = azurerm_cognitive_deployment.embedding.name
      }

      # Azure AI Vision
      env {
        name  = "AZURE_VISION_ENDPOINT"
        value = azurerm_cognitive_account.vision.endpoint
      }

      # Azure AI Search
      env {
        name  = "AZURE_SEARCH_ENDPOINT"
        value = "https://${azurerm_search_service.main.name}.search.windows.net"
      }

      env {
        name  = "AZURE_SEARCH_INDEX"
        value = "products"
      }

      # Search key (required for operations)
      env {
        name        = "AZURE_SEARCH_KEY"
        secret_name = "search-key"
      }

      # Azure Cosmos DB
      env {
        name        = "AZURE_COSMOS_CONNECTION_STRING"
        secret_name = "cosmos-connection"
      }

      env {
        name  = "AZURE_COSMOS_DATABASE"
        value = azurerm_cosmosdb_mongo_database.main.name
      }

      # Azure Storage
      env {
        name  = "AZURE_STORAGE_ACCOUNT_URL"
        value = azurerm_storage_account.main.primary_blob_endpoint
      }

      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = azurerm_storage_account.main.name
      }

      env {
        name  = "AZURE_STORAGE_CONTAINER"
        value = azurerm_storage_container.product_images.name
      }

      # Managed Identity flag (set to false to use connection strings/keys)
      env {
        name  = "USE_MANAGED_IDENTITY"
        value = "false"
      }

      # Application Insights
      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.main.connection_string
      }
    }
  }

  secret {
    name  = "cosmos-connection"
    value = data.azurerm_cosmosdb_account.main.connection_strings[0]
  }

  secret {
    name  = "search-key"
    value = azurerm_search_service.main.primary_key
  }

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = local.tags

  depends_on = [
    azurerm_private_endpoint.cosmos
  ]
}

resource "azurerm_container_app" "frontend" {
  name                         = "frontend-vnet"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "frontend-vnet"
      image  = "${azurerm_container_registry.main.login_server}/frontend:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = local.tags
}

# ============================================================================
# MANAGED IDENTITY ROLE ASSIGNMENTS FOR CONTAINER APP
# ============================================================================

resource "azurerm_role_assignment" "backend_openai_user" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_container_app.backend.identity[0].principal_id
}

resource "azurerm_role_assignment" "backend_vision_user" {
  scope                = azurerm_cognitive_account.vision.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_container_app.backend.identity[0].principal_id
}

resource "azurerm_role_assignment" "backend_search_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = azurerm_container_app.backend.identity[0].principal_id
}

resource "azurerm_role_assignment" "backend_search_service_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Service Contributor"
  principal_id         = azurerm_container_app.backend.identity[0].principal_id
}

resource "azurerm_role_assignment" "backend_storage_blob_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_container_app.backend.identity[0].principal_id
}

resource "azurerm_role_assignment" "backend_kv_secrets_user" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_container_app.backend.identity[0].principal_id
}
