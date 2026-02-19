#!/bin/bash
set -e

echo "Installing System Dependencies for XvG-AutoKeybind on Linux..."

# Check for apt
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y build-essential python3-dev libevdev-dev python3-tk xdotool python3-pip
else
    echo "Warning: apt-get not found. Please ensure you have the following installed:"
    echo "- build-essential"
    echo "- python3-dev"
    echo "- libevdev-dev"
    echo "- python3-tk"
    echo "- xdotool"
fi

# Setup uinput permissions (Critical for Wayland/Evdev)
echo "Setting up permissions for /dev/uinput..."
sudo usermod -aG input $USER

# Ensure uinput group exists and add user to it (some distros use 'uinput' group for /dev/uinput)
if getent group uinput > /dev/null; then
    sudo usermod -aG uinput $USER
fi

# Create udev rule to allow 'input' group to write to uinput
# This handles both cases: /dev/uinput owned by root:input or root:uinput
# We force it to be accessible by the 'input' group for simplicity, or 'uinput' if present.
# Ideally, we just want our user to have access. 
# A common pattern is: KERNEL=="uinput", SUBSYSTEM=="misc", TAG+="uaccess", OPTIONS+="static_node=uinput"
# But for a dedicated group approach:
echo 'KERNEL=="uinput", SUBSYSTEM=="misc", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-xvga-uinput.rules

# Reload rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Installing Python Dependencies..."
if command -v uv &> /dev/null; then
    uv venv
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

# Fix ownership if run as root/sudo
if [ "$SUDO_USER" ]; then
    echo "Fixing permissions for $SUDO_USER..."
    chown -R $SUDO_USER:$SUDO_USER .venv 2>/dev/null || true
    chown -R $SUDO_USER:$SUDO_USER . 2>/dev/null || true
fi

echo ""
echo "----------------------------------------------------------------"
echo "Installation Complete!"
echo "----------------------------------------------------------------"
echo "IMPORTANT: Group changes require a logout/login to take effect."
echo "If you want to run the app immediately without logging out, run:"
echo ""
echo "    newgrp input"
echo ""
echo "Then, run the app:"
echo "    uv run python autokeybind.py"
echo "----------------------------------------------------------------"
