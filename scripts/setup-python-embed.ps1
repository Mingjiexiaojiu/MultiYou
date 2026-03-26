# setup-python-embed.ps1
# Downloads Windows embedded Python and bootstraps pip + project dependencies
# Usage: .\scripts\setup-python-embed.ps1 [-Version 3.11.9]

param(
    [string]$Version = "3.11.9"
)

$ErrorActionPreference = "Stop"

$PythonEmbedDir = Join-Path $PSScriptRoot "..\python-backend\python-embed"
$BackendDir     = Join-Path $PSScriptRoot "..\backend"
$DownloadUrl    = "https://www.python.org/ftp/python/$Version/python-$Version-embed-amd64.zip"
$ZipPath        = Join-Path $env:TEMP "python-embed.zip"

Write-Host "==> Setting up embedded Python $Version for MultiYou packaging" -ForegroundColor Cyan

# 1. Clean and create target directory
if (Test-Path $PythonEmbedDir) {
    Write-Host "    Cleaning existing python-embed directory..."
    Remove-Item -Recurse -Force $PythonEmbedDir
}
New-Item -ItemType Directory -Force -Path $PythonEmbedDir | Out-Null

# 2. Download embedded Python
Write-Host "    Downloading $DownloadUrl ..."
Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath -UseBasicParsing

# 3. Extract
Write-Host "    Extracting to $PythonEmbedDir ..."
Expand-Archive -Path $ZipPath -DestinationPath $PythonEmbedDir -Force
Remove-Item $ZipPath

# 4. Enable site-packages by editing python311._pth
$PthFile = Get-ChildItem $PythonEmbedDir -Filter "python*._pth" | Select-Object -First 1
if ($PthFile) {
    $content = Get-Content $PthFile.FullName
    $content = $content -replace '#import site', 'import site'
    Set-Content -Path $PthFile.FullName -Value $content
    Write-Host "    Enabled site-packages in $($PthFile.Name)"
}

# 5. Bootstrap pip
Write-Host "    Bootstrapping pip..."
$GetPipUrl  = "https://bootstrap.pypa.io/get-pip.py"
$GetPipPath = Join-Path $env:TEMP "get-pip.py"
Invoke-WebRequest -Uri $GetPipUrl -OutFile $GetPipPath -UseBasicParsing
& "$PythonEmbedDir\python.exe" $GetPipPath --no-warn-script-location
Remove-Item $GetPipPath

# 6. Install backend requirements
$RequirementsFile = Join-Path $BackendDir "requirements.txt"
if (Test-Path $RequirementsFile) {
    Write-Host "    Installing backend dependencies from requirements.txt ..."
    & "$PythonEmbedDir\python.exe" -m pip install -r $RequirementsFile --no-warn-script-location
} else {
    Write-Warning "requirements.txt not found at $RequirementsFile — skipping dependency install"
}

Write-Host ""
Write-Host "==> Embedded Python setup complete!" -ForegroundColor Green
Write-Host "    Location: $PythonEmbedDir"
