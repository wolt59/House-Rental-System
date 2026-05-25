# 快速启动后端服务脚本 (Windows PowerShell)
# 使用方法: .\start_backend.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  智能房屋租赁系统 - 后端启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查虚拟环境是否存在
if (-Not (Test-Path ".venv")) {
    Write-Host "错误: 虚拟环境不存在!" -ForegroundColor Red
    Write-Host "请先运行: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# 激活虚拟环境
Write-Host "正在激活虚拟环境..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"

# 检查是否激活成功
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 虚拟环境激活失败!" -ForegroundColor Red
    exit 1
}

Write-Host "虚拟环境激活成功!" -ForegroundColor Green
Write-Host ""

# 从 .env 文件读取端口配置（默认为 8000）
$envFile = ".env"
$port = 8000

if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
    foreach ($line in $envContent) {
        if ($line -match "^BACKEND_PORT=(\d+)$") {
            $port = $matches[1]
            break
        }
    }
}

Write-Host "后端服务配置:" -ForegroundColor Cyan
Write-Host "  - 主机: 0.0.0.0" -ForegroundColor White
Write-Host "  - 端口: $port" -ForegroundColor White
Write-Host "  - 重载模式: 启用" -ForegroundColor White
Write-Host ""

# 启动 uvicorn
Write-Host "正在启动后端服务..." -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --host 0.0.0.0 --port $port --reload
