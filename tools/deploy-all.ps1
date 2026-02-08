<#
.SYNOPSIS
    Deploy all AI Bot Casino services to Google Cloud Run.

.DESCRIPTION
    Deploys all services in the correct order:
    1. Backend (aibotcasino-api) - deployed first because frontend needs its URL
    2. Frontend (aibotcasino-web) - auto-detects backend URL for VITE_API_URL

    This script calls deploy.ps1 for each service, passing through all parameters.

.PARAMETER ProjectId
    The GCP project ID. Required.

.PARAMETER Region
    The GCP region for Cloud Run. Default: europe-west1

.PARAMETER Tag
    Docker image tag. Default: latest

.PARAMETER SkipBuild
    Skip Docker build and push; deploy existing images only.

.EXAMPLE
    .\deploy-all.ps1 -ProjectId "my-gcp-project"

.EXAMPLE
    .\deploy-all.ps1 -ProjectId "my-gcp-project" -Tag "v1.2.0"

.EXAMPLE
    .\deploy-all.ps1 -ProjectId "my-gcp-project" -SkipBuild
#>

param(
    [string]$ProjectId,

    [string]$Region = "europe-west1",

    [string]$Tag = "latest",

    [switch]$SkipBuild
)

# Auto-detect ProjectId from gcloud config if not provided
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        Write-Host "ERROR: No ProjectId provided and no default project set in gcloud." -ForegroundColor Red
        Write-Host "  Use: .\deploy-all.ps1 -ProjectId YOUR_PROJECT" -ForegroundColor Yellow
        Write-Host "  Or:  gcloud config set project YOUR_PROJECT" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  Using project from gcloud config: $ProjectId" -ForegroundColor Gray
}

$ErrorActionPreference = "Continue"

# --- Helpers -----------------------------------------------------------------

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message" -ForegroundColor Gray
}

# --- Resolve deploy.ps1 path ------------------------------------------------

$deployScript = Join-Path $PSScriptRoot "deploy.ps1"

if (-not (Test-Path $deployScript)) {
    Write-Host "ERROR: deploy.ps1 not found at: $deployScript" -ForegroundColor Red
    exit 1
}

# --- Build common arguments --------------------------------------------------

$commonArgs = @{
    ProjectId = $ProjectId
    Region    = $Region
    Tag       = $Tag
}

if ($SkipBuild) {
    $commonArgs["SkipBuild"] = $true
}

# --- Deploy backend first ----------------------------------------------------

Write-Step "Deploying backend (1/2)"

& $deployScript -Service "backend" @commonArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Backend deployment failed. Aborting." -ForegroundColor Red
    exit 1
}

Write-Ok "Backend deployment complete"

# --- Deploy frontend ----------------------------------------------------------

Write-Step "Deploying frontend (2/2)"

& $deployScript -Service "frontend" @commonArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Frontend deployment failed." -ForegroundColor Red
    exit 1
}

Write-Ok "Frontend deployment complete"

# --- Summary -----------------------------------------------------------------

Write-Step "All services deployed!"

$backendUrl = gcloud run services describe aibotcasino-api `
    --region=$Region `
    --format="value(status.url)" 2>$null

$frontendUrl = gcloud run services describe aibotcasino-web `
    --region=$Region `
    --format="value(status.url)" 2>$null

Write-Host ""
Write-Host "  Backend (API):  $backendUrl" -ForegroundColor Green
Write-Host "  Frontend (Web): $frontendUrl" -ForegroundColor Green
Write-Host ""
