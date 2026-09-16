$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Join-Path $PSScriptRoot 'frontend')
npm.cmd run dev -- --hostname 127.0.0.1
