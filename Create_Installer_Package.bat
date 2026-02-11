@echo off
title Create SyrHousing Installer Package
color 0B

echo ================================================
echo   Creating SyrHousing Installer Package
echo ================================================
echo.

:: Create package directory
set PACKAGE_DIR=SyrHousing_Package_%date:~-4%%date:~-10,2%%date:~-7,2%
mkdir %PACKAGE_DIR%

echo [1/5] Copying essential files...
xcopy *.py %PACKAGE_DIR%\ /Y >nul
xcopy *.bat %PACKAGE_DIR%\ /Y >nul
xcopy *.ps1 %PACKAGE_DIR%\ /Y >nul
xcopy *.md %PACKAGE_DIR%\ /Y >nul
xcopy *.txt %PACKAGE_DIR%\ /Y >nul

echo [2/5] Copying backend...
xcopy backend %PACKAGE_DIR%\backend\ /E /I /EXCLUDE:exclude_package.txt >nul

echo [3/5] Copying frontend...
if exist frontend xcopy frontend %PACKAGE_DIR%\frontend\ /E /I /EXCLUDE:exclude_package.txt >nul

echo [4/5] Creating README...
echo SyrHousing - Installation Package > %PACKAGE_DIR%\START_HERE.txt
echo. >> %PACKAGE_DIR%\START_HERE.txt
echo Installation Instructions: >> %PACKAGE_DIR%\START_HERE.txt
echo 1. Copy this entire folder to C:\ >> %PACKAGE_DIR%\START_HERE.txt
echo 2. Run: Install_SyrHousing.bat >> %PACKAGE_DIR%\START_HERE.txt
echo 3. Run: SyrHousing_Manager.bat >> %PACKAGE_DIR%\START_HERE.txt
echo. >> %PACKAGE_DIR%\START_HERE.txt
echo Enjoy automatic grant discovery! >> %PACKAGE_DIR%\START_HERE.txt

echo [5/5] Creating ZIP package...
powershell Compress-Archive -Path %PACKAGE_DIR% -DestinationPath %PACKAGE_DIR%.zip -Force

echo.
echo ================================================
echo   Package Created Successfully!
echo ================================================
echo.
echo Package location:
echo   %CD%\%PACKAGE_DIR%.zip
echo.
echo Size:
dir %PACKAGE_DIR%.zip | find ".zip"
echo.
echo You can now share this ZIP file with anyone!
echo.
pause
