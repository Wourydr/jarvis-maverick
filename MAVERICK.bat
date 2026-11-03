@echo off
title MAVERICK // NEURAL OS
cd /d "%~dp0"

:: Verification et demarrage automatique du serveur Ollama si necessaire
curl -s http://127.0.0.1:11434/api/version >nul 2>&1
if %errorlevel% neq 0 (
    echo Demarrage du serveur local Ollama...
    start "" /B "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 3 /nobreak >nul
)

call venv\Scripts\activate
"%~dp0venv\Scripts\python.exe" app_neural.py
