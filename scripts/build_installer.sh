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
    
    # --- Windows Build ---
    # Check if python.exe is available
    if ! command -v python.exe &> /dev/null; then
        echo "Error: python.exe not found in PATH."
        exit 1
    fi
    
    # Check if PyInstaller is installed in Windows Python
    if ! python.exe -m PyInstaller --version &> /dev/null; then
        echo "PyInstaller not found in Windows Python. Installing..."
        python.exe -m pip install pyinstaller
    fi

    echo "Building Windows EXE (python.exe)..."
    python.exe -m PyInstaller XvGKeybind.spec --noconfirm --clean --distpath dist/windows

    # --- Linux Build ---
    echo "Building Linux Binary (pyinstaller)..."
    pyinstaller XvGKeybind.spec --noconfirm --clean --distpath dist/linux
else
    # Native Linux (just build Linux)
    echo "Linux detected. Using pyinstaller..."
    pyinstaller XvGKeybind.spec --noconfirm --clean --distpath dist/linux
fi

# 3. Preparation for Inno Setup
# Inno Setup expects the file in a specific location as per installer.iss
# Source: "dist\XvGKeybind.exe"
# Since we built to dist/windows, we can copy it to dist/ or update installer.iss.
# Copying is easier for now.
mkdir -p dist
if [ -f "dist/windows/XvGKeybind.exe" ]; then
    cp "dist/windows/XvGKeybind.exe" "dist/XvGKeybind.exe"
fi

# 4. Run Inno Setup
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
    echo "Skipping Installer build (Windows Only)."
    # Don't exit 1 if we are on pure Linux and just wanted the binary, but script implies full installer build.
    # If on WSL, we expect it to work.
    if grep -qi microsoft /proc/version; then
         exit 1
    fi
fi

echo "Build Complete!"
echo "Artifacts:"
if [ -f "dist/windows/XvGKeybind.exe" ]; then
    echo " - Windows EXE: dist/windows/XvGKeybind.exe"
fi
if [ -f "dist/linux/XvGKeybind" ]; then
    echo " - Linux Binary: dist/linux/XvGKeybind"
fi
if [ -f "Output/XvGAutoSetup.exe" ]; then
    echo " - Installer: Output/XvGAutoSetup.exe"
fi
