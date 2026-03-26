# build.ps1
# Full Windows build: setup embedded Python + npm build + electron-builder NSIS
# Usage: .\scripts\build.ps1

$ErrorActionPreference = "Stop"
$Root = Join-Path $PSScriptRoot ".."

Write-Host "==> Step 1: Setup embedded Python" -ForegroundColor Cyan
& "$PSScriptRoot\setup-python-embed.ps1"

Write-Host ""
Write-Host "==> Step 2: Copy backend code to python-backend/backend/" -ForegroundColor Cyan
$BackendSrc = Join-Path $Root "backend"
$BackendDst = Join-Path $Root "python-backend\backend"
if (Test-Path $BackendDst) { Remove-Item -Recurse -Force $BackendDst }
Copy-Item -Recurse -Force $BackendSrc $BackendDst
# Remove pycache
Get-ChildItem -Recurse -Filter "__pycache__" $BackendDst | Remove-Item -Recurse -Force

Write-Host ""
Write-Host "==> Step 3: Build Vue3 frontend" -ForegroundColor Cyan
Set-Location (Join-Path $Root "frontend\vue-app")
npm run build

Write-Host ""
Write-Host "==> Step 4: Run electron-builder" -ForegroundColor Cyan
Set-Location (Join-Path $Root "frontend\vue-app")
npx electron-builder --win

Write-Host ""
Write-Host "==> Build complete! Check frontend/vue-app/dist-electron/ for output." -ForegroundColor Green
