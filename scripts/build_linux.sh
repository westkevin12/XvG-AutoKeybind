#!/bin/bash
set -e

echo "Building Linux Binary..."



# Clean previous builds
rm -rf build dist

# Detect build tool: prefer uv for installation speed, fallback to standard pip
if command -v uv &> /dev/null; then
    echo "Using uv to install dependencies in a system-linked venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    uv pip install -r requirements.txt pyinstaller
    uv pip install --force-reinstall Pillow
else
    echo "uv not found, falling back to standard venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt pyinstaller
    pip install --force-reinstall Pillow
fi

# Build
# Note: hidden-import might be needed for pynput backends
PYSTRAY_BACKEND=xorg pyinstaller --noconfirm --onefile --windowed --name "XvG-AutoKeybind" \
    --add-data "icon.ico:." \
    --add-data "scripts/fix_wayland_permissions.sh:scripts" \
    --hidden-import "pynput.keyboard._xorg" \
    --hidden-import "pynput.mouse._xorg" \
    --collect-all "pystray" \
    --collect-all "pyautogui" \
    --hidden-import "PIL" \
    --hidden-import "PIL.Image" \
    --hidden-import "PIL.ImageTk" \
    --hidden-import "PIL._tkinter_finder" \
    autokeybind.py

# Deactivate and clean up virtual environment
deactivate
rm -rf .venv

# Create release directory
mkdir -p dist/release
mv dist/XvG-AutoKeybind dist/release/XvG-AutoKeybind

# Copy install script
cp scripts/install_linux.sh dist/release/install.sh
chmod +x dist/release/install.sh

echo "Build Complete!"
echo ""
echo "Release Package Created at: dist/release/"
echo "Contains:"
echo "  - XvG-AutoKeybind (Binary)"
echo "  - install.sh (Setup Script)"
echo ""
echo "To test like a user:"
echo "  1. cd dist/release"
echo "  2. sudo ./install.sh"
echo "  3. newgrp input"
echo "  4. ./XvG-AutoKeybind"
