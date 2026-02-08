<#
.SYNOPSIS
    Initialize Google Cloud Platform project for AI Bot Casino.

.DESCRIPTION
    This script sets up all required GCP resources for the AI Bot Casino project:
    - Enables required APIs (Cloud Run, Firestore, Secret Manager, etc.)
    - Creates a Firestore database in Native mode
    - Creates a service account for Cloud Run with minimal permissions
    - Creates Secret Manager secrets (empty - you fill in values later)
    - Creates Artifact Registry repository for Docker images

.PARAMETER ProjectId
    The GCP project ID to initialize. Required.

.PARAMETER Region
    The GCP region for resources. Default: europe-west1

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
    [string]$ProjectId,

    [string]$Region = "europe-west1",

    [string]$DatabaseId = "aibotcasino",

    [string]$ServiceAccountName = "aibotcasino-runner"
)

# Auto-detect ProjectId from gcloud config if not provided
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        Write-Host "ERROR: No ProjectId provided and no default project set in gcloud." -ForegroundColor Red
        Write-Host "  Use: .\init-gcp.ps1 -ProjectId YOUR_PROJECT" -ForegroundColor Yellow
        Write-Host "  Or:  gcloud config set project YOUR_PROJECT" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  Using project from gcloud config: $ProjectId" -ForegroundColor Gray
}

$ErrorActionPreference = "Continue"

# --- Helpers -----------------------------------------------------------------

$script:ErrLog = Join-Path $env:TEMP "init-gcp-err.txt"

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

function Write-Skip {
    param([string]$Message)
    Write-Host "  [SKIP] $Message (already exists)" -ForegroundColor Yellow
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

# --- Verify prerequisites ----------------------------------------------------

Write-Step "Verifying prerequisites"

# Check gcloud is installed
try {
    $gcloudOutput = gcloud version 2>$null | Select-Object -First 1
    Write-Ok "gcloud CLI found: $gcloudOutput"
} catch {
    Write-Host "  ERROR: gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
    exit 1
}

# Set the project
Write-Info "Setting active project to: $ProjectId"
gcloud config set project $ProjectId 2>"$script:ErrLog"
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Failed to set project. Verify the project ID is correct and you have access."
    exit 1
}
Write-Ok "Project set: $ProjectId"

# Check billing is enabled
Write-Info "Checking billing status..."
$billingEnabled = gcloud billing projects describe $ProjectId --format="value(billingEnabled)" 2>"$script:ErrLog"
if ($billingEnabled -ne "True") {
    Write-Host ""
    Write-Host "  ERROR: Billing is NOT enabled for project '$ProjectId'." -ForegroundColor Red
    Write-Host "  Most GCP services (Cloud Run, Secret Manager, Artifact Registry)" -ForegroundColor Red
    Write-Host "  require billing to be enabled before they can be activated." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Enable billing at:" -ForegroundColor Yellow
    Write-Host "  https://console.cloud.google.com/billing/linkedaccount?project=$ProjectId" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Then re-run this script." -ForegroundColor Yellow
    exit 1
}
Write-Ok "Billing is enabled"

# --- Step 1: Enable required APIs --------------------------------------------

Write-Step "Enabling required APIs"

$apis = @(
    "run.googleapis.com",              # Cloud Run
    "firestore.googleapis.com",        # Firestore
    "secretmanager.googleapis.com",    # Secret Manager
    "cloudbuild.googleapis.com",       # Cloud Build (for deployments)
    "artifactregistry.googleapis.com", # Artifact Registry (Docker images)
    "iam.googleapis.com",              # IAM (service accounts)
    "recaptchaenterprise.googleapis.com" # reCAPTCHA Enterprise
)

foreach ($api in $apis) {
    $shortName = $api -replace "\.googleapis\.com", ""
    Write-Info "Enabling $shortName..."
    gcloud services enable $api --quiet 2>"$script:ErrLog"
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "$shortName API enabled"
    } else {
        Write-Fail "Failed to enable $shortName API"
    }
}

# --- Step 2: Create Firestore database ---------------------------------------

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
        --quiet 2>"$script:ErrLog"

    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Firestore database '$DatabaseId' created"
    } else {
        Write-Fail "Failed to create Firestore database '$DatabaseId'"
        Write-Info "You can create it manually: https://console.cloud.google.com/firestore"
    }
}

# --- Step 3: Create Artifact Registry repository -----------------------------

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
        --quiet 2>"$script:ErrLog"

    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Artifact Registry repository '$repoName' created"
    } else {
        Write-Fail "Failed to create Artifact Registry repository '$repoName'"
    }
}

# --- Step 4: Create service account ------------------------------------------

Write-Step "Creating service account for Cloud Run"

$saEmail = "$ServiceAccountName@$ProjectId.iam.gserviceaccount.com"

$existingSa = gcloud iam service-accounts list --format="value(email)" 2>$null | Where-Object { $_ -eq $saEmail }

if ($existingSa) {
    Write-Skip "Service account '$ServiceAccountName'"
} else {
    Write-Info "Creating service account '$ServiceAccountName'..."
    gcloud iam service-accounts create $ServiceAccountName `
        --display-name="AI Bot Casino Cloud Run Service Account" `
        --quiet 2>"$script:ErrLog"

    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Service account created: $saEmail"
    } else {
        Write-Fail "Failed to create service account '$ServiceAccountName'"
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
        --condition=None 2>"$script:ErrLog" | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Granted $shortRole"
    } else {
        Write-Fail "Failed to grant $shortRole"
    }
}

# --- Step 5: Create Secret Manager secrets -----------------------------------

Write-Step "Creating Secret Manager secrets (empty - fill values later)"

$secrets = @(
    @{ Name = "aibotcasino-jwt-secret"; Description = "JWT signing secret" }
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
            --quiet 2>"$script:ErrLog"

        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Secret '$($secret.Name)' created - $($secret.Description)"
        } else {
            Write-Fail "Failed to create secret '$($secret.Name)'"
        }
    }
}

# --- Step 6: Generate JWT secret and store it --------------------------------

Write-Step "Generating JWT secret"

Write-Info "Generating a random 256-bit JWT secret..."
$jwtSecret = -join ((1..32) | ForEach-Object { "{0:x2}" -f (Get-Random -Maximum 256) })

# Store it in Secret Manager
Write-Info "Storing JWT secret in Secret Manager..."
$jwtSecret | gcloud secrets versions add "aibotcasino-jwt-secret" --data-file=- --quiet 2>"$script:ErrLog"

if ($LASTEXITCODE -eq 0) {
    Write-Ok "JWT secret generated and stored in 'aibotcasino-jwt-secret'"
} else {
    Write-Fail "Failed to store JWT secret"
    Write-Info "You can add it manually: echo 'YOUR_SECRET' | gcloud secrets versions add aibotcasino-jwt-secret --data-file=-"
}

# --- Cleanup temp file -------------------------------------------------------

Remove-Item $script:ErrLog -ErrorAction SilentlyContinue

# --- Summary -----------------------------------------------------------------

Write-Step "Setup Complete!"

$dockerRegistry = "$Region-docker.pkg.dev/$ProjectId/$repoName"

Write-Host @"

  Project:           $ProjectId
  Region:            $Region
  Firestore DB:      $DatabaseId
  Service Account:   $saEmail
  Docker Registry:   $dockerRegistry

  Secrets created (fill values via GCP Console or gcloud):
    - aibotcasino-jwt-secret      (auto-generated)
    - aibotcasino-mailersend-api-key (set your MailerSend API key)

  reCAPTCHA Enterprise:
    Uses project-level API (no secret key needed).
    Create a site key at: https://console.cloud.google.com/security/recaptcha?project=$ProjectId

  Next steps:
    1. Set secret values:
       echo "YOUR_KEY" | gcloud secrets versions add aibotcasino-mailersend-api-key --data-file=-

    2. Deploy services:
       .\tools\deploy-all.ps1 -ProjectId "$ProjectId"
       See deploy.ps1 and deploy-all.ps1 for deployment options.

"@ -ForegroundColor White
