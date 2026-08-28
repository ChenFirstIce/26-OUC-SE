$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Write-Host '[1/2] 后端接口与权限测试' -ForegroundColor Cyan
Push-Location (Join-Path $ProjectRoot 'backend')
try { python -m pytest -q } finally { Pop-Location }
Write-Host '[2/2] 前端类型检查与生产构建' -ForegroundColor Cyan
npm run build --prefix (Join-Path $ProjectRoot 'frontend')
Write-Host '全部检查通过。' -ForegroundColor Green

