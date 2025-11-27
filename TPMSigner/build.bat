@echo off
echo ========================================
echo Building 64-bit TPMSigner.exe
echo ========================================

where dotnet >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: .NET SDK not found!
    echo Install from: https://dotnet.microsoft.com/download
    pause
    exit /b 1
)

echo.
echo Cleaning previous builds...
dotnet clean

echo.
echo Building Release x64...
dotnet publish -c Release -r win-x64 --self-contained false /p:PublishSingleFile=true

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Copying to parent directory...
copy /Y bin\Release\net8.0-windows\win-x64\publish\TPMSigner.exe ..\TPMSigner.exe

echo.
echo Copying to dpa directory...
copy /Y bin\Release\net8.0-windows\win-x64\publish\TPMSigner.exe ..\dpa\TPMSigner.exe

echo.
echo ========================================
echo SUCCESS!
echo Location: ..\TPMSigner.exe
echo ========================================
pause
