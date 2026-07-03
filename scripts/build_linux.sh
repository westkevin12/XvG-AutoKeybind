#!/bin/bash
set -e

echo "Building Linux Binary..."

# Ensure all application dependencies are installed
echo "Installing application dependencies..."
if command -v uv &> /dev/null; then
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

# Locate Python library directory to resolve libtcl/libtk version 9 dependencies on Linux
if [ -f ".venv/bin/python3" ]; then
    PYTHON_EXE=".venv/bin/python3"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_EXE=".venv/bin/python"
else
    PYTHON_EXE="python3"
fi

PYTHON_LIB_DIR=$($PYTHON_EXE -c "import sys, os; print(os.path.abspath(os.path.join(os.path.dirname(getattr(sys, '_base_executable', sys.executable)), '..', 'lib')))" 2>/dev/null || true)
if [ -n "$PYTHON_LIB_DIR" ] && [ -d "$PYTHON_LIB_DIR" ]; then
    export LD_LIBRARY_PATH="$PYTHON_LIB_DIR:${LD_LIBRARY_PATH:-}"
    echo "Set LD_LIBRARY_PATH to: $PYTHON_LIB_DIR"
fi

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
    --collect-all "pyautogui" \
    --hidden-import "PIL" \
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
