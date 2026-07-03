#!/bin/bash
set -e

echo "Building Linux Binary..."

# Ensure all application dependencies are installed on system Python
echo "Installing application dependencies..."
python3 -m pip install --user --break-system-packages -r requirements.txt pyinstaller
python3 -m pip install --user --break-system-packages --force-reinstall Pillow

# Clean previous builds
rm -rf build dist

# Build
# Note: hidden-import might be needed for pynput backends
PYSTRAY_BACKEND=xorg python3 -m PyInstaller --noconfirm --onefile --windowed --name "XvG-AutoKeybind" \
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
