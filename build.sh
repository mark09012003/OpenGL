#!/bin/bash

echo "========================================"
echo "MapleStory 自動化助手 - 打包腳本"
echo "========================================"
echo ""

# 檢查是否安裝了 PyInstaller
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "[錯誤] 未安裝 PyInstaller"
    echo "正在安裝 PyInstaller..."
    pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "[錯誤] PyInstaller 安裝失敗"
        exit 1
    fi
fi

echo "[1/3] 清理舊的構建文件..."
rm -rf build dist __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

echo "[2/3] 開始打包..."
pyinstaller build.spec --clean --noconfirm

if [ $? -ne 0 ]; then
    echo "[錯誤] 打包失敗"
    exit 1
fi

echo "[3/3] 打包完成！"
echo ""
echo "可執行文件位置: dist/MapleStoryAutoPrayer.exe"
echo ""


