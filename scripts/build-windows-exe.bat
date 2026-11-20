@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "BUILD_PYTHON=%~dp0..\.exe-build.local\venv\Scripts\python.exe"
if not exist "%BUILD_PYTHON%" (
    echo Build Python environment not found. See the Windows EXE section in README.md.
    pause
    exit /b 1
)

"%BUILD_PYTHON%" "%~dp0build-windows-exe.py"
set "BUILD_STATUS=%ERRORLEVEL%"
if "%BUILD_STATUS%"=="0" (
    echo Build complete. Output: release\windows\OrderSystem-Demo.exe
) else (
    echo Build failed. Check the messages above.
)
pause
exit /b %BUILD_STATUS%
