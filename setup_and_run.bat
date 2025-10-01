@echo off
echo ========================================
echo RFP Processing Pipeline Setup
echo ========================================

echo.
echo 1. Installing dependencies...
pip install -r requirements.txt

echo.
echo 2. Creating output directory...
if not exist "output" mkdir output

echo.
echo 3. Checking environment configuration...
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and add your Azure OpenAI API key
    echo.
    pause
)

echo.
echo 4. Starting the server...
echo ========================================
echo Server will be available at:
echo   Web Interface: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo ========================================
echo.

python run_server.py

pause