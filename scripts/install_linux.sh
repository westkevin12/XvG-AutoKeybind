#!/bin/bash
set -e

echo "Installing System Dependencies for XvG-AutoKeybind on Linux..."

# Check for apt
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y build-essential python3-dev libevdev-dev python3-tk xdotool
else
    echo "Warning: apt-get not found. Please ensure you have the following installed:"
    echo "- build-essential"
    echo "- python3-dev"
    echo "- libevdev-dev"
    echo "- python3-tk"
    echo "- xdotool"
fi

echo "Installing Python Dependencies..."
if command -v uv &> /dev/null; then
    uv venv
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

echo "Done! Run with: uv run python autokeybind.py"
