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

:: Initialize database
python setup_mongodb.py

echo.
echo Setup complete! To start the server:
echo   venv\Scripts\activate
echo   python run.py
echo.
pause