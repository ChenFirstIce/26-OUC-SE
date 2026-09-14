$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    python -m venv (Join-Path $ProjectRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' }
}
& $Python -m pip install -r (Join-Path $ProjectRoot 'server\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed' }
$ErrorActionPreference = 'Continue'
foreach ($Directory in @('admin-web', 'patient-web\c2b\Frontend')) {
    npm ci --prefix (Join-Path $ProjectRoot $Directory)
    if ($LASTEXITCODE -ne 0) { throw "npm ci failed: $Directory" }
}
Write-Host '初始化完成。运行 .\scripts\start.ps1 启动系统。' -ForegroundColor Green
