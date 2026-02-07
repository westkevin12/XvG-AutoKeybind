#!/bin/bash
# scripts/build_installer.sh

# Exit on error
set -e

echo "Starting Build Process..."

# 1. Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist build Output

# 2. Run PyInstaller
echo "Running PyInstaller..."
# Check if running in WSL or Linux (Case insensitive check)
if grep -qi microsoft /proc/version; then
    echo "WSL detected."
    
    # Check if python.exe is available
    if ! command -v python.exe &> /dev/null; then
        echo "Error: python.exe not found in PATH."
        echo "Please install Python on Windows and ensure it's in your PATH."
        exit 1
    fi
    
    # Check if PyInstaller is installed in Windows Python
    if ! python.exe -m PyInstaller --version &> /dev/null; then
        echo "PyInstaller not found in Windows Python. Installing..."
        python.exe -m pip install pyinstaller
    fi

    echo "Building Windows EXE using python.exe..."
    python.exe -m PyInstaller XvGKeybind.spec --noconfirm --clean
else
    echo "Linux detected. Using pyinstaller..."
    pyinstaller XvGKeybind.spec --noconfirm --clean
fi

# 3. Run Inno Setup
echo "Running Inno Setup..."
# Try common paths
ISCC_PATH="/mnt/c/Program Files (x86)/Inno Setup 6/ISCC.exe"
if [ ! -f "$ISCC_PATH" ]; then
    ISCC_PATH="/mnt/c/Program Files/Inno Setup 6/ISCC.exe"
fi

if [ -f "$ISCC_PATH" ]; then
    # Convert script path to Windows format for ISCC
    SCRIPT_WIN_PATH=$(wslpath -w "installer.iss")
    "$ISCC_PATH" "$SCRIPT_WIN_PATH"
else
    echo "Inno Setup Compiler (ISCC.exe) not found at standard locations."
    echo "Please ensure Inno Setup 6 is installed in Windows/Program Files."
    exit 1
fi

echo "Build Complete!"
echo "Artifacts:"
echo " - EXE: dist/XvGKeybind.exe"
echo " - Installer: Output/XvGAutoSetup.exe"
