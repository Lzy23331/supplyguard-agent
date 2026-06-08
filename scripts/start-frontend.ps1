$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\.."
$nodePath = Join-Path $projectRoot ".tools\node"

if (-not (Test-Path (Join-Path $nodePath "npm.cmd"))) {
  throw "Portable Node.js was not found at $nodePath. Run npm install with a local Node.js installation first."
}

$env:Path = "$nodePath;$env:Path"
Set-Location (Join-Path $projectRoot "frontend")
npm run dev

