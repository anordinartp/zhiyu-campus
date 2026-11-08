@echo off
chcp 65001 >nul
title 知屿校园 - 后端服务

echo ========================================
echo   知屿校园 后端启动器
echo ========================================
echo.

cd /d "%~dp0backend"

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 没找到 python，请先安装 Python 3.10+ 并勾选 Add to PATH
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] 创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
) else (
    echo [1/3] 虚拟环境已存在
)

echo [2/3] 安装依赖（用阿里云镜像，比较快）...
.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check ^
  -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络
    pause
    exit /b 1
)

echo [3/3] 启动服务...
echo.
echo   本机访问：  http://127.0.0.1:8080
echo   同学访问：  http://你的IP:8080（需同一局域网并放行防火墙）
echo.
echo   关闭这个窗口 = 停止服务
echo ========================================
echo.

.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8080

echo.
echo 服务已停止
pause
