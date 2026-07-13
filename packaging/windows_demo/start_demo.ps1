param([switch]$NoBrowser)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$BackendPort = if ($env:KIP_BACKEND_PORT) { [int]$env:KIP_BACKEND_PORT } else { 8000 }
$FrontendPort = if ($env:KIP_FRONTEND_PORT) { [int]$env:KIP_FRONTEND_PORT } else { 5001 }
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Database = Join-Path $Root "data\kip_demo.db"
$Runtime = Join-Path $Root "runtime"
$Logs = Join-Path $Root "logs"
$BackendPid = Join-Path $Runtime "backend.pid"
$FrontendPid = Join-Path $Runtime "frontend.pid"
$LauncherLog = Join-Path $Logs "launcher.log"

function Write-Launcher([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Add-Content -LiteralPath $LauncherLog -Value $line
    Write-Output $Message
}
function Rotate-Log([string]$Path) {
    if ((Test-Path -LiteralPath $Path) -and (Get-Item -LiteralPath $Path).Length -gt 5MB) {
        $Previous = "$Path.1"
        if (Test-Path -LiteralPath $Previous) { Remove-Item -LiteralPath $Previous -Force }
        Move-Item -LiteralPath $Path -Destination $Previous
    }
}
function Assert-Port([int]$Port, [string]$Variable) {
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $Port is already in use. Set $Variable to another port; no existing process was stopped."
    }
}
function Wait-Url([string]$Url, [int]$Seconds) {
    $Deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $Deadline) {
        try {
            $Response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
            if ($Response.StatusCode -eq 200) { return }
        } catch { Start-Sleep -Milliseconds 400 }
    }
    throw "A demo service did not become ready in time. Check the logs folder."
}

New-Item -ItemType Directory -Force -Path $Runtime,$Logs | Out-Null
foreach ($Log in "backend.log","backend.error.log","frontend.log","frontend.error.log","launcher.log") {
    Rotate-Log (Join-Path $Logs $Log)
}
if (-not (Test-Path -LiteralPath $Python)) { throw "Demo runtime is not installed. Run install_demo.cmd first." }
if (-not (Test-Path -LiteralPath $Database)) { throw "Demo database is missing. Run scripts\reset_demo.ps1." }
if ((Test-Path -LiteralPath $BackendPid) -or (Test-Path -LiteralPath $FrontendPid)) {
    throw "Demo PID files already exist. Run stop_demo.cmd first."
}
Assert-Port $BackendPort "KIP_BACKEND_PORT"
Assert-Port $FrontendPort "KIP_FRONTEND_PORT"

$OldDatabaseUrl = $env:DATABASE_URL
$OldJwt = $env:JWT_SECRET_KEY
$OldEnvironment = $env:ENVIRONMENT
$OldCors = $env:CORS_ORIGINS
try {
    $env:DATABASE_URL = "sqlite:///$($Database.Replace('\','/'))"
    $RandomBytes = New-Object byte[] 48
    $Generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $Generator.GetBytes($RandomBytes) } finally { $Generator.Dispose() }
    $env:JWT_SECRET_KEY = ([BitConverter]::ToString($RandomBytes)).Replace("-", "")
    $env:ENVIRONMENT = "demo"
    $env:CORS_ORIGINS = "http://127.0.0.1:$FrontendPort,http://localhost:$FrontendPort"
    $BackendScript = '"' + (Join-Path $Root "scripts\run_demo_backend.py") + '"'
    $Backend = Start-Process -FilePath $Python -ArgumentList @(
        $BackendScript,"--port","$BackendPort"
    ) -WorkingDirectory $Root -WindowStyle Hidden `
      -RedirectStandardOutput (Join-Path $Logs "backend.log") `
      -RedirectStandardError (Join-Path $Logs "backend.error.log") -PassThru
    Set-Content -LiteralPath $BackendPid -Value $Backend.Id -NoNewline
    Wait-Url "http://127.0.0.1:$BackendPort/health" 60

    $FrontendScript = '"' + (Join-Path $Root "scripts\serve_demo_frontend.py") + '"'
    $FrontendDirectory = '"' + (Join-Path $Root "frontend") + '"'
    $Frontend = Start-Process -FilePath $Python -ArgumentList @(
        $FrontendScript,"--port","$FrontendPort",
        "--backend-port","$BackendPort","--directory",$FrontendDirectory
    ) -WorkingDirectory $Root -WindowStyle Hidden `
      -RedirectStandardOutput (Join-Path $Logs "frontend.log") `
      -RedirectStandardError (Join-Path $Logs "frontend.error.log") -PassThru
    Set-Content -LiteralPath $FrontendPid -Value $Frontend.Id -NoNewline
    Wait-Url "http://127.0.0.1:$FrontendPort" 30
    Write-Launcher "KIP SQLite demo started."
    Write-Output "Backend: http://127.0.0.1:$BackendPort"
    Write-Output "Demo: http://127.0.0.1:$FrontendPort"
    if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$FrontendPort" }
} catch {
    & (Join-Path $Root "stop_demo.ps1") -Quiet
    throw
} finally {
    $env:DATABASE_URL = $OldDatabaseUrl
    $env:JWT_SECRET_KEY = $OldJwt
    $env:ENVIRONMENT = $OldEnvironment
    $env:CORS_ORIGINS = $OldCors
}
