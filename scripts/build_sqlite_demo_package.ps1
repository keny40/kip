param([switch]$SkipFlutterBuild)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DistRoot = [IO.Path]::GetFullPath((Join-Path $Root "dist"))
$Target = [IO.Path]::GetFullPath((Join-Path $DistRoot "kip-sqlite-demo"))
$Workspace = [IO.Path]::GetFullPath($Root)
if (-not $Target.StartsWith($Workspace + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe distribution target."
}
if (Test-Path -LiteralPath $Target) {
    Remove-Item -LiteralPath $Target -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $Target | Out-Null

if (-not $SkipFlutterBuild) {
    $Flutter = (Get-Command flutter -ErrorAction Stop).Source
    Push-Location (Join-Path $Root "frontend")
    try {
        & $Flutter build web --release --no-pub "--dart-define=KIP_API_BASE_URL="
        if ($LASTEXITCODE -ne 0) { throw "Flutter release build failed." }
    } finally {
        Pop-Location
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $Root "frontend\build\web\index.html"))) {
    throw "Flutter Web build output is missing."
}

Copy-Item -Path (Join-Path $Root "packaging\windows_demo\*") -Destination $Target -Recurse
New-Item -ItemType Directory -Force -Path (Join-Path $Target "backend"),(Join-Path $Target "frontend"),(Join-Path $Target "data"),(Join-Path $Target "logs"),(Join-Path $Target "runtime"),(Join-Path $Target "samples") | Out-Null
Copy-Item -LiteralPath (Join-Path $Root "backend\app") -Destination (Join-Path $Target "backend\app") -Recurse
Copy-Item -LiteralPath (Join-Path $Root "backend\alembic") -Destination (Join-Path $Target "backend\alembic") -Recurse
Copy-Item -LiteralPath (Join-Path $Root "backend\alembic.ini") -Destination (Join-Path $Target "backend\alembic.ini")
Copy-Item -LiteralPath (Join-Path $Root "backend\requirements-demo.txt") -Destination (Join-Path $Target "backend\requirements-demo.txt")
Copy-Item -Path (Join-Path $Root "frontend\build\web\*") -Destination (Join-Path $Target "frontend") -Recurse
Copy-Item -Path (Join-Path $Root "samples\*.csv") -Destination (Join-Path $Target "samples")
foreach ($Name in "create_sqlite_demo_db.py","create_demo_admin.py","serve_demo_frontend.py","verify_demo_package.py","run_demo_backend.py") {
    Copy-Item -LiteralPath (Join-Path $Root "scripts\$Name") -Destination (Join-Path $Target "scripts\$Name")
}

$SourceMaps = @(Get-ChildItem -LiteralPath $Target -Recurse -File -Filter "*.map")
if ($SourceMaps) { throw "Source map files were found in the release package." }
$WasmSymbols = @(Get-ChildItem -LiteralPath $Target -Recurse -File -Filter "*.symbols")
foreach ($Symbol in $WasmSymbols) {
    $Resolved = [IO.Path]::GetFullPath($Symbol.FullName)
    if (-not $Resolved.StartsWith($Target + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe symbol cleanup target."
    }
    Remove-Item -LiteralPath $Resolved -Force
}

$Commit = (git -C $Root rev-parse --short=12 HEAD).Trim()
Set-Content -LiteralPath (Join-Path $Target "VERSION") -Value "0.1.0-sqlite-demo+$Commit" -Encoding ascii

& python (Join-Path $Target "scripts\create_sqlite_demo_db.py")
if ($LASTEXITCODE -ne 0) { throw "Demo database creation failed." }

$CacheDirs = @(Get-ChildItem -LiteralPath $Target -Recurse -Directory -Filter "__pycache__")
foreach ($Directory in $CacheDirs) {
    $Resolved = [IO.Path]::GetFullPath($Directory.FullName)
    if (-not $Resolved.StartsWith($Target + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe cache cleanup target."
    }
    Remove-Item -LiteralPath $Resolved -Recurse -Force
}
Get-ChildItem -LiteralPath $Target -Recurse -File -Filter "*.pyc" | Remove-Item -Force

& python (Join-Path $Target "scripts\verify_demo_package.py")
if ($LASTEXITCODE -ne 0) { throw "Built package verification failed." }
$Size = (Get-ChildItem -LiteralPath $Target -Recurse -File | Measure-Object -Property Length -Sum).Sum
$Archive = [IO.Path]::GetFullPath((Join-Path $DistRoot "kip-sqlite-demo.zip"))
if (-not $Archive.StartsWith($DistRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe demo archive target."
}
if (Test-Path -LiteralPath $Archive) { Remove-Item -LiteralPath $Archive -Force }
& tar.exe -a -c -f $Archive -C $DistRoot (Split-Path -Leaf $Target)
if ($LASTEXITCODE -ne 0) { throw "Demo ZIP creation failed." }
$ArchiveSize = (Get-Item -LiteralPath $Archive).Length
Write-Output "DEMO_PACKAGE_READY files=$((Get-ChildItem -LiteralPath $Target -Recurse -File).Count) bytes=$Size archive_bytes=$ArchiveSize"
