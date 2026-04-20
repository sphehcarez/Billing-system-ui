param(
    [int]$FrontendPort = 8000,
    [int]$BackendPort = 8001,
    [switch]$StopExisting
)

$ErrorActionPreference = "Stop"

function Test-UrlReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        Invoke-WebRequest -UseBasicParsing $Url | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Wait-ForUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$Attempts = 40,
        [int]$DelayMilliseconds = 750
    )

    for ($attempt = 0; $attempt -lt $Attempts; $attempt++) {
        if (Test-UrlReady -Url $Url) {
            return $true
        }
        Start-Sleep -Milliseconds $DelayMilliseconds
    }
    return $false
}

$scriptRoot = $PSScriptRoot
$uiRoot = Split-Path -Parent $scriptRoot
$repoRoot = Split-Path -Parent $uiRoot
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$backendDir = Join-Path $uiRoot "backend"
$backendScript = Join-Path $backendDir "main.py"
$frontendLog = Join-Path $repoRoot "frontend.local.log"
$frontendErr = Join-Path $repoRoot "frontend.local.err.log"
$backendLog = Join-Path $repoRoot "backend.local.log"
$backendErr = Join-Path $repoRoot "backend.local.err.log"
$tunnelScript = Join-Path $scriptRoot "start_share_tunnels.ps1"

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment not found at $pythonExe"
}

if ($StopExisting) {
    Get-Process ssh -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1
}

$frontendReady = Test-UrlReady -Url "http://localhost:$FrontendPort/"
$backendReady = Test-UrlReady -Url "http://localhost:$BackendPort/health"

if (-not $backendReady) {
    foreach ($file in @($backendLog, $backendErr)) {
        if (Test-Path $file) {
            Remove-Item -LiteralPath $file -Force
        }
    }
    Start-Process -FilePath $pythonExe `
        -ArgumentList @("main.py") `
        -WorkingDirectory $backendDir `
        -RedirectStandardOutput $backendLog `
        -RedirectStandardError $backendErr | Out-Null

    if (-not (Wait-ForUrl -Url "http://localhost:$BackendPort/health")) {
        throw "Backend did not start on http://localhost:$BackendPort/health. Check $backendLog and $backendErr"
    }
}

if (-not $frontendReady) {
    foreach ($file in @($frontendLog, $frontendErr)) {
        if (Test-Path $file) {
            Remove-Item -LiteralPath $file -Force
        }
    }
    Start-Process -FilePath $pythonExe `
        -ArgumentList @("-m", "http.server", "$FrontendPort") `
        -WorkingDirectory $uiRoot `
        -RedirectStandardOutput $frontendLog `
        -RedirectStandardError $frontendErr | Out-Null

    if (-not (Wait-ForUrl -Url "http://localhost:$FrontendPort/")) {
        throw "Frontend did not start on http://localhost:$FrontendPort/. Check $frontendLog and $frontendErr"
    }
}

Write-Host ""
Write-Host "Local services are ready."
Write-Host "Frontend: http://localhost:$FrontendPort/"
Write-Host "Backend:  http://localhost:$BackendPort/health"
Write-Host ""

& $tunnelScript -FrontendPort $FrontendPort -BackendPort $BackendPort -StopExisting:$StopExisting
