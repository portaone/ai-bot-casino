<#
.SYNOPSIS
    Deploy the test bot as a Cloud Run Job.

.DESCRIPTION
    Builds the test-bot Docker image, pushes it to Artifact Registry,
    and creates/updates a Cloud Run Job that runs the bot continuously.

    The bot reads its configuration from environment variables:
      API_URL      - Casino API base URL (required)
      API_TOKEN    - Bot API token (required)
      STRATEGY     - Betting strategy (default: random)
      BET_SIZE     - Base bet size (default: 10)
      POLL_INTERVAL - Seconds between polls (default: 2.0)

.PARAMETER ProjectId
    GCP project ID. Auto-detected from gcloud config if omitted.

.PARAMETER Region
    GCP region. Default: europe-west1

.PARAMETER ApiUrl
    Casino API URL. Required.

.PARAMETER ApiToken
    Bot API token. Required.

.PARAMETER Strategy
    Betting strategy. Default: random

.PARAMETER BetSize
    Base bet size. Default: 10

.PARAMETER JobName
    Cloud Run Job name. Default: aibotcasino-bot

.EXAMPLE
    .\tools\deploy-bot.ps1 -ApiUrl "https://play.aibotcasino.com" -ApiToken "abc_sk_..."

.EXAMPLE
    .\tools\deploy-bot.ps1 -ApiUrl "https://play.aibotcasino.com" -ApiToken "abc_sk_..." -Strategy "martingale-red" -BetSize 5
#>

param(
    [string]$ProjectId,
    [string]$Region = "europe-west1",
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][string]$ApiToken,
    [string]$Strategy = "random",
    [int]$BetSize = 10,
    [string]$JobName = "aibotcasino-bot"
)

$ErrorActionPreference = "Stop"

# Auto-detect ProjectId
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        Write-Host "ERROR: No ProjectId provided and no default project set." -ForegroundColor Red
        exit 1
    }
    Write-Host "Using project: $ProjectId" -ForegroundColor Gray
}

$Registry = "$Region-docker.pkg.dev/$ProjectId/aibotcasino"
$ImageTag = "$Registry/test-bot:latest"

# --- Build & Push -----------------------------------------------------------

Write-Host ""
Write-Host "Building test-bot Docker image..." -ForegroundColor Cyan
gcloud builds submit ./test-bot `
    --tag $ImageTag `
    --region $Region `
    --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Image pushed: $ImageTag" -ForegroundColor Green

# --- Create or Update Cloud Run Job -----------------------------------------

Write-Host ""
Write-Host "Deploying Cloud Run Job '$JobName'..." -ForegroundColor Cyan

# Check if job already exists
$existingJob = gcloud run jobs list --region $Region --format="value(name)" 2>$null | Where-Object { $_ -eq $JobName }

$envVars = "API_URL=$ApiUrl,API_TOKEN=$ApiToken,STRATEGY=$Strategy,BET_SIZE=$BetSize,POLL_INTERVAL=2.0"

if ($existingJob) {
    Write-Host "Updating existing job..." -ForegroundColor Gray
    gcloud run jobs update $JobName `
        --region $Region `
        --image $ImageTag `
        --set-env-vars $envVars `
        --task-timeout 24h `
        --max-retries 3 `
        --memory 512Mi `
        --cpu 1 `
        --quiet

} else {
    Write-Host "Creating new job..." -ForegroundColor Gray
    gcloud run jobs create $JobName `
        --region $Region `
        --image $ImageTag `
        --set-env-vars $envVars `
        --task-timeout 24h `
        --max-retries 3 `
        --memory 512Mi `
        --cpu 1 `
        --quiet
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Job deployment failed." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Job '$JobName' deployed" -ForegroundColor Green

# --- Execute the job ---------------------------------------------------------

Write-Host ""
Write-Host "Starting job execution..." -ForegroundColor Cyan
gcloud run jobs execute $JobName --region $Region --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Job started!" -ForegroundColor Green
} else {
    Write-Host "WARNING: Job created but failed to start. Start manually:" -ForegroundColor Yellow
    Write-Host "  gcloud run jobs execute $JobName --region $Region" -ForegroundColor Yellow
}

# --- Summary -----------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Bot Deployment Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host @"

  Job name:    $JobName
  Image:       $ImageTag
  Strategy:    $Strategy
  Bet size:    $BetSize
  API URL:     $ApiUrl
  Timeout:     24h (auto-restarts up to 3 times)

  Useful commands:
    # View logs
    gcloud run jobs executions list --job $JobName --region $Region
    gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JobName" --limit 50

    # Re-run the bot
    gcloud run jobs execute $JobName --region $Region

    # Stop current execution
    gcloud run jobs executions list --job $JobName --region $Region
    gcloud run jobs executions cancel <EXECUTION_NAME> --region $Region

    # Update strategy
    gcloud run jobs update $JobName --region $Region --set-env-vars "STRATEGY=martingale-red"
    gcloud run jobs execute $JobName --region $Region

"@ -ForegroundColor White
