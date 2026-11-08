@echo off
chcp 65001 >nul
title 开放 8080 端口（局域网访问）

:: 判断是否已经是管理员
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 需要管理员权限，正在请求授权...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ========================================
echo   为「知屿校园」开放 8080 端口
echo ========================================
echo.

netsh advfirewall firewall delete rule name="知屿校园-8080" >nul 2>&1

netsh advfirewall firewall add rule ^
    name="知屿校园-8080" ^
    dir=in ^
    action=allow ^
    protocol=TCP ^
    localport=8080 ^
    profile=any

if %errorlevel% equ 0 (
    echo.
    echo [成功] 8080 端口已放行。
    echo.
    echo 现在同一 WiFi 下的电脑/手机可以访问：
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
        for /f "tokens=1" %%b in ("%%a") do echo     http://%%b:8080
    )
    echo.
    echo 注意：必须先把后端服务启动起来（双击 启动服务.bat）。
) else (
    echo.
    echo [失败] 没能添加规则，请确认你是管理员。
)

echo.
pause
