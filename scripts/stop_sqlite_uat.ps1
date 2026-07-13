param([switch]$RemoveLogs)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $Root "tmp\uat_runtime"

function Stop-OwnedTree([string]$PidFile, [string]$ExpectedCommand) {
    if (-not (Test-Path -LiteralPath $PidFile)) { return }
    $rootPid = [int](Get-Content -LiteralPath $PidFile -Raw)
    $rootProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $rootPid" -ErrorAction SilentlyContinue
    if ($rootProcess) {
        if (-not $rootProcess.CommandLine -or $rootProcess.CommandLine -notmatch $ExpectedCommand) {
            throw "PID $rootPid does not belong to the expected UAT process; it was not stopped."
        }
        $all = @(Get-CimInstance Win32_Process)
        $ids = [Collections.Generic.List[int]]::new()
        $frontier = @($rootPid)
        while ($frontier.Count -gt 0) {
            $next = @()
            foreach ($parentId in $frontier) {
                foreach ($child in $all | Where-Object { $_.ParentProcessId -eq $parentId }) {
                    $ids.Add([int]$child.ProcessId)
                    $next += [int]$child.ProcessId
                }
            }
            $frontier = $next
        }
        $stopIds = $ids.ToArray()
        [array]::Reverse($stopIds)
        foreach ($id in $stopIds) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
        Stop-Process -Id $rootPid -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $PidFile -Force
}

Stop-OwnedTree (Join-Path $RuntimeDir "frontend.pid") "http\.server"
Stop-OwnedTree (Join-Path $RuntimeDir "backend.pid") "uvicorn.*app\.main:app"

if ($RemoveLogs -and (Test-Path -LiteralPath $RuntimeDir)) {
    Get-ChildItem -LiteralPath $RuntimeDir -File | Where-Object { $_.Extension -eq ".log" } | Remove-Item -Force
}
if ((Test-Path -LiteralPath $RuntimeDir) -and -not (Get-ChildItem -LiteralPath $RuntimeDir -Force)) {
    Remove-Item -LiteralPath $RuntimeDir -Force
}
Write-Output "SQLite UAT services stopped."
