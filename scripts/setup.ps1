$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host '[1/4] 检查 Python...' -ForegroundColor Cyan
python --version
Write-Host '[2/4] 安装后端依赖...' -ForegroundColor Cyan
python -m pip install -r (Join-Path $ProjectRoot 'backend\requirements.txt')
Write-Host '[3/4] 检查 Node.js 并安装前端依赖...' -ForegroundColor Cyan
node --version
npm install --prefix (Join-Path $ProjectRoot 'frontend')
Write-Host '[4/4] 执行首次后端健康检查和种子初始化...' -ForegroundColor Cyan
Push-Location (Join-Path $ProjectRoot 'backend')
try {
    python -c "from app.main import initialize_database; initialize_database(); print('database initialized')"
} finally {
    Pop-Location
}
Write-Host '初始化完成。运行 .\scripts\start.ps1 启动系统。' -ForegroundColor Green
