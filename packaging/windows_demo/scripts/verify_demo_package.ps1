param([switch]$Running)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { throw "Run install_demo.cmd first." }
& $Python (Join-Path $PSScriptRoot "verify_demo_package.py")
if ($LASTEXITCODE -ne 0) { throw "Static package verification failed." }
if ($Running) {
    $BackendPort = if ($env:KIP_BACKEND_PORT) { [int]$env:KIP_BACKEND_PORT } else { 8000 }
    $FrontendPort = if ($env:KIP_FRONTEND_PORT) { [int]$env:KIP_FRONTEND_PORT } else { 5001 }
    $Health = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$BackendPort/health" -TimeoutSec 5
    $Frontend = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$FrontendPort" -TimeoutSec 5
    $Tracks = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$FrontendPort/api/v1/tracks" -TimeoutSec 5
    if ($Health.StatusCode -ne 200 -or $Frontend.StatusCode -ne 200 -or $Tracks.StatusCode -ne 200) {
        throw "Running service verification failed."
    }
    Write-Output "RUNNING_VERIFY_OK health=200 frontend=200 public_api=200"
}
