@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"

if exist "%PYTHON_EXE%" (
    start "Collectables UI Server" /D "%~dp0" "%PYTHON_EXE%" app.py
    timeout /t 3 /nobreak >nul
    start "" http://127.0.0.1:5000
    goto :eof
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "Collectables UI Server" /D "%~dp0" py -3 app.py
    timeout /t 3 /nobreak >nul
    start "" http://127.0.0.1:5000
    goto :eof
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "Collectables UI Server" /D "%~dp0" python app.py
    timeout /t 3 /nobreak >nul
    start "" http://127.0.0.1:5000
    goto :eof
)

echo Python was not found for this launcher.
echo Expected one of:
echo   %PYTHON_EXE%
echo   py -3
echo   python
pause
