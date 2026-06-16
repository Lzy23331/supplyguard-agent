$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\.."
$venvPath = Join-Path $projectRoot ".venv"
$pythonPath = Join-Path $venvPath "Scripts\python.exe"
$requirements = Join-Path $projectRoot "backend\requirements.txt"

if (-not (Test-Path $pythonPath)) {
  py -3 -m venv $venvPath
}

& $pythonPath -m pip install --upgrade pip
& $pythonPath -m pip install -r $requirements

Write-Host "后端独立虚拟环境已准备完成：$venvPath"
Write-Host "启动后端：.\scripts\start-backend.ps1"
