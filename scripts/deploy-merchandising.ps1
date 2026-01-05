# ============================================================================
# Merchandising Portal - Deployment Script (Feature 1 & 2)
# ============================================================================
# Deploys merchandising backend and frontend to Azure Container Apps
# Usage: .\scripts\deploy-merchandising.ps1
# ============================================================================

param(
    [string]$ResourceGroup = "rg-ketzagentic-kh7xm2",
    [string]$Location = "eastus2",
    [string]$BackendName = "merchandising-backend",
    [string]$FrontendName = "merchandising-frontend",
    [switch]$SkipBuild,
    [switch]$SkipDeploy
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Merchandising Portal Deployment" -ForegroundColor Cyan
Write-Host "Feature 1: Rules Management" -ForegroundColor Cyan
Write-Host "Feature 2: Synonym Management" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Get resource info from Azure
# ============================================================================
Write-Host "[1/3] Fetching Azure Resources..." -ForegroundColor Yellow

# Get ACR name
$ACR_NAME = (az acr list -g $ResourceGroup --query "[0].name" -o tsv)
if (-not $ACR_NAME) {
    Write-Host "  ERROR: No Container Registry found in $ResourceGroup" -ForegroundColor Red
    exit 1
}
$ACR_SERVER = "${ACR_NAME}.azurecr.io"

Write-Host ""
Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor Gray
Write-Host "  ACR: $ACR_SERVER" -ForegroundColor Gray
Write-Host "  Backend App: $BackendName" -ForegroundColor Gray
Write-Host "  Frontend App: $FrontendName" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Login to ACR
# ============================================================================
Write-Host "  - Logging into Container Registry..." -ForegroundColor Gray
az acr login --name $ACR_NAME
Write-Host "  ✓ Logged into ACR" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 2: Build and Push Docker Images
# ============================================================================
if (-not $SkipBuild) {
    Write-Host "[2/3] Building and Pushing Docker Images..." -ForegroundColor Yellow
    
    # Get current timestamp for versioning
    $VERSION = "v2-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    
    # Build Merchandising Backend
    Write-Host "  - Building merchandising backend..." -ForegroundColor Gray
    Push-Location "$RootDir\merchandising-backend"
    docker build -t "${ACR_SERVER}/merchandising-backend:${VERSION}" -t "${ACR_SERVER}/merchandising-backend:v2" -t "${ACR_SERVER}/merchandising-backend:latest" .
    
    Write-Host "  - Pushing merchandising backend..." -ForegroundColor Gray
    docker push "${ACR_SERVER}/merchandising-backend:${VERSION}"
    docker push "${ACR_SERVER}/merchandising-backend:v2"
    docker push "${ACR_SERVER}/merchandising-backend:latest"
    Pop-Location
    
    Write-Host "  ✓ Backend image pushed (${VERSION})" -ForegroundColor Green
    
    # Get backend URL for frontend build
    $BACKEND_FQDN = (az containerapp show -n $BackendName -g $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv 2>$null)
    if (-not $BACKEND_FQDN) {
        Write-Host "  Warning: Backend not found. Using default URL pattern." -ForegroundColor Yellow
        $BACKEND_URL = "https://${BackendName}.happyisland-58d32b38.eastus2.azurecontainerapps.io"
    } else {
        $BACKEND_URL = "https://$BACKEND_FQDN"
    }
    
    # Build Merchandising Frontend
    Write-Host "  - Building merchandising frontend..." -ForegroundColor Gray
    Write-Host "    Backend API: $BACKEND_URL" -ForegroundColor Gray
    Push-Location "$RootDir\merchandising-frontend"
    docker build `
        --build-arg VITE_API_BASE=$BACKEND_URL `
        -t "${ACR_SERVER}/merchandising-frontend:${VERSION}" `
        -t "${ACR_SERVER}/merchandising-frontend:v2" `
        -t "${ACR_SERVER}/merchandising-frontend:latest" .
    
    Write-Host "  - Pushing merchandising frontend..." -ForegroundColor Gray
    docker push "${ACR_SERVER}/merchandising-frontend:${VERSION}"
    docker push "${ACR_SERVER}/merchandising-frontend:v2"
    docker push "${ACR_SERVER}/merchandising-frontend:latest"
    Pop-Location
    
    Write-Host "  ✓ Frontend image pushed (${VERSION})" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[2/3] Skipping Build (--SkipBuild)" -ForegroundColor Gray
    $VERSION = "v2"
    Write-Host ""
}

# ============================================================================
# STEP 3: Update Container Apps
# ============================================================================
if (-not $SkipDeploy) {
    Write-Host "[3/3] Updating Container Apps..." -ForegroundColor Yellow
    
    # Check if apps exist, create if not
    $backendExists = az containerapp show -n $BackendName -g $ResourceGroup --query "name" -o tsv 2>$null
    $frontendExists = az containerapp show -n $FrontendName -g $ResourceGroup --query "name" -o tsv 2>$null
    
    # Get Container App Environment
    $ENV_NAME = (az containerapp env list -g $ResourceGroup --query "[0].name" -o tsv)
    if (-not $ENV_NAME) {
        Write-Host "  ERROR: No Container App Environment found!" -ForegroundColor Red
        exit 1
    }
    
    # Get Azure resources (Cosmos DB, Search, etc.)
    $COSMOS_ENDPOINT = (az cosmosdb list -g $ResourceGroup --query "[0].documentEndpoint" -o tsv)
    $COSMOS_KEY = (az cosmosdb keys list -g $ResourceGroup --name (az cosmosdb list -g $ResourceGroup --query "[0].name" -o tsv) --query "primaryMasterKey" -o tsv)
    $SEARCH_ENDPOINT = (az search service list -g $ResourceGroup --query "[0].searchServiceUri" -o tsv)
    $SEARCH_KEY = (az search admin-key show -g $ResourceGroup --service-name (az search service list -g $ResourceGroup --query "[0].name" -o tsv) --query "primaryKey" -o tsv)
    
    # Update or Create Backend
    if ($backendExists) {
        Write-Host "  - Updating backend container app..." -ForegroundColor Gray
        az containerapp update `
            --name $BackendName `
            --resource-group $ResourceGroup `
            --image "${ACR_SERVER}/merchandising-backend:v2" `
            --set-env-vars `
                "AZURE_COSMOS_ENDPOINT=${COSMOS_ENDPOINT}" `
                "AZURE_COSMOS_KEY=${COSMOS_KEY}" `
                "AZURE_COSMOS_DATABASE=merchandising" `
                "AZURE_SEARCH_ENDPOINT=${SEARCH_ENDPOINT}" `
                "AZURE_SEARCH_KEY=${SEARCH_KEY}" `
                "AZURE_SEARCH_INDEX=products" `
            --output none
        Write-Host "  ✓ Backend updated" -ForegroundColor Green
    } else {
        Write-Host "  - Creating backend container app..." -ForegroundColor Gray
        az containerapp create `
            --name $BackendName `
            --resource-group $ResourceGroup `
            --environment $ENV_NAME `
            --image "${ACR_SERVER}/merchandising-backend:v2" `
            --target-port 8000 `
            --ingress external `
            --registry-server $ACR_SERVER `
            --env-vars `
                "AZURE_COSMOS_ENDPOINT=${COSMOS_ENDPOINT}" `
                "AZURE_COSMOS_KEY=${COSMOS_KEY}" `
                "AZURE_COSMOS_DATABASE=merchandising" `
                "AZURE_SEARCH_ENDPOINT=${SEARCH_ENDPOINT}" `
                "AZURE_SEARCH_KEY=${SEARCH_KEY}" `
                "AZURE_SEARCH_INDEX=products" `
            --cpu 0.5 `
            --memory 1.0Gi `
            --min-replicas 1 `
            --max-replicas 3 `
            --output none
        Write-Host "  ✓ Backend created" -ForegroundColor Green
    }
    
    # Get final backend URL
    $BACKEND_FQDN = (az containerapp show -n $BackendName -g $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv)
    $BACKEND_URL = "https://$BACKEND_FQDN"
    
    # Update or Create Frontend
    if ($frontendExists) {
        Write-Host "  - Updating frontend container app..." -ForegroundColor Gray
        az containerapp update `
            --name $FrontendName `
            --resource-group $ResourceGroup `
            --image "${ACR_SERVER}/merchandising-frontend:v2" `
            --output none
        Write-Host "  ✓ Frontend updated" -ForegroundColor Green
    } else {
        Write-Host "  - Creating frontend container app..." -ForegroundColor Gray
        az containerapp create `
            --name $FrontendName `
            --resource-group $ResourceGroup `
            --environment $ENV_NAME `
            --image "${ACR_SERVER}/merchandising-frontend:v2" `
            --target-port 80 `
            --ingress external `
            --registry-server $ACR_SERVER `
            --cpu 0.25 `
            --memory 0.5Gi `
            --min-replicas 1 `
            --max-replicas 2 `
            --output none
        Write-Host "  ✓ Frontend created" -ForegroundColor Green
    }
    
    Write-Host ""
} else {
    Write-Host "[3/3] Skipping Deploy (--SkipDeploy)" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================

# Get final URLs
$FRONTEND_FQDN = (az containerapp show -n $FrontendName -g $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv 2>$null)
$BACKEND_FQDN = (az containerapp show -n $BackendName -g $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv 2>$null)

Write-Host "========================================" -ForegroundColor Green
Write-Host "Merchandising Portal Deployed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend URL: https://$FRONTEND_FQDN" -ForegroundColor Cyan
Write-Host "Backend URL:  https://$BACKEND_FQDN" -ForegroundColor Cyan
Write-Host ""
Write-Host "Features:" -ForegroundColor Yellow
Write-Host "  ✓ Feature 1: Rules Management (/rules)" -ForegroundColor Green
Write-Host "  ✓ Feature 2: Synonym Management (/synonyms)" -ForegroundColor Green
Write-Host ""
Write-Host "Test the deployment:" -ForegroundColor Yellow
Write-Host "  1. Open frontend URL in browser"
Write-Host "  2. Navigate to Rules or Synonyms"
Write-Host "  3. Create test rules/synonyms"
Write-Host "  4. Test synonym search impact"
Write-Host ""
