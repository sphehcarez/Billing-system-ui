param(
    [int]$FrontendPort = 8000,
    [int]$BackendPort = 8001,
    [switch]$StopExisting
)

$ErrorActionPreference = "Stop"

function Start-LocalhostRunTunnel {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [Parameter(Mandatory = $true)]
        [string]$LogRoot
    )

    $outLog = Join-Path $LogRoot "$Name-tunnel.out.log"
    $errLog = Join-Path $LogRoot "$Name-tunnel.err.log"

    foreach ($file in @($outLog, $errLog)) {
        if (Test-Path $file) {
            Remove-Item -LiteralPath $file -Force
        }
    }

    $process = Start-Process -FilePath "ssh.exe" `
        -ArgumentList @(
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "-R", "80:localhost:$Port",
            "nokey@localhost.run"
        ) `
        -RedirectStandardOutput $outLog `
        -RedirectStandardError $errLog `
        -PassThru

    $url = $null
    for ($attempt = 0; $attempt -lt 30 -and -not $url; $attempt++) {
        Start-Sleep -Milliseconds 750
        if (Test-Path $outLog) {
            $match = Select-String -Path $outLog -Pattern 'https://[a-z0-9.-]+\.lhr\.life' -AllMatches -ErrorAction SilentlyContinue
            if ($match) {
                $url = $match.Matches[-1].Value
            }
        }
        if ($process.HasExited) {
            break
        }
    }

    [pscustomobject]@{
        Name = $Name
        Port = $Port
        ProcessId = $process.Id
        Url = $url
        OutLog = $outLog
        ErrLog = $errLog
        Running = -not $process.HasExited
    }
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

if ($StopExisting) {
    Get-Process ssh -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1
}

$frontendCheck = $null
$backendCheck = $null
try {
    $frontendCheck = (Invoke-WebRequest -UseBasicParsing "http://localhost:$FrontendPort/").StatusCode
} catch {
    throw "Frontend is not responding on http://localhost:$FrontendPort/. Start the local frontend first."
}

try {
    $backendCheck = Invoke-WebRequest -UseBasicParsing "http://localhost:$BackendPort/health"
} catch {
    throw "Backend is not responding on http://localhost:$BackendPort/health. Start the local backend first."
}

$frontendTunnel = Start-LocalhostRunTunnel -Name "frontend" -Port $FrontendPort -LogRoot $repoRoot
$backendTunnel = Start-LocalhostRunTunnel -Name "backend" -Port $BackendPort -LogRoot $repoRoot

if (-not $frontendTunnel.Url) {
    throw "Frontend tunnel did not return a public URL. Check $($frontendTunnel.OutLog) and $($frontendTunnel.ErrLog)."
}

if (-not $backendTunnel.Url) {
    throw "Backend tunnel did not return a public URL. Check $($backendTunnel.OutLog) and $($backendTunnel.ErrLog)."
}

$encodedApiBase = [uri]::EscapeDataString("$($backendTunnel.Url)/api")
$shareUrl = "$($frontendTunnel.Url)/login.html?apiBase=$encodedApiBase"

Write-Host ""
Write-Host "Frontend URL: $($frontendTunnel.Url)"
Write-Host "Backend URL:  $($backendTunnel.Url)"
Write-Host "Share URL:    $shareUrl"
Write-Host ""
Write-Host "Frontend tunnel PID: $($frontendTunnel.ProcessId)"
Write-Host "Backend tunnel PID:  $($backendTunnel.ProcessId)"
Write-Host ""
Write-Host "Logs:"
Write-Host " - $($frontendTunnel.OutLog)"
Write-Host " - $($frontendTunnel.ErrLog)"
Write-Host " - $($backendTunnel.OutLog)"
Write-Host " - $($backendTunnel.ErrLog)"
