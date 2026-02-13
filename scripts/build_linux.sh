#!/bin/bash
set -e

echo "Building Linux Binary..."

# Ensure PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    if command -v uv &> /dev/null; then
        uv pip install pyinstaller
    else
        pip install pyinstaller
    fi
fi

# Clean previous builds
rm -rf build dist

# Build
# Note: hidden-import might be needed for pynput backends
uv run pyinstaller --noconfirm --onefile --windowed --name "XvG-AutoKeybind" \
    --add-data "icon.ico:." \
    --hidden-import "pynput.keyboard._xorg" \
    --hidden-import "pynput.mouse._xorg" \
    --collect-all "pystray" \
    autokeybind.py

echo "Build Complete! Binary is in dist/XvG-AutoKeybind"
echo "You can run it with: ./dist/XvG-AutoKeybind"
