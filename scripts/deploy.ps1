# ============================================================================
# KetzAgenticEcomm - Full Deployment Script
# ============================================================================
# Deploys all infrastructure and applications to Azure
# Usage: .\scripts\deploy.ps1
# ============================================================================

param(
    [string]$ResourceGroup = "rg-ketzagentic-kh7xm2",
    [string]$Location = "eastus2",
    [string]$BackendName = "backend-vnet",
    [string]$FrontendName = "frontend-vnet",
    [switch]$SkipInfra,
    [switch]$SkipBuild,
    [switch]$SkipDeploy
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "KetzAgenticEcomm Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STEP 1: Deploy Infrastructure with Terraform (Optional)
# ============================================================================
if (-not $SkipInfra) {
    Write-Host "[1/4] Deploying Infrastructure..." -ForegroundColor Yellow
    
    Push-Location "$RootDir\infra\terraform"
    
    try {
        Write-Host "  - Running terraform init..." -ForegroundColor Gray
        terraform init -upgrade | Out-Null
        
        Write-Host "  - Running terraform plan..." -ForegroundColor Gray
        terraform plan -out=tfplan
        
        Write-Host "  - Running terraform apply..." -ForegroundColor Gray
        terraform apply -auto-approve tfplan
        
        Write-Host "  ✓ Infrastructure deployed!" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
} else {
    Write-Host "[1/4] Skipping Infrastructure (--SkipInfra)" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# Get resource info from Azure directly
# ============================================================================
Write-Host "  Fetching resource info from Azure..." -ForegroundColor Gray

# Get ACR name
$ACR_NAME = (az acr list -g $ResourceGroup --query "[0].name" -o tsv)
$ACR_SERVER = "${ACR_NAME}.azurecr.io"

# Get Container App URLs
$BACKEND_FQDN = (az containerapp show -n $BackendName -g $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv 2>$null)
if (-not $BACKEND_FQDN) {
    Write-Host "  Warning: Backend container app '$BackendName' not found. Using default." -ForegroundColor Yellow
    $BACKEND_URL = "https://$BackendName.azurecontainerapps.io"
    $WS_URL = "wss://$BackendName.azurecontainerapps.io"
} else {
    $BACKEND_URL = "https://$BACKEND_FQDN"
    $WS_URL = "wss://$BACKEND_FQDN"
}

Write-Host ""
Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor Gray
Write-Host "  ACR: $ACR_SERVER" -ForegroundColor Gray
Write-Host "  Backend: $BackendName" -ForegroundColor Gray
Write-Host "  Frontend: $FrontendName" -ForegroundColor Gray
Write-Host "  Backend URL: $BACKEND_URL" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# STEP 2: Login to ACR
# ============================================================================
Write-Host "[2/4] Logging into Container Registry..." -ForegroundColor Yellow
az acr login --name $ACR_NAME
Write-Host "  ✓ Logged into ACR" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 3: Build and Push Docker Images
# ============================================================================
if (-not $SkipBuild) {
    Write-Host "[3/4] Building and Pushing Docker Images..." -ForegroundColor Yellow
    
    # Get current timestamp for versioning
    $VERSION = Get-Date -Format "yyyyMMdd-HHmmss"
    
    # Build Backend
    Write-Host "  - Building backend..." -ForegroundColor Gray
    Push-Location "$RootDir\backend"
    docker build -t "${ACR_SERVER}/backend:${VERSION}" -t "${ACR_SERVER}/backend:latest" .
    
    Write-Host "  - Pushing backend..." -ForegroundColor Gray
    docker push "${ACR_SERVER}/backend:${VERSION}"
    docker push "${ACR_SERVER}/backend:latest"
    Pop-Location
    
    Write-Host "  ✓ Backend image pushed (${VERSION})" -ForegroundColor Green
    
    # Build Frontend
    Write-Host "  - Building frontend..." -ForegroundColor Gray
    Push-Location "$RootDir\frontend"
    docker build `
        --build-arg VITE_BACKEND_URL=$BACKEND_URL `
        --build-arg VITE_WS_URL=$WS_URL `
        -t "${ACR_SERVER}/frontend:${VERSION}" `
        -t "${ACR_SERVER}/frontend:latest" .
    
    Write-Host "  - Pushing frontend..." -ForegroundColor Gray
    docker push "${ACR_SERVER}/frontend:${VERSION}"
    docker push "${ACR_SERVER}/frontend:latest"
    Pop-Location
    
    Write-Host "  ✓ Frontend image pushed (${VERSION})" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[3/4] Skipping Build (--SkipBuild)" -ForegroundColor Gray
    $VERSION = "latest"
    Write-Host ""
}

# ============================================================================
# STEP 4: Update Container Apps
# ============================================================================
if (-not $SkipDeploy) {
    Write-Host "[4/4] Updating Container Apps..." -ForegroundColor Yellow
    
    # Update Backend
    Write-Host "  - Updating backend container app..." -ForegroundColor Gray
    az containerapp update `
        --name $BackendName `
        --resource-group $ResourceGroup `
        --image "${ACR_SERVER}/backend:latest" `
        --output none
    
    Write-Host "  ✓ Backend updated" -ForegroundColor Green
    
    # Update Frontend
    Write-Host "  - Updating frontend container app..." -ForegroundColor Gray
    az containerapp update `
        --name $FrontendName `
        --resource-group $ResourceGroup `
        --image "${ACR_SERVER}/frontend:latest" `
        --output none
    
    Write-Host "  ✓ Frontend updated" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[4/4] Skipping Deploy (--SkipDeploy)" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================

# Get final URLs
$FRONTEND_FQDN = (az containerapp show -n $FrontendName -g $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv 2>$null)
$BACKEND_FQDN = (az containerapp show -n $BackendName -g $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv 2>$null)

Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend URL: https://$FRONTEND_FQDN" -ForegroundColor Cyan
Write-Host "Backend URL:  https://$BACKEND_FQDN" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create GPT-4o-realtime deployment in Azure OpenAI Studio (if not done)"
Write-Host "  2. Run: python scripts/seed_products.py"
Write-Host "  3. Run: python scripts/index_images.py"
Write-Host ""
