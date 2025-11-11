@echo off
echo AR Memory Reconstructor Backend Setup
echo ====================================

:: Create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

:: Install dependencies
pip install -r requirements.txt

:: Create .env file
if not exist ".env" copy .env.example .env

:: Choose database setup
echo.
echo Choose database option:
echo 1. MongoDB Atlas (Cloud - Recommended)
echo 2. Local MongoDB
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo Setting up MongoDB Atlas...
    python setup_atlas.py
) else (
    echo.
    echo Setting up local MongoDB...
    python setup_mongodb.py
)

echo.
echo Setup complete! To start the server:
echo   venv\Scripts\activate
echo   python run.py
echo.
pause