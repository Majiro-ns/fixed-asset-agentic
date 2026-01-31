@echo off
chcp 65001 > nul
echo ========================================
echo   Fixed Asset Classification System
echo   (Kotei Shisan Hantei System)
echo ========================================
echo.

REM Set working directory to script location
cd /d "%~dp0"

REM Activate virtual environment if exists
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Check dependencies
echo [INFO] Checking dependencies...
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo [WARN] streamlit is not installed
    echo [INFO] Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [INFO] Starting Streamlit UI...
echo [INFO] Browser will open automatically
echo [INFO] Press Ctrl+C to stop
echo.

REM Start Streamlit
streamlit run ui/app_minimal.py --server.port 8501

pause
