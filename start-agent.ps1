$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows'
if (-not (Test-Path -LiteralPath '.venv-windows\Scripts\python.exe')) {
    throw 'Trusted environment missing. See KRN_SETUP.md for setup.'
}
# LiveKit CLI prefers .venv, which is blocked on this PC. Keep the working
# Python 3.14 environment first so the agent loads Playwright and pyexpat.
$venv = (Resolve-Path -LiteralPath '.venv-windows').Path
$env:VIRTUAL_ENV = $venv
# Use the user-wide Playwright cache, not a Cursor sandbox path.
if (-not $env:PLAYWRIGHT_BROWSERS_PATH) {
    $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:LOCALAPPDATA 'ms-playwright'
}
$env:PATH = @(
    (Join-Path $venv 'Scripts')
    (Join-Path $env:USERPROFILE '.local\bin')
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\LiveKit.LiveKitCLI_Microsoft.Winget.Source_8wekyb3d8bbwe"
    'C:\Program Files\nodejs'
    $env:PATH
) -join ';'
uv sync --locked
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
uv run python src/agent.py dev
