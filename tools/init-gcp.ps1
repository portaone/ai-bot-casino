<#
.SYNOPSIS
    Initialize Google Cloud Platform project for AI Bot Casino.

.DESCRIPTION
    This script sets up all required GCP resources for the AI Bot Casino project:
    - Enables required APIs (Cloud Run, Firestore, Secret Manager, etc.)
    - Creates a Firestore database in Native mode
    - Creates a service account for Cloud Run with minimal permissions
    - Creates Secret Manager secrets (empty — you fill in values later)
    - Creates Artifact Registry repository for Docker images

.PARAMETER ProjectId
    The GCP project ID to initialize. Required.

.PARAMETER Region
    The GCP region for resources. Default: us-central1

.PARAMETER DatabaseId
    The Firestore database ID. Default: aibotcasino

.PARAMETER ServiceAccountName
    The service account name for Cloud Run. Default: aibotcasino-runner

.EXAMPLE
    .\init-gcp.ps1 -ProjectId "my-gcp-project"

.EXAMPLE
    .\init-gcp.ps1 -ProjectId "my-gcp-project" -Region "europe-west1"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "us-central1",

    [string]$DatabaseId = "aibotcasino",

    [string]$ServiceAccountName = "aibotcasino-runner"
)

$ErrorActionPreference = "Stop"

# ── Helpers ──────────────────────────────────────────────────────────────────

function Write-Step {
    param([string]$Message)
    Write-Host "`n══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Skip {
    param([string]$Message)
    Write-Host "  - $Message (already exists)" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message" -ForegroundColor Gray
}

# ── Verify prerequisites ────────────────────────────────────────────────────

Write-Step "Verifying prerequisites"

# Check gcloud is installed
try {
    $gcloudVersion = gcloud version --format="value(Google Cloud SDK)" 2>$null
    Write-Ok "gcloud CLI found: $gcloudVersion"
} catch {
    Write-Host "ERROR: gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
    exit 1
}

# Set the project
Write-Info "Setting active project to: $ProjectId"
gcloud config set project $ProjectId 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to set project. Verify the project ID is correct and you have access." -ForegroundColor Red
    exit 1
}
Write-Ok "Project set: $ProjectId"

# ── Step 1: Enable required APIs ────────────────────────────────────────────

Write-Step "Enabling required APIs"

$apis = @(
    "run.googleapis.com",              # Cloud Run
    "firestore.googleapis.com",        # Firestore
    "secretmanager.googleapis.com",    # Secret Manager
    "cloudbuild.googleapis.com",       # Cloud Build (for deployments)
    "artifactregistry.googleapis.com", # Artifact Registry (Docker images)
    "iam.googleapis.com"               # IAM (service accounts)
)

foreach ($api in $apis) {
    $shortName = $api -replace "\.googleapis\.com", ""
    Write-Info "Enabling $shortName..."
    gcloud services enable $api --quiet 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "$shortName API enabled"
    } else {
        Write-Host "  WARNING: Failed to enable $shortName API" -ForegroundColor Yellow
    }
}

# ── Step 2: Create Firestore database ───────────────────────────────────────

Write-Step "Creating Firestore database"

# Check if database already exists
$existingDb = gcloud firestore databases list --format="value(name)" 2>$null | Where-Object { $_ -match $DatabaseId }

if ($existingDb) {
    Write-Skip "Firestore database '$DatabaseId'"
} else {
    Write-Info "Creating Firestore database '$DatabaseId' in $Region (Native mode)..."
    gcloud firestore databases create `
        --database=$DatabaseId `
        --location=$Region `
        --type=firestore-native `
        --quiet 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Firestore database '$DatabaseId' created"
    } else {
        Write-Host "  WARNING: Failed to create database. It may already exist or the location may not support Firestore." -ForegroundColor Yellow
        Write-Info "You can create it manually: https://console.cloud.google.com/firestore"
    }
}

# ── Step 3: Create Artifact Registry repository ────────────────────────────

Write-Step "Creating Artifact Registry repository"

$repoName = "aibotcasino"
$existingRepo = gcloud artifacts repositories list --location=$Region --format="value(name)" 2>$null | Where-Object { $_ -eq $repoName }

if ($existingRepo) {
    Write-Skip "Artifact Registry repository '$repoName'"
} else {
    Write-Info "Creating Docker repository '$repoName' in $Region..."
    gcloud artifacts repositories create $repoName `
        --repository-format=docker `
        --location=$Region `
        --description="AI Bot Casino Docker images" `
        --quiet 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Artifact Registry repository '$repoName' created"
    } else {
        Write-Host "  WARNING: Failed to create repository" -ForegroundColor Yellow
    }
}

# ── Step 4: Create service account ──────────────────────────────────────────

Write-Step "Creating service account for Cloud Run"

$saEmail = "$ServiceAccountName@$ProjectId.iam.gserviceaccount.com"

$existingSa = gcloud iam service-accounts list --format="value(email)" 2>$null | Where-Object { $_ -eq $saEmail }

if ($existingSa) {
    Write-Skip "Service account '$ServiceAccountName'"
} else {
    Write-Info "Creating service account '$ServiceAccountName'..."
    gcloud iam service-accounts create $ServiceAccountName `
        --display-name="AI Bot Casino Cloud Run Service Account" `
        --quiet 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Service account created: $saEmail"
    } else {
        Write-Host "  WARNING: Failed to create service account" -ForegroundColor Yellow
    }
}

# Grant required roles to service account
Write-Info "Granting IAM roles..."

$roles = @(
    "roles/datastore.user",            # Firestore read/write
    "roles/secretmanager.secretAccessor", # Read secrets
    "roles/logging.logWriter",          # Write logs
    "roles/monitoring.metricWriter"     # Write metrics
)

foreach ($role in $roles) {
    $shortRole = $role -replace "roles/", ""
    gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$saEmail" `
        --role=$role `
        --quiet `
        --condition=None 2>$null | Out-Null

    Write-Ok "Granted $shortRole"
}

# ── Step 5: Create Secret Manager secrets ───────────────────────────────────

Write-Step "Creating Secret Manager secrets (empty — fill values later)"

$secrets = @(
    @{ Name = "aibotcasino-jwt-secret"; Description = "JWT signing secret (generate: openssl rand -hex 32)" },
    @{ Name = "aibotcasino-recaptcha-secret"; Description = "Google reCAPTCHA v3 secret key" },
    @{ Name = "aibotcasino-mailersend-api-key"; Description = "MailerSend API key for transactional emails" }
)

foreach ($secret in $secrets) {
    $existingSecret = gcloud secrets list --format="value(name)" 2>$null | Where-Object { $_ -eq $secret.Name }

    if ($existingSecret) {
        Write-Skip "Secret '$($secret.Name)'"
    } else {
        Write-Info "Creating secret '$($secret.Name)'..."
        gcloud secrets create $secret.Name `
            --replication-policy="automatic" `
            --quiet 2>$null

        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Secret '$($secret.Name)' created — $($secret.Description)"
        } else {
            Write-Host "  WARNING: Failed to create secret '$($secret.Name)'" -ForegroundColor Yellow
        }
    }
}

# ── Step 6: Generate JWT secret and store it ────────────────────────────────

Write-Step "Generating JWT secret"

Write-Info "Generating a random 256-bit JWT secret..."
$jwtSecret = -join ((1..32) | ForEach-Object { "{0:x2}" -f (Get-Random -Maximum 256) })

# Store it in Secret Manager
Write-Info "Storing JWT secret in Secret Manager..."
$jwtSecret | gcloud secrets versions add "aibotcasino-jwt-secret" --data-file=- --quiet 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Ok "JWT secret generated and stored in 'aibotcasino-jwt-secret'"
} else {
    Write-Host "  WARNING: Failed to store JWT secret. You can add it manually:" -ForegroundColor Yellow
    Write-Info "  echo 'YOUR_SECRET' | gcloud secrets versions add aibotcasino-jwt-secret --data-file=-"
}

# ── Summary ─────────────────────────────────────────────────────────────────

Write-Step "Setup Complete!"

$dockerRegistry = "$Region-docker.pkg.dev/$ProjectId/$repoName"

Write-Host @"

  Project:           $ProjectId
  Region:            $Region
  Firestore DB:      $DatabaseId
  Service Account:   $saEmail
  Docker Registry:   $dockerRegistry

  Secrets created (fill values via GCP Console or gcloud):
    - aibotcasino-jwt-secret      (auto-generated ✓)
    - aibotcasino-recaptcha-secret (set your reCAPTCHA v3 secret)
    - aibotcasino-mailersend-api-key (set your MailerSend API key)

  Next steps:
    1. Set secret values:
       echo "YOUR_KEY" | gcloud secrets versions add aibotcasino-recaptcha-secret --data-file=-
       echo "YOUR_KEY" | gcloud secrets versions add aibotcasino-mailersend-api-key --data-file=-

    2. Build and push Docker images:
       docker build -t $dockerRegistry/backend:latest ./backend
       docker build -t $dockerRegistry/frontend:latest ./frontend
       docker push $dockerRegistry/backend:latest
       docker push $dockerRegistry/frontend:latest

    3. Deploy to Cloud Run:
       gcloud run deploy aibotcasino-api \
         --image=$dockerRegistry/backend:latest \
         --service-account=$saEmail \
         --region=$Region \
         --set-secrets="AUTH_JWT_SECRET=aibotcasino-jwt-secret:latest,RECAPTCHA_SECRET_KEY=aibotcasino-recaptcha-secret:latest,EMAIL_MAILERSEND_API_KEY=aibotcasino-mailersend-api-key:latest" \
         --set-env-vars="MOCK_MODE=false,DATABASE_NAME=$DatabaseId,GCP_PROJECT_ID=$ProjectId"

"@ -ForegroundColor White
