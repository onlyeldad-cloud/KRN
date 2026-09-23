param([switch]$Dev, [switch]$Rebuild)

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
if ($Dev) {
    & $npm.Source run dev -- --hostname 127.0.0.1 --port 3000
    exit $LASTEXITCODE
}

# Reuse a compiled build so the first click is not waiting on Next.js compilation.
$env:KRN_LOCAL_MODE = 'true'
$env:NEXT_PUBLIC_KRN_REQUIRES_PASSWORD = 'false'
$buildId = Join-Path $PWD '.next\BUILD_ID'
$mustBuild = $Rebuild -or -not (Test-Path -LiteralPath $buildId)
if (-not $mustBuild) {
    $built = (Get-Item -LiteralPath $buildId).LastWriteTimeUtc
    $watch = @('package.json', 'package-lock.json', 'next.config.ts', 'app', 'components', 'lib', 'public')
    foreach ($item in $watch) {
        if (-not (Test-Path -LiteralPath $item)) { continue }
        $info = Get-Item -LiteralPath $item
        if ($info.LastWriteTimeUtc -gt $built) {
            $mustBuild = $true
            break
        }
        if ($info.PSIsContainer) {
            $newer = Get-ChildItem -LiteralPath $item -File -Recurse -ErrorAction SilentlyContinue |
                Where-Object { $_.LastWriteTimeUtc -gt $built } |
                Select-Object -First 1
            if ($newer) {
                $mustBuild = $true
                break
            }
        }
    }
}
if ($mustBuild) {
    Write-Host 'Preparing the web app. This runs only after source changes.'
    & $npm.Source run build -- --no-lint
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
& $npm.Source run start -- --hostname 127.0.0.1 --port 3000
exit $LASTEXITCODE
