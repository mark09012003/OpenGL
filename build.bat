@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

%PYTHON% --version || goto :failed
%PYTHON% -m pip install --upgrade -r requirements.txt pyinstaller || goto :failed
%PYTHON% -m PyInstaller build.spec --clean --noconfirm || goto :failed

if not exist "dist\MapleStoryAutoPrayer.exe" goto :failed
copy /y "config.json" "dist\config.json" >nul || goto :failed

echo.
echo Windows build ready: %CD%\dist\MapleStoryAutoPrayer.exe
echo Copy both MapleStoryAutoPrayer.exe and config.json to the same folder.
pause
exit /b 0

:failed
echo.
echo Build failed. Check the error above and use Python 3.10 or newer on Windows.
pause
exit /b 1
