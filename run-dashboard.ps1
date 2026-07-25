$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dashboardRoot = Join-Path $projectRoot "dashboard"

Set-Location -LiteralPath $dashboardRoot

if (-not (Test-Path -LiteralPath "node_modules")) {
    Write-Host "Installing dashboard dependencies..."
    npm install
}

Write-Host "Starting Süper Lig Forecast Lab at http://localhost:3000"
npm run dev -- --host 127.0.0.1 --port 3000
