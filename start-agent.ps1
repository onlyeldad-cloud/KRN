$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows313'
if (-not (Test-Path -LiteralPath '.venv-windows313\Scripts\python.exe')) {
    throw 'Trusted environment missing. See KRN_SETUP.md for setup.'
}
# LiveKit CLI prefers .venv, which is blocked on this PC. Keep the working
# official Python 3.13 environment first. The Python 3.14 grpcio binary
# is blocked by Smart App Control on this PC.
$venv = (Resolve-Path -LiteralPath '.venv-windows313').Path
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
exit $LASTEXITCODE
