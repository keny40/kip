param([switch]$Quiet)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Runtime = Join-Path $Root "runtime"

function Stop-OwnedProcess([string]$PidFile, [string]$Expected) {
    if (-not (Test-Path -LiteralPath $PidFile)) { return }
    $Id = [int](Get-Content -LiteralPath $PidFile -Raw)
    $Process = Get-CimInstance Win32_Process -Filter "ProcessId = $Id" -ErrorAction SilentlyContinue
    if ($Process) {
        if (-not $Process.CommandLine -or $Process.CommandLine -notmatch $Expected) {
            throw "PID $Id is not an expected KIP demo process and was not stopped."
        }
        Stop-Process -Id $Id -Force
    }
    Remove-Item -LiteralPath $PidFile -Force
}

Stop-OwnedProcess (Join-Path $Runtime "frontend.pid") "serve_demo_frontend\.py"
Stop-OwnedProcess (Join-Path $Runtime "backend.pid") "run_demo_backend\.py"
if ((Test-Path -LiteralPath $Runtime) -and -not (Get-ChildItem -LiteralPath $Runtime -Force)) {
    Remove-Item -LiteralPath $Runtime -Force
}
if (-not $Quiet) { Write-Output "KIP SQLite demo stopped. Other Python and browser processes were not touched." }
