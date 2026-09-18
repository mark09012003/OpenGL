# Windows 打包

此程式使用 Win32 API，請在 **Windows 10/11 x64** 上打包與執行。需要 Python 3.10 以上版本及網路連線以安裝相依套件。

1. 解壓縮整個專案到 Windows 資料夾。
2. 安裝 [Python for Windows](https://www.python.org/downloads/windows/)；安裝時勾選「Add python.exe to PATH」。
3. 雙擊 `build.bat`。腳本會安裝 `requirements.txt` 與 PyInstaller，然後打包。
4. 將 `dist/MapleStoryAutoPrayer.exe` 和 `dist/config.json` **一起**複製到要使用的資料夾；直接啟動 `.exe`，不需要在目標電腦安裝 Python。

設定會從執行檔旁的 `config.json` 讀取並保存。請將程式放在可寫入的資料夾（例如桌面或使用者文件夾）。

打包後請在實際遊戲畫面測試視窗選擇、血條校準、多人與畫面邊緣狀況、停止功能。macOS 上的測試不能驗證 Win32 擷取與按鍵操作。
