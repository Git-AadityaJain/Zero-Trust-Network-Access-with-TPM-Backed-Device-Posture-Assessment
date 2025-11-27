@echo off
echo ========================================
echo Building ZTNA DPA Executable
echo ========================================
echo.

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

echo.
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo Building executable...
pyinstaller dpa.spec --clean --noconfirm

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Creating release package...
if not exist "dist\release" mkdir "dist\release"

REM Copy executable
copy "dist\ZTNA-DPA.exe" "dist\release\" >nul 2>&1

REM Copy TPMSigner.exe if it exists
if exist "TPMSigner.exe" (
    copy "TPMSigner.exe" "dist\release\" >nul 2>&1
    echo Copied TPMSigner.exe
)

REM Create README
(
echo ZTNA Device Posture Agent
echo =========================
echo.
echo Installation:
echo   1. Run as Administrator
echo   2. Configure backend URL in C:\ProgramData\ZTNA\config.json
echo   3. Enroll device with enrollment code
echo.
echo Usage:
echo   ZTNA-DPA.exe --help
echo.
echo Configuration:
echo   Location: C:\ProgramData\ZTNA\config.json
echo   Backend URL: Set DPA_BACKEND_URL environment variable or edit config.json
echo.
) > "dist\release\README.txt"

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Executable location: dist\release\ZTNA-DPA.exe
echo.
pause

