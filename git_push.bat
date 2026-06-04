@echo off
:: [LOG: 20260604_1232]
echo ==========================================
echo   Git Push Helper Script
echo ==========================================
echo.

echo [Step 1] Checking git status...
git status
echo.

set /p msg="Enter commit message (default: update): "
if "%msg%"=="" (
    set msg="update"
)

echo.
echo 1. Adding files to staging...
git add .

echo 2. Committing changes...
git commit -m "%msg%"

echo 3. Pushing to GitHub...
git push origin main

echo.
echo ==========================================
echo   GitHub Upload Completed!
echo ==========================================

pause
