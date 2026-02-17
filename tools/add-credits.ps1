<#
.SYNOPSIS
    Add BotChips credits to a bot in Firestore.

.DESCRIPTION
    Reads the current balance of a bot from Firestore via the REST API
    and adds the specified amount.

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

$accessToken = gcloud auth print-access-token 2>$null
if (-not $accessToken) {
    Write-Host "ERROR: Failed to get access token. Run 'gcloud auth login' first." -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $accessToken"
    "Content-Type"  = "application/json"
}

$baseUrl = "https://firestore.googleapis.com/v1/projects/$ProjectId/databases/$DatabaseId/documents"

# Read current document
Write-Host "Reading current balance..." -ForegroundColor Cyan

try {
    $doc = Invoke-RestMethod -Uri "$baseUrl/Bots/$BotId" -Method GET -Headers $headers
} catch {
    Write-Host "ERROR: Bot '$BotId' not found in Firestore. $_" -ForegroundColor Red
    exit 1
}

$currentBalance = 0
if ($doc.fields.balance.integerValue) {
    $currentBalance = [int]$doc.fields.balance.integerValue
}
$botName = $doc.fields.name.stringValue

$newBalance = $currentBalance + $Amount

Write-Host "Bot name:        $botName" -ForegroundColor White
Write-Host "Current balance: $currentBalance BC" -ForegroundColor White
Write-Host "New balance:     $newBalance BC (+$Amount)" -ForegroundColor Green

# Update balance
Write-Host ""
Write-Host "Updating Firestore..." -ForegroundColor Cyan

$body = @{
    fields = @{
        balance = @{
            integerValue = "$newBalance"
        }
    }
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod `
        -Uri "$baseUrl/Bots/$BotId`?updateMask.fieldPaths=balance" `
        -Method PATCH `
        -Headers $headers `
        -Body $body

    Write-Host "[OK] Balance updated: $currentBalance -> $newBalance BC" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to update balance. $_" -ForegroundColor Red
    exit 1
}
