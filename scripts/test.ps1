$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Write-Host '[1/2] 后端接口与权限测试' -ForegroundColor Cyan
Push-Location (Join-Path $ProjectRoot 'server')
try {
    & (Join-Path $ProjectRoot '.venv\Scripts\python.exe') -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed' }
} finally { Pop-Location }
Write-Host '[2/2] 前端类型检查与生产构建' -ForegroundColor Cyan
# Windows PowerShell treats npm warnings on stderr as errors when redirected.
# Native command success is determined by its exit code below.
$ErrorActionPreference = 'Continue'
npm run build --prefix (Join-Path $ProjectRoot 'admin-web')
if ($LASTEXITCODE -ne 0) { throw 'Admin build failed' }
Write-Host '全部检查通过。' -ForegroundColor Green
