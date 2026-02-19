# build_installer.ps1

Write-Host "Starting Build Process..." -ForegroundColor Cyan

# 1. Clean previous builds
Write-Host "Cleaning previous builds..."
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "Output") { Remove-Item -Recurse -Force "Output" }

# 2. Run PyInstaller
Write-Host "Running PyInstaller..." -ForegroundColor Cyan
pyinstaller XvG-AutoKeybind.spec --noconfirm --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed!" -ForegroundColor Red
    exit 1
}

# 3. Check for Inno Setup Compiler
$isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $isccPath)) {
    # Try alternate location or ask user
    $isccPath = "C:\Program Files\Inno Setup 6\ISCC.exe"
    if (-not (Test-Path $isccPath)) {
        Write-Host "Inno Setup Compiler (ISCC.exe) not found at standard locations." -ForegroundColor Red
        Write-Host "Please ensure Inno Setup 6 is installed."
        exit 1
    }
}

# 4. Run Inno Setup
Write-Host "Running Inno Setup..." -ForegroundColor Cyan
& $isccPath "installer.iss"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Inno Setup failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "Artifacts:"
Write-Host " - EXE: dist\XvG-AutoKeybind.exe"
Write-Host " - Installer: Output\XvGAutoSetup.exe"
