$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Runtime = Join-Path $Root "runtime"
if (-not (Test-Path -LiteralPath $Python)) { throw "Run install_demo.cmd first." }
if ((Test-Path (Join-Path $Runtime "backend.pid")) -or (Test-Path (Join-Path $Runtime "frontend.pid"))) {
    throw "Stop the demo before resetting it."
}
$Answer = Read-Host "This backs up and replaces only data\kip_demo.db. Type RESET to continue"
if ($Answer -cne "RESET") { Write-Output "Reset canceled."; exit 0 }
& $Python (Join-Path $PSScriptRoot "create_sqlite_demo_db.py") --replace
if ($LASTEXITCODE -ne 0) { throw "Demo reset failed." }
Write-Output "Demo data reset completed. Run scripts\setup_admin.ps1 to create an administrator."
