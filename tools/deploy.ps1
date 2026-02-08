<#
.SYNOPSIS
    Deploy a single AI Bot Casino service to Google Cloud Run.

.DESCRIPTION
    Builds a Docker image and deploys it to Cloud Run for the specified service.
    Supports backend (aibotcasino-api) and frontend (aibotcasino-web).

    Backend deployment includes:
    - Secret Manager secrets (JWT, MailerSend)
    - Environment variables (MOCK_MODE, DATABASE_NAME, GCP_PROJECT_ID)
    - Service account binding

    Frontend deployment includes:
    - Auto-detection of backend Cloud Run URL for VITE_API_URL
    - Port 80 configuration

.PARAMETER ProjectId
    The GCP project ID. Required.

.PARAMETER Service
    Which service to deploy: "backend" or "frontend". Required.

.PARAMETER Region
    The GCP region for Cloud Run. Default: europe-west1

.PARAMETER Tag
    Docker image tag. Default: latest

.PARAMETER SkipBuild
    Skip Docker build and push; deploy an existing image only.

.EXAMPLE
    .\deploy.ps1 -ProjectId "my-gcp-project" -Service backend

.EXAMPLE
    .\deploy.ps1 -ProjectId "my-gcp-project" -Service frontend -Tag "v1.2.0"

.EXAMPLE
    .\deploy.ps1 -ProjectId "my-gcp-project" -Service backend -SkipBuild
#>

param(
    [string]$ProjectId,

    [Parameter(Mandatory = $true)]
    [ValidateSet("backend", "frontend")]
    [string]$Service,

    [string]$Region = "europe-west1",

    [string]$Tag = "latest",

    [switch]$SkipBuild
)

# Auto-detect ProjectId from gcloud config if not provided
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        Write-Host "ERROR: No ProjectId provided and no default project set in gcloud." -ForegroundColor Red
        Write-Host "  Use: .\deploy.ps1 -ProjectId YOUR_PROJECT -Service backend" -ForegroundColor Yellow
        Write-Host "  Or:  gcloud config set project YOUR_PROJECT" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  Using project from gcloud config: $ProjectId" -ForegroundColor Gray
}

$ErrorActionPreference = "Continue"

# --- Helpers -----------------------------------------------------------------

$script:ErrLog = Join-Path $env:TEMP "deploy-err.txt"

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

function Write-Fail {
    param([string]$Message)
    Write-Host "  [FAIL] $Message" -ForegroundColor Red
    if (Test-Path $script:ErrLog) {
        $errContent = (Get-Content $script:ErrLog -Raw -ErrorAction SilentlyContinue)
        if ($errContent) {
            foreach ($line in ($errContent.Trim() -split "`n")) {
                Write-Host "         $line" -ForegroundColor Red
            }
        }
    }
}

# --- Variables ---------------------------------------------------------------

$repoName = "aibotcasino"
$registry = "$Region-docker.pkg.dev/$ProjectId/$repoName"
$image = "$registry/${Service}:$Tag"
$saEmail = "aibotcasino-runner@$ProjectId.iam.gserviceaccount.com"

if ($Service -eq "backend") {
    $cloudRunService = "aibotcasino-api"
} else {
    $cloudRunService = "aibotcasino-web"
}

# --- Verify prerequisites ----------------------------------------------------

Write-Step "Verifying prerequisites"

try {
    $gcloudOutput = gcloud version 2>$null | Select-Object -First 1
    Write-Ok "gcloud CLI found: $gcloudOutput"
} catch {
    Write-Host "  ERROR: gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
    exit 1
}

if (-not $SkipBuild) {
    try {
        $dockerVersion = docker version --format "{{.Client.Version}}" 2>$null
        Write-Ok "Docker found: $dockerVersion"
    } catch {
        Write-Host "  ERROR: Docker not found or not running." -ForegroundColor Red
        exit 1
    }
}

# Set the project
Write-Info "Setting active project to: $ProjectId"
gcloud config set project $ProjectId 2>"$script:ErrLog"
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Failed to set project. Verify the project ID and your access."
    exit 1
}
Write-Ok "Project set: $ProjectId"

# Check billing is enabled
Write-Info "Checking billing status..."
$billingEnabled = gcloud billing projects describe $ProjectId --format="value(billingEnabled)" 2>"$script:ErrLog"
if ($billingEnabled -ne "True") {
    Write-Host ""
    Write-Host "  ERROR: Billing is NOT enabled for project '$ProjectId'." -ForegroundColor Red
    Write-Host "  Cloud Run deployment requires billing to be enabled." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Enable billing at:" -ForegroundColor Yellow
    Write-Host "  https://console.cloud.google.com/billing/linkedaccount?project=$ProjectId" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Then re-run this script." -ForegroundColor Yellow
    exit 1
}
Write-Ok "Billing is enabled"

# --- Configure Docker auth ---------------------------------------------------

if (-not $SkipBuild) {
    Write-Step "Configuring Docker authentication"

    Write-Info "Setting up auth for $Region-docker.pkg.dev..."
    gcloud auth configure-docker "$Region-docker.pkg.dev" --quiet 2>"$script:ErrLog"
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Docker auth configured"
    } else {
        Write-Fail "Failed to configure Docker auth. Push may fail."
    }
}

# --- Build Docker image ------------------------------------------------------

if (-not $SkipBuild) {
    Write-Step "Building Docker image: $Service"

    Write-Info "Image: $image"
    Write-Info "Context: ./$Service"

    docker build -t $image "./$Service"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Docker build failed for $Service" -ForegroundColor Red
        exit 1
    }
    Write-Ok "Docker image built: $image"

    # --- Push Docker image --------------------------------------------------------

    Write-Step "Pushing Docker image"

    Write-Info "Pushing $image..."
    docker push $image
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Docker push failed. Check Artifact Registry permissions." -ForegroundColor Red
        exit 1
    }
    Write-Ok "Image pushed: $image"
} else {
    Write-Step "Skipping build (--SkipBuild)"
    Write-Info "Will deploy existing image: $image"
}

# --- Deploy to Cloud Run -----------------------------------------------------

Write-Step "Deploying $Service to Cloud Run"

Write-Info "Service:  $cloudRunService"
Write-Info "Image:    $image"
Write-Info "Region:   $Region"

if ($Service -eq "backend") {
    Write-Info "Deploying backend with secrets and env vars..."

    gcloud run deploy $cloudRunService `
        --image=$image `
        --region=$Region `
        --platform=managed `
        --service-account=$saEmail `
        --allow-unauthenticated `
        --update-secrets="AUTH_JWT_SECRET=aibotcasino-jwt-secret:latest,EMAIL_MAILERSEND_API_KEY=aibotcasino-mailersend-api-key:latest" `
        --update-env-vars="MOCK_MODE=false,DATABASE_NAME=aibotcasino,GCP_PROJECT_ID=$ProjectId" `
        --quiet 2>"$script:ErrLog"

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to deploy $cloudRunService"
        Remove-Item $script:ErrLog -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    # Frontend: detect backend URL first
    Write-Info "Detecting backend URL..."
    $backendUrl = gcloud run services describe aibotcasino-api `
        --region=$Region `
        --format="value(status.url)" 2>"$script:ErrLog"

    if (-not $backendUrl) {
        Write-Fail "Could not detect backend URL. Deploy backend first."
        $backendUrl = "https://aibotcasino-api-FIXME.a.run.app"
        Write-Info "Using placeholder; set VITE_API_URL manually after deploy."
    } else {
        Write-Ok "Backend URL: $backendUrl"
    }

    Write-Info "Deploying frontend with VITE_API_URL=$backendUrl..."

    gcloud run deploy $cloudRunService `
        --image=$image `
        --region=$Region `
        --platform=managed `
        --allow-unauthenticated `
        --port=80 `
        --update-env-vars="CLOUD_RUN=true,VITE_API_URL=$backendUrl" `
        --quiet 2>"$script:ErrLog"

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to deploy $cloudRunService"
        Remove-Item $script:ErrLog -ErrorAction SilentlyContinue
        exit 1
    }
}

Write-Ok "$cloudRunService deployed successfully"

# --- Print deployed URL ------------------------------------------------------

Write-Step "Deployment Complete!"

$serviceUrl = gcloud run services describe $cloudRunService `
    --region=$Region `
    --format="value(status.url)" 2>$null

if ($serviceUrl) {
    Write-Host ""
    Write-Host "  Service: $cloudRunService" -ForegroundColor White
    Write-Host "  URL:     $serviceUrl" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Info "Could not retrieve service URL. Check the Cloud Run console."
}

# --- Cleanup temp file -------------------------------------------------------

Remove-Item $script:ErrLog -ErrorAction SilentlyContinue
