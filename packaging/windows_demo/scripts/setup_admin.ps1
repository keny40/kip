$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { throw "Run install_demo.cmd first." }
$Email = if ($env:KIP_DEMO_ADMIN_EMAIL) { $env:KIP_DEMO_ADMIN_EMAIL } else { Read-Host "Administrator email" }
if ($env:KIP_DEMO_ADMIN_PASSWORD) {
    & $Python (Join-Path $PSScriptRoot "create_demo_admin.py") --email $Email --password-env KIP_DEMO_ADMIN_PASSWORD
} else {
    & $Python (Join-Path $PSScriptRoot "create_demo_admin.py") --email $Email
}
if ($LASTEXITCODE -ne 0) { throw "Administrator setup failed." }
Write-Output "Administrator setup completed. The password was not logged."
