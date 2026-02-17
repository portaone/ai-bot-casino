<#
.SYNOPSIS
    Add BotChips credits to a bot in Firestore.

.DESCRIPTION
    Reads the current balance of a bot from Firestore and adds the specified
    amount. Uses the gcloud firestore CLI.

.PARAMETER BotId
    The bot UUID. Required.

.PARAMETER Amount
    Number of BotChips to add. Required.

.PARAMETER ProjectId
    GCP project ID. Auto-detected from gcloud config if omitted.

.PARAMETER DatabaseId
    Firestore database ID. Default: aibotcasino

.EXAMPLE
    .\tools\add-credits.ps1 -BotId "a15ce333-8f05-424e-842b-63f50d3f1473" -Amount 10000
#>

param(
    [Parameter(Mandatory=$true)][string]$BotId,
    [Parameter(Mandatory=$true)][int]$Amount,
    [string]$ProjectId,
    [string]$DatabaseId = "aibotcasino"
)

$ErrorActionPreference = "Stop"

# Auto-detect ProjectId
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        Write-Host "ERROR: No ProjectId provided and no default project set." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Project: $ProjectId | Database: $DatabaseId" -ForegroundColor Gray
Write-Host "Bot ID:  $BotId" -ForegroundColor Gray
Write-Host "Adding:  $Amount BotChips" -ForegroundColor Gray
Write-Host ""

# Read current balance
Write-Host "Reading current balance..." -ForegroundColor Cyan
$doc = gcloud firestore documents get "projects/$ProjectId/databases/$DatabaseId/documents/Bots/$BotId" --format=json 2>$null

if ($LASTEXITCODE -ne 0 -or -not $doc) {
    Write-Host "ERROR: Bot '$BotId' not found in Firestore." -ForegroundColor Red
    exit 1
}

$parsed = $doc | ConvertFrom-Json
$currentBalance = 0
if ($parsed.fields.balance.integerValue) {
    $currentBalance = [int]$parsed.fields.balance.integerValue
}
$botName = $parsed.fields.name.stringValue

$newBalance = $currentBalance + $Amount

Write-Host "Bot name:        $botName" -ForegroundColor White
Write-Host "Current balance: $currentBalance BC" -ForegroundColor White
Write-Host "New balance:     $newBalance BC (+$Amount)" -ForegroundColor Green

# Update balance
Write-Host ""
Write-Host "Updating Firestore..." -ForegroundColor Cyan

gcloud firestore documents update "projects/$ProjectId/databases/$DatabaseId/documents/Bots/$BotId" `
    --update-fields="balance=$newBalance" `
    --quiet 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Balance updated: $currentBalance -> $newBalance BC" -ForegroundColor Green
} else {
    # Fallback: try using the REST API via gcloud
    Write-Host "Direct update failed, trying REST API..." -ForegroundColor Yellow

    $accessToken = gcloud auth print-access-token 2>$null
    $apiUrl = "https://firestore.googleapis.com/v1/projects/$ProjectId/databases/$DatabaseId/documents/Bots/$BotId`?updateMask.fieldPaths=balance"

    $body = @{
        fields = @{
            balance = @{
                integerValue = "$newBalance"
            }
        }
    } | ConvertTo-Json -Depth 5

    try {
        $response = Invoke-RestMethod -Uri $apiUrl -Method PATCH -Headers @{
            "Authorization" = "Bearer $accessToken"
            "Content-Type" = "application/json"
        } -Body $body

        Write-Host "[OK] Balance updated via REST API: $currentBalance -> $newBalance BC" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to update balance. $_" -ForegroundColor Red
        exit 1
    }
}
