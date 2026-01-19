@echo off
title iOS Converter - Easy Launch
color 0A

:menu
cls
echo ============================================
echo        iOS Format Converter
echo   HEIC/HEIF to PNG  -  MOV/M4V to MP4
echo ============================================
echo.
echo What would you like to do?
echo.
echo   1. Convert files in a folder
echo   2. Check if everything is working
echo   3. Exit
echo.
choice /c 123 /n /m "Select option (1-3): "

if errorlevel 3 exit /b
if errorlevel 2 goto check
if errorlevel 1 goto convert

:convert
echo.
set /p "folder=Enter folder path (or drag folder here): "
rem Remove quotes if present
set folder=%folder:"=%
echo.
echo Starting conversion...
echo.
iOSConverter.exe -d "%folder%"
echo.
pause
goto menu

:check
echo.
iOSConverter.exe --check
echo.
pause
goto menu
