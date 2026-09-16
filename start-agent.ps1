$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows'
if (-not (Test-Path -LiteralPath '.venv-windows\Scripts\python.exe')) {
    throw 'Trusted environment missing. See KRN_SETUP.md for setup.'
}
uv sync --locked
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
lk agent dev
