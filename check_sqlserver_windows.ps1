# Windows SQL Server 配置检查脚本
# 用于检查 SQL Server 是否已正确配置以允许 Docker 容器连接

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "SQL Server 远程连接配置检查" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 SQL Server 服务是否运行
Write-Host "1. 检查 SQL Server 服务状态..." -ForegroundColor Yellow
$sqlService = Get-Service -Name "MSSQLSERVER" -ErrorAction SilentlyContinue
if ($sqlService) {
    if ($sqlService.Status -eq "Running") {
        Write-Host "   ✓ SQL Server 服务正在运行" -ForegroundColor Green
    } else {
        Write-Host "   ✗ SQL Server 服务未运行，状态: $($sqlService.Status)" -ForegroundColor Red
        Write-Host "   请启动 SQL Server 服务" -ForegroundColor Red
    }
} else {
    Write-Host "   ✗ 未找到 SQL Server 服务" -ForegroundColor Red
    Write-Host "   请确保已安装 SQL Server" -ForegroundColor Red
}

# 检查防火墙规则
Write-Host ""
Write-Host "2. 检查防火墙规则..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "SQL Server 1433" -ErrorAction SilentlyContinue
if ($firewallRule) {
    Write-Host "   ✓ 找到防火墙规则: SQL Server 1433" -ForegroundColor Green
} else {
    Write-Host "   ⚠ 未找到防火墙规则，可能需要手动添加" -ForegroundColor Yellow
    Write-Host "   建议添加规则允许端口 1433 的入站连接" -ForegroundColor Yellow
}

# 获取本机 IP 地址
Write-Host ""
Write-Host "3. 获取本机 IP 地址（供 Docker 配置使用）..." -ForegroundColor Yellow
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -ExpandProperty IPAddress
if ($ipAddresses) {
    Write-Host "   本机 IP 地址（请配置到 Docker 的 config.ini 中）：" -ForegroundColor Green
    foreach ($ip in $ipAddresses) {
        Write-Host "     - $ip" -ForegroundColor Green
    }
} else {
    Write-Host "   ⚠ 无法获取 IP 地址" -ForegroundColor Yellow
}

# 检查 SQL Server 是否监听 1433 端口
Write-Host ""
Write-Host "4. 检查 SQL Server 端口监听..." -ForegroundColor Yellow
$listening = Get-NetTCPConnection -LocalPort 1433 -State Listen -ErrorAction SilentlyContinue
if ($listening) {
    Write-Host "   ✓ SQL Server 正在监听端口 1433" -ForegroundColor Green
} else {
    Write-Host "   ✗ SQL Server 未监听端口 1433" -ForegroundColor Red
    Write-Host "   请检查 SQL Server Configuration Manager 中的 TCP/IP 协议配置" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "配置建议：" -ForegroundColor Cyan
Write-Host "1. 打开 SQL Server Configuration Manager" -ForegroundColor White
Write-Host "2. 启用 TCP/IP 协议" -ForegroundColor White
Write-Host "3. 确保端口 1433 已配置" -ForegroundColor White
Write-Host "4. 重启 SQL Server 服务" -ForegroundColor White
Write-Host "5. 在 SQL Server Management Studio 中启用 SQL Server 身份验证" -ForegroundColor White
Write-Host "6. 创建用于 Docker 连接的用户（如果使用 SQL Server 身份验证）" -ForegroundColor White
Write-Host "7. 配置 Windows 防火墙允许端口 1433" -ForegroundColor White
Write-Host ""
Write-Host "详细说明请参考 DOCKER_DEPLOY.md" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

