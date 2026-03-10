@echo off
:: =================================================================================================
:: STEER Framework — Windows Installer
:: =================================================================================================
:: This script sets up the STEER Framework on Windows, including:
::   - Python dependency installation
::   - WSL setup check for running C-based tests (NIST STS, Diehard, TestU01)
::   - Desktop shortcut creation
::   - PATH configuration
:: =================================================================================================

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo   STEER Framework Installer for Windows
echo ================================================================================
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.10+ from https://www.python.org/downloads/
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Found Python %PYVER%

:: Determine framework root (parent of installers directory)
set "SCRIPT_DIR=%~dp0"
set "FRAMEWORK_ROOT=%SCRIPT_DIR%.."
pushd "%FRAMEWORK_ROOT%"
set "FRAMEWORK_ROOT=%CD%"
popd

echo [OK] Framework root: %FRAMEWORK_ROOT%

:: Install Python dependencies
echo.
echo Installing Python dependencies...
echo.

pip install "PyQt6>=6.7.0" 2>nul
if errorlevel 1 (
    echo [WARN] Could not install PyQt6. Trying with --user flag...
    pip install --user "PyQt6>=6.7.0"
)

:: Install dependencies for causal model tests
pip install "numpy>=1.21.0" "pandas>=1.3.0" "scikit-learn>=1.0.0" "scipy>=1.7.0" 2>nul
if errorlevel 1 (
    pip install --user "numpy>=1.21.0" "pandas>=1.3.0" "scikit-learn>=1.0.0" "scipy>=1.7.0"
)

echo.
echo [OK] Python dependencies installed.

:: Check for WSL
echo.
echo Checking for WSL (needed to run C-based tests: NIST STS, Diehard, TestU01)...
wsl --status >nul 2>&1
if errorlevel 1 (
    echo [WARN] WSL is not installed.
    echo        C-based tests ^(NIST STS, Diehard, TestU01^) require WSL with Ubuntu.
    echo        Install WSL: wsl --install -d Ubuntu-24.04
    echo        The GUI will still work but C tests will be unavailable.
) else (
    echo [OK] WSL is available.
    echo      Checking for Ubuntu distribution...
    wsl -d Ubuntu-24.04 -- echo "Ubuntu 24.04 available" 2>nul
    if errorlevel 1 (
        echo [WARN] Ubuntu-24.04 not found in WSL.
        echo        Install it: wsl --install -d Ubuntu-24.04
    ) else (
        echo [OK] Ubuntu-24.04 is available in WSL.
    )
)

:: Build STEER C tests in WSL (if available)
echo.
echo Building STEER C tests (NIST STS, Diehard, TestU01)...

:: Convert Windows path to WSL /mnt/ path
set "WSL_ROOT=%FRAMEWORK_ROOT%"
set "WSL_ROOT=%WSL_ROOT:\=/%"
set "WSL_ROOT=%WSL_ROOT:C:=/mnt/c%"
set "WSL_ROOT=%WSL_ROOT:D:=/mnt/d%"
set "WSL_ROOT=%WSL_ROOT:E:=/mnt/e%"

wsl -d Ubuntu-24.04 -- bash -c "cd '%WSL_ROOT%' && bash build.sh" 2>nul
if errorlevel 1 (
    echo [WARN] Could not build C tests. They may need to be built manually in WSL.
) else (
    echo [OK] STEER C tests built successfully.
)

:: Create launcher script
echo.
echo Creating launcher...

set "LAUNCHER=%FRAMEWORK_ROOT%\steer-gui.bat"
(
    echo @echo off
    echo cd /d "%FRAMEWORK_ROOT%\src\steer-gui"
    echo python main.py --root "%FRAMEWORK_ROOT%" %%*
) > "%LAUNCHER%"

echo [OK] Launcher created: %LAUNCHER%

:: Create desktop shortcut
echo.
echo Creating desktop shortcut...

:: Detect actual Desktop path (handles OneDrive redirect)
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v Desktop 2^>nul') do set "DESKTOP=%%b"
if not defined DESKTOP set "DESKTOP=%USERPROFILE%\Desktop"
:: Expand environment variables in the path
call set "DESKTOP=%DESKTOP%"
set "SHORTCUT=%DESKTOP%\STEER Framework.lnk"

:: Use PowerShell to create .lnk shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%LAUNCHER%'; $s.WorkingDirectory = '%FRAMEWORK_ROOT%'; $s.Description = 'STEER Framework - Statistical Testing of Entropy'; $s.WindowStyle = 7; $s.Save()" 2>nul

if exist "%SHORTCUT%" (
    echo [OK] Desktop shortcut created.
) else (
    echo [WARN] Could not create desktop shortcut.
)

:: Create Start Menu entry
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "STARTSHORTCUT=%STARTMENU%\STEER Framework.lnk"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTSHORTCUT%'); $s.TargetPath = '%LAUNCHER%'; $s.WorkingDirectory = '%FRAMEWORK_ROOT%'; $s.Description = 'STEER Framework'; $s.WindowStyle = 7; $s.Save()" 2>nul

if exist "%STARTSHORTCUT%" (
    echo [OK] Start Menu shortcut created.
)

:: Create CLI docs launcher
set "DOCS_LAUNCHER=%FRAMEWORK_ROOT%\steer-docs.bat"
(
    echo @echo off
    echo python "%FRAMEWORK_ROOT%\src\steer-docs\steer_docs.py" %%*
) > "%DOCS_LAUNCHER%"

echo [OK] Documentation CLI: %DOCS_LAUNCHER%

echo.
echo ================================================================================
echo   Installation complete!
echo ================================================================================
echo.
echo   Launch GUI:        steer-gui.bat
echo   View docs (CLI):   steer-docs.bat --list
echo   Desktop shortcut:  %SHORTCUT%
echo.
echo   Note: To run C-based tests (NIST STS, Diehard, TestU01), ensure WSL
echo         with Ubuntu-24.04 is set up and the framework is built
echo         (run build.sh in WSL).
echo.

pause
