$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $ProjectRoot '.runtime'
foreach ($Name in @('backend', 'frontend')) {
    $PidFile = Join-Path $RuntimeDir "$Name.pid"
    if (Test-Path -LiteralPath $PidFile) {
        $ProcessId = [int](Get-Content -LiteralPath $PidFile -Raw)
        $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($Process) {
            Stop-Process -Id $ProcessId
            Write-Host "已停止 $Name (PID $ProcessId)"
        }
        Remove-Item -LiteralPath $PidFile -Force
    }
}

