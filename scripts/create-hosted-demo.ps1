$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Join-Path $PSScriptRoot '..')
$region = if ($env:KRN_LIVEKIT_REGION) { $env:KRN_LIVEKIT_REGION } else { 'eu-central' }

Write-Host "1/3 Creating the LiveKit Cloud agent in $region..."
lk agent create --yes --project krn-01 --region $region
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '2/3 Sending GOOGLE_API_KEY from .env.local into the cloud agent...'
lk agent update-secrets --yes --project krn-01 --secrets-file .env.local --ignore-empty-secrets
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '3/3 Commit livekit.toml, then connect Vercel and GitHub secrets as in KRN_SETUP.md'
Write-Host 'Choose a demo password (8+ characters). Put it in Vercel as KRN_DEMO_PASSWORD.'
