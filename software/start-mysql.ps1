# 启动本项目专用的 MySQL 8.0 实例（3307 端口，独立数据目录）
#
# 设计说明：
#   - 不使用系统服务 MySQL80，避免与机器上已有实例互相干扰，也不需要管理员权限；
#   - 数据目录放在 C:\zhiyu\mysql-data（纯英文路径），因为 MySQL 对中文路径支持不好；
#   - 只监听 127.0.0.1：数据库不对局域网暴露，避免 root 无口令被外部访问；
#   - root 无口令，仅用于本地开发；生产环境必须改口令。
#
# 用法：powershell -ExecutionPolicy Bypass -File .\start-mysql.ps1

$ErrorActionPreference = 'Stop'

$base = 'D:\MySQL\MySQL Server 8.0'
$data = 'C:\zhiyu\mysql-data'
$port = 3307
$outLog = 'C:\zhiyu\mysqld.out.log'
$errLog = 'C:\zhiyu\mysqld.err.log'

if (-not (Test-Path "$base\bin\mysqld.exe")) {
    throw "找不到 mysqld.exe：$base\bin\mysqld.exe"
}

# 已经起来就不重复启动
$probe = & "$base\bin\mysqladmin.exe" -u root --protocol=TCP -P $port -h 127.0.0.1 ping 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Output "MySQL 已在 $port 端口运行，无需重复启动。"
    exit 0
}

if (-not (Test-Path "$data\auto.cnf")) {
    Write-Output "首次运行：初始化数据目录 $data ..."
    New-Item -ItemType Directory -Path $data -Force | Out-Null
    & "$base\bin\mysqld.exe" --no-defaults --initialize-insecure --basedir="$base" --datadir="$data"
    if ($LASTEXITCODE -ne 0) { throw "初始化失败，退出码 $LASTEXITCODE" }
}

Write-Output "启动 mysqld（端口 $port）..."
$argLine = "--no-defaults --basedir=`"$base`" --datadir=`"$data`" --port=$port --bind-address=127.0.0.1 --mysqlx=OFF"
Start-Process -FilePath "$base\bin\mysqld.exe" -ArgumentList $argLine `
    -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $errLog

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    & "$base\bin\mysqladmin.exe" -u root --protocol=TCP -P $port -h 127.0.0.1 ping 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Output "MySQL 已就绪：127.0.0.1:$port"
        exit 0
    }
}
throw "MySQL 启动超时，请查看 $errLog"
