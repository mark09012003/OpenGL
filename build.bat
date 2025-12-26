@echo off
chcp 65001 >nul
echo ========================================
echo MapleStory 自動化助手 - 打包腳本
echo ========================================
echo.

REM 檢查是否安裝了 PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [錯誤] 未安裝 PyInstaller
    echo 正在安裝 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [錯誤] PyInstaller 安裝失敗
        pause
        exit /b 1
    )
)

echo [1/3] 清理舊的構建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo [2/3] 開始打包...
python -m PyInstaller build.spec --clean --noconfirm

if errorlevel 1 (
    echo [錯誤] 打包失敗
    pause
    exit /b 1
)

echo [3/3] 打包完成！
echo.
echo 可執行文件位置: dist\MapleStoryAutoPrayer.exe
echo.
pause

