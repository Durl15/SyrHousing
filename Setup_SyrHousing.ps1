# SyrHousing Setup Script
# Creates desktop shortcut and optionally sets up auto-start

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SyrHousing Windows Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptPath "syrhousing_manager.py"
$batchFile = Join-Path $scriptPath "SyrHousing_Manager.bat"

# Check if Python is installed
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found! Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check if required packages are installed
Write-Host "[2/4] Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import tkinter; import requests" 2>&1 | Out-Null
    Write-Host "  ✓ All dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "  ! Installing missing dependencies..." -ForegroundColor Yellow
    pip install requests
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
}

# Create desktop shortcut
Write-Host "[3/4] Creating desktop shortcut..." -ForegroundColor Yellow
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "SyrHousing Manager.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "python"
$shortcut.Arguments = "`"$pythonScript`""
$shortcut.WorkingDirectory = $scriptPath
$shortcut.Description = "SyrHousing Grant Management System"
$shortcut.IconLocation = "shell32.dll,21"  # House icon
$shortcut.Save()

Write-Host "  ✓ Desktop shortcut created" -ForegroundColor Green

# Ask about auto-start
Write-Host "[4/4] Auto-start configuration..." -ForegroundColor Yellow
$autoStart = Read-Host "  Do you want SyrHousing to start automatically on Windows boot? (Y/N)"

if ($autoStart -eq "Y" -or $autoStart -eq "y") {
    # Create startup shortcut
    $startupPath = [Environment]::GetFolderPath("Startup")
    $startupShortcut = Join-Path $startupPath "SyrHousing Manager.lnk"

    $startupShortcutObj = $WScriptShell.CreateShortcut($startupShortcut)
    $startupShortcutObj.TargetPath = "pythonw"  # Use pythonw to hide console
    $startupShortcutObj.Arguments = "`"$pythonScript`""
    $startupShortcutObj.WorkingDirectory = $scriptPath
    $startupShortcutObj.WindowStyle = 7  # Minimized
    $startupShortcutObj.Save()

    Write-Host "  ✓ Auto-start enabled" -ForegroundColor Green
} else {
    Write-Host "  ○ Auto-start skipped" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start SyrHousing Manager:" -ForegroundColor White
Write-Host "  • Double-click the desktop shortcut" -ForegroundColor White
Write-Host "  • Or run: python syrhousing_manager.py" -ForegroundColor White
Write-Host ""

# Ask if user wants to launch now
$launch = Read-Host "Launch SyrHousing Manager now? (Y/N)"
if ($launch -eq "Y" -or $launch -eq "y") {
    Start-Process python -ArgumentList "`"$pythonScript`"" -WorkingDirectory $scriptPath
    Write-Host "✓ SyrHousing Manager launched!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
