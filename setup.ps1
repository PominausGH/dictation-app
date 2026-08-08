#Requires -Version 5.1
<#
  Voxtty setup for Windows — creates a venv, installs dependencies, and
  registers a Task Scheduler task so Voxtty starts on login.

  Mirrors setup.sh's structure. Run via setup.bat (recommended) or directly:
    powershell -ExecutionPolicy Bypass -File setup.ps1
#>

$ErrorActionPreference = "Stop"
$InstallDir = $PSScriptRoot

Write-Host "=== Voxtty Setup (Windows) ==="

# [1/5] Python virtual environment + dependencies
Write-Host "[1/5] Creating Python virtual environment..."
Set-Location $InstallDir
python -m venv venv
$venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"
$venvPythonw = Join-Path $InstallDir "venv\Scripts\pythonw.exe"

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

# openwakeword's tflite-runtime dependency has no current-Python wheels, so a
# plain install fails; pull it in separately with --no-deps + its real deps
# (falls back to onnxruntime at import time when tflite_runtime is absent).
# Same workaround as setup.sh and packaging/aur/PKGBUILD.
& $venvPython -m pip install --no-deps "openwakeword>=0.6.0"
& $venvPython -m pip install "onnxruntime>=1.10.0,<2" "scipy>=1.3,<2" "scikit-learn>=1,<2" "requests>=2.0,<3" "tqdm>=4.0,<5.0"

# [2/5] Resolve OS-correct config dir (single source of truth stays in Python/platformdirs)
Write-Host "[2/5] Resolving config directory..."
$configDir = (& $venvPython -c "import platformdirs; print(platformdirs.user_config_dir('voxtty', appauthor=False))").Trim()
New-Item -ItemType Directory -Force -Path $configDir | Out-Null

# [3/5] API key template (for optional AI cleanup)
Write-Host "[3/5] Setting up AI cleanup config..."
$envFile = Join-Path $configDir "env"
if (-not (Test-Path $envFile)) {
    @"
# Optional: enables the AI cleanup pass (set cleanup_enabled=true in config.json).
# Paste your Anthropic API key after the = sign, then restart Voxtty.
ANTHROPIC_API_KEY=
"@ | Set-Content -Path $envFile -Encoding UTF8
    Write-Host "  Created $envFile (add your API key there to enable AI cleanup)."
}

# [4/5] Register the Task Scheduler autostart task
Write-Host "[4/5] Installing autostart task..."
$taskXmlTemplate = Join-Path $InstallDir "packaging\windows\voxtty-task.xml"
$taskXmlRendered = Join-Path $env:TEMP "voxtty-task-rendered.xml"

(Get-Content $taskXmlTemplate -Raw) `
    -replace "__VOXTTY_INSTALL_DIR__", $InstallDir `
    -replace "__VOXTTY_PYTHONW__", $venvPythonw |
    Set-Content -Path $taskXmlRendered -Encoding Unicode

schtasks /Create /TN Voxtty /XML $taskXmlRendered /F | Out-Null
Remove-Item $taskXmlRendered

# [5/5] Start it now
Write-Host "[5/5] Starting Voxtty..."
schtasks /Run /TN Voxtty | Out-Null

Write-Host ""
Write-Host "=== Setup Complete ==="
Write-Host ""
Write-Host "Task management:"
Write-Host "  schtasks /Query /TN Voxtty      # check status"
Write-Host "  schtasks /End /TN Voxtty        # stop"
Write-Host "  schtasks /Run /TN Voxtty        # start"
Write-Host ""
Write-Host "Logs saved under: $(& $venvPython -c "import platformdirs; print(platformdirs.user_data_dir('voxtty', appauthor=False))")"
Write-Host ""
Write-Host "Press Alt+D to toggle dictation on/off."
