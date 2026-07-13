param(
    [int]$BackendPort = $(if ($env:KIP_UAT_BACKEND_PORT) { [int]$env:KIP_UAT_BACKEND_PORT } else { 8000 }),
    [int]$FlutterPort = $(if ($env:KIP_UAT_FLUTTER_PORT) { [int]$env:KIP_UAT_FLUTTER_PORT } else { 5001 })
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$UatDb = Join-Path $BackendDir "kip_uat.db"
$RuntimeDir = Join-Path $Root "tmp\uat_runtime"
$BackendPidFile = Join-Path $RuntimeDir "backend.pid"
$FlutterPidFile = Join-Path $RuntimeDir "frontend.pid"
$BackendLog = Join-Path $RuntimeDir "backend.log"
$BackendErrorLog = Join-Path $RuntimeDir "backend.error.log"
$FlutterLog = Join-Path $RuntimeDir "flutter.log"
$FlutterErrorLog = Join-Path $RuntimeDir "flutter.error.log"

function Assert-PortAvailable([int]$Port) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        throw "Port $Port is already in use. Set KIP_UAT_BACKEND_PORT or KIP_UAT_FLUTTER_PORT."
    }
}

function Wait-Http([string]$Url, [int]$TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    throw "Timed out waiting for $Url"
}

if (-not (Test-Path -LiteralPath $UatDb)) { throw "UAT database not found: backend/kip_uat.db" }
if (-not $env:KIP_UAT_ADMIN_EMAIL -or -not $env:KIP_UAT_ADMIN_PASSWORD) {
    throw "KIP_UAT_ADMIN_EMAIL and KIP_UAT_ADMIN_PASSWORD are required."
}
if ((Test-Path $BackendPidFile) -or (Test-Path $FlutterPidFile)) {
    throw "UAT PID files already exist. Run scripts\stop_sqlite_uat.ps1 first."
}
Assert-PortAvailable $BackendPort
Assert-PortAvailable $FlutterPort
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$PreviousDatabaseUrl = $env:DATABASE_URL
$PreviousJwtSecret = $env:JWT_SECRET_KEY
$JwtSecret = if ($env:KIP_UAT_JWT_SECRET) {
    $env:KIP_UAT_JWT_SECRET
} else {
    [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
}

try {
    $absoluteDb = ($UatDb -replace '\\', '/')
    $env:DATABASE_URL = "sqlite:///$absoluteDb"
    python (Join-Path $PSScriptRoot "prepare_uat_admin.py")
    if ($LASTEXITCODE -ne 0) { throw "Unable to prepare the UAT administrator." }

    $env:DATABASE_URL = "sqlite:///./kip_uat.db"
    $env:JWT_SECRET_KEY = $JwtSecret
    $backendCommand = "Set-Location -LiteralPath '$BackendDir'; python -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort"
    $backend = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-NonInteractive", "-Command", $backendCommand) -WindowStyle Hidden -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendErrorLog -PassThru
    Set-Content -LiteralPath $BackendPidFile -Value $backend.Id -NoNewline
    Wait-Http "http://127.0.0.1:$BackendPort/health" 60

    $flutter = (Get-Command flutter).Source
    Push-Location $FrontendDir
    try {
        & $flutter build web --no-pub --dart-define=KIP_API_BASE_URL=http://127.0.0.1:$BackendPort
        if ($LASTEXITCODE -ne 0) { throw "Flutter Web build failed." }
    } finally {
        Pop-Location
    }
    $flutterCommand = "Set-Location -LiteralPath '$FrontendDir\build\web'; python -m http.server $FlutterPort --bind 127.0.0.1"
    $frontend = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-NonInteractive", "-Command", $flutterCommand) -WindowStyle Hidden -RedirectStandardOutput $FlutterLog -RedirectStandardError $FlutterErrorLog -PassThru
    Set-Content -LiteralPath $FlutterPidFile -Value $frontend.Id -NoNewline
    Wait-Http "http://127.0.0.1:$FlutterPort" 180

    Write-Output "SQLite UAT services are ready."
    Write-Output "Backend: http://127.0.0.1:$BackendPort"
    Write-Output "Flutter: http://127.0.0.1:$FlutterPort"
} catch {
    & (Join-Path $PSScriptRoot "stop_sqlite_uat.ps1")
    throw
} finally {
    $env:DATABASE_URL = $PreviousDatabaseUrl
    $env:JWT_SECRET_KEY = $PreviousJwtSecret
}
