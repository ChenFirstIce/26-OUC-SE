$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $ProjectRoot '.runtime'
$BackendDir = Join-Path $ProjectRoot 'backend'
$FrontendDir = Join-Path $ProjectRoot 'frontend'
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

function Assert-PortFree([int]$Port) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) { throw "端口 $Port 已被占用，请先关闭占用程序或执行 stop.ps1。" }
}

Assert-PortFree 8000
Assert-PortFree 5173

$LanAddress = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
    Where-Object {
        $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and
        -not [System.Net.IPAddress]::IsLoopback($_) -and
        $_.IPAddressToString -notlike '169.254.*'
    } |
    Select-Object -First 1 -ExpandProperty IPAddressToString
if (-not $LanAddress) { $LanAddress = '127.0.0.1' }

# 后端创建派发任务时使用该地址生成二维码；子进程会继承此环境变量。
$env:FRONTEND_ORIGIN = "http://${LanAddress}:5173"
$Backend = Start-Process -FilePath python -ArgumentList 'run.py' -WorkingDirectory $BackendDir -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $RuntimeDir 'backend.log') -RedirectStandardError (Join-Path $RuntimeDir 'backend-error.log') -PassThru
$ViteScript = Join-Path $FrontendDir 'node_modules\vite\bin\vite.js'
$Frontend = Start-Process -FilePath node -ArgumentList $ViteScript,'--host','0.0.0.0','--port','5173' -WorkingDirectory $FrontendDir -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $RuntimeDir 'frontend.log') -RedirectStandardError (Join-Path $RuntimeDir 'frontend-error.log') -PassThru

Set-Content -LiteralPath (Join-Path $RuntimeDir 'backend.pid') -Value $Backend.Id
Set-Content -LiteralPath (Join-Path $RuntimeDir 'frontend.pid') -Value $Frontend.Id

$Ready = $false
for ($Attempt = 1; $Attempt -le 20; $Attempt++) {
    Start-Sleep -Milliseconds 500
    try {
        $Health = Invoke-RestMethod 'http://127.0.0.1:8000/health'
        $Front = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5173/'
        if ($Health.status -eq 'ok' -and $Front.StatusCode -eq 200) { $Ready = $true; break }
    } catch { }
}
if (-not $Ready) {
    Write-Host '启动失败，请查看 .runtime\backend-error.log 和 frontend-error.log。' -ForegroundColor Red
    exit 1
}

Write-Host '系统启动成功：' -ForegroundColor Green
Write-Host '医生/管理端: http://127.0.0.1:5173/login'
Write-Host "患者手机端: http://${LanAddress}:5173/p/fill/demo-patient-token"
Write-Host 'Swagger:     http://127.0.0.1:8000/docs'
Write-Host '医生账号: doctor1 / Doctor123!'
Write-Host '管理员:   admin / Admin123!'
Write-Host '患者访问码: 123456'
if ($LanAddress -eq '127.0.0.1') {
    Write-Host '未检测到局域网地址，实体手机扫码暂不可用。' -ForegroundColor Yellow
} else {
    Write-Host '手机需与电脑连接同一局域网；若 Windows 弹出防火墙提示，请允许 Node.js 访问专用网络。' -ForegroundColor Yellow
}
