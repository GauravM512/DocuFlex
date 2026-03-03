@echo off
setlocal

REM Always run from this script's folder
cd /d "%~dp0"

set "SOFFICE=%~dp0libreoffice\App\libreoffice\program\soffice.exe"
set "LO_ACCEPT=--accept=socket,host=localhost,port=8100;urp;"

if not exist "%SOFFICE%" (
    echo [ERROR] LibreOffice executable not found:
    echo %SOFFICE%
    exit /b 1
)

echo Starting LibreOffice headless server...
for /f %%P in ('powershell -NoProfile -Command "$p = Start-Process -FilePath \"%SOFFICE%\" -ArgumentList @('--headless','%LO_ACCEPT%') -PassThru; Write-Output $p.Id"') do set "LO_PID=%%P"

if not defined LO_PID (
    echo [ERROR] Failed to start LibreOffice server.
    exit /b 1
)

echo LibreOffice started with PID %LO_PID%
echo.
echo Starting DocuFlex...
echo Press Ctrl+C to stop. LibreOffice will be stopped automatically.
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn main:app --reload
) else (
    python -m uvicorn main:app --reload
)

echo.
echo Stopping LibreOffice (PID %LO_PID%)...
taskkill /IM soffice.exe /F
echo Done.

endlocal
