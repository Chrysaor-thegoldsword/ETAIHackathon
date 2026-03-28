@echo off
setlocal

cd /d "%~dp0"

echo Starting ET Money Mentor...
echo.

if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (`findstr /r /v "^[ ]*# ^[ ]*$" ".env"`) do (
        if /I "%%~A"=="GROQ_API_KEY" set "GROQ_API_KEY=%%~B"
        if /I "%%~A"=="GROQ_MODEL" set "GROQ_MODEL=%%~B"
    )
)

if not defined GROQ_API_KEY (
    echo GROQ_API_KEY was not found in .env
    set /p GROQ_API_KEY=Enter your Groq API key: 
)

if not defined GROQ_API_KEY (
    echo.
    echo No API key provided. Exiting.
    pause
    exit /b 1
)

echo Installing required packages if needed...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Python command failed. Trying with py launcher...
    py -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Could not install dependencies.
        pause
        exit /b 1
    )
    echo.
    echo Launching app on http://127.0.0.1:8000
    py -m uvicorn src.main:app --reload
    pause
    exit /b
)

echo.
echo Launching app on http://127.0.0.1:8000
python -m uvicorn src.main:app --reload
pause
