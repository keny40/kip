$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Requirements = Join-Path $Root "backend\requirements-demo.txt"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (Test-Path -LiteralPath $VenvPython) {
    Write-Output "Demo Python environment is already installed."
    exit 0
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    throw "Python 3.11 or newer was not found. Install Python from python.org and enable Add Python to PATH."
}
$VersionOk = & $Python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 or newer is required." }

Write-Output "Creating the isolated demo environment..."
& $Python.Source -m venv (Join-Path $Root ".venv")
if ($LASTEXITCODE -ne 0) { throw "Unable to create the Python virtual environment." }
& $VenvPython -m pip install --disable-pip-version-check -r $Requirements 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "install.log")
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed. Check logs\install.log." }
Write-Output "Installation completed. Next, run scripts\setup_admin.ps1 and start_demo.cmd."
