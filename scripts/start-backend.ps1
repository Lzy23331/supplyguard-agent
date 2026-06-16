$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\.."
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  throw "未找到项目虚拟环境：$venvPython。请先运行 .\scripts\setup-backend-env.ps1"
}

Set-Location (Join-Path $projectRoot "backend")
& $venvPython run.py
