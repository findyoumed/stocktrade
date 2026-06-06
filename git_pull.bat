@echo off
:: [LOG: 20260605_0938]
echo ==========================================
echo   Git Pull Helper Script
echo ==========================================
echo.

:: Check if .git folder exists to decide clone or pull
if not exist ".git" (
    echo [Info] Repository not initialized here. Cloning from GitHub...
    git clone https://github.com/findyoumed/stocktrade.git .
) else (
    echo [Step 1] Fetching updates from remote...
    git fetch origin
    
    echo.
    echo [Step 2] Pulling latest changes from main branch...
    git pull origin main
)

echo.
echo ==========================================
echo   Git Pull Process Completed!
echo ==========================================
echo.
pause
