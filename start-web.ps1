$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Join-Path $PSScriptRoot 'frontend')
$nodeDir = 'C:\Program Files\nodejs'
if (Test-Path -LiteralPath (Join-Path $nodeDir 'npm.cmd')) {
    $env:PATH = "$nodeDir;$env:PATH"
}
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) {
    throw "Node.js/npm not found. Install Node 24 or add 'C:\Program Files\nodejs' to PATH."
}
& $npm.Source run dev -- --hostname 127.0.0.1
