@echo off
title iOS Format Converter
cd /d "%~dp0"

echo ==========================================
echo        iOS Format Converter
echo   HEIC/HEIF to PNG  -  MOV/M4V to MP4
echo ==========================================
echo.
echo Current directory: %CD%
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if "%~1"=="" (
    echo No files specified. What would you like to do?
    echo.
    echo   1. Check dependencies
    echo   2. Launch GUI
    echo   3. Select folder to convert
    echo   4. Exit
    echo.
    choice /c 1234 /n /m "Enter choice (1-4): "
    
    if errorlevel 4 exit /b
    if errorlevel 3 goto selectfolder
    if errorlevel 2 goto launchgui
    if errorlevel 1 goto checkdeps
)

goto convert

:checkdeps
.venv\Scripts\python.exe ios_converter_cli.py --check
echo.
pause
exit /b

:launchgui
echo Launching GUI...
start "" ".venv\Scripts\pythonw.exe" ios_converter.py
exit /b

:selectfolder
set /p "folder=Enter folder path: "
.venv\Scripts\python.exe ios_converter_cli.py -d "%folder%"
echo.
pause
exit /b

:convert

if "%~1"=="--gui" (
    echo Launching GUI...
    start "" ".venv\Scripts\pythonw.exe" ios_converter.py
    exit /b
)

if "%~1"=="--check" (
    .venv\Scripts\python.exe ios_converter_cli.py --check
    echo.
    pause
    exit /b
)

echo Converting files...
.venv\Scripts\python.exe ios_converter_cli.py %*
echo.
pause
