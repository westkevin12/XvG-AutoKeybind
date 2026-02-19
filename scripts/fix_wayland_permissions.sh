#!/bin/bash
# Script to fix Wayland/Evdev Permissions (uinput)
# This allows the application to inject mouse/keyboard events without root.

echo "Fixing Wayland/Evdev Permissions (uinput)..."

# Add current user to input and uinput groups
sudo usermod -aG input $USER
if getent group uinput > /dev/null; then
    sudo usermod -aG uinput $USER
fi

# Create udev rule for uinput
echo "Creating udev rule for /dev/uinput..."
echo 'KERNEL=="uinput", SUBSYSTEM=="misc", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-xvga-uinput.rules

# Reload udev rules
echo "Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "----------------------------------------------------------------"
echo "Permissions updated successfully!"
echo "IMPORTANT: You must log out and back in for group changes to take effect."
echo "Alternatively, run 'newgrp input' in your terminal before starting the app."
echo "----------------------------------------------------------------"
