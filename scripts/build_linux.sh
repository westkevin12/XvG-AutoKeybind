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
    --add-data "scripts/fix_wayland_permissions.sh:scripts" \
    --hidden-import "pynput.keyboard._xorg" \
    --hidden-import "pynput.mouse._xorg" \
    --collect-all "pystray" \
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
