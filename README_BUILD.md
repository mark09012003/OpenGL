# 打包說明

## 使用方式

### Windows
直接雙擊運行 `build.bat`，或在命令提示符中執行：
```bash
build.bat
```

### Linux/Mac
```bash
chmod +x build.sh
./build.sh
```

## 手動打包

如果自動腳本無法運行，可以手動執行：

```bash
# 安裝 PyInstaller（如果尚未安裝）
pip install pyinstaller

# 清理舊文件
rm -rf build dist __pycache__

# 執行打包
pyinstaller build.spec --clean --noconfirm
```

## 打包結果

打包完成後，可執行文件位於：
- Windows: `dist\MapleStoryAutoPrayer.exe`
- Linux/Mac: `dist/MapleStoryAutoPrayer`

## 注意事項

1. **依賴檢查**：確保已安裝所有依賴：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置文件**：`config.json` 會自動包含在打包文件中，首次運行時會自動創建。

3. **圖標**：如需添加應用圖標，請：
   - 準備一個 `.ico` 文件（Windows）或 `.icns` 文件（Mac）
   - 在 `build.spec` 中修改 `icon=None` 為圖標文件路徑

4. **控制台視窗**：當前設置為不顯示控制台視窗（`console=False`）。如需調試，可改為 `console=True`。

5. **文件大小**：打包後的文件可能較大（約 50-100MB），因為包含了 Python 運行時和所有依賴庫。

## 問題排查

如果打包失敗，請檢查：
1. 是否已安裝所有依賴：`pip install -r requirements.txt`
2. 是否已安裝 PyInstaller：`pip install pyinstaller`
3. 查看錯誤訊息，可能需要添加額外的隱藏導入（hiddenimports）


