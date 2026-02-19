#!/bin/bash
# Script to fix Wayland/Evdev Permissions (uinput)
# This allows the application to inject mouse/keyboard events without root.

APP_NAME="XvG-AutoKeybind"

# Function to run with root privileges (sudo or pkexec)
elevate() {
    if [ "$EUID" -eq 0 ]; then
        "$@"
    else
        if command -v pkexec &> /dev/null; then
            echo "Requesting privileges via pkexec..."
            pkexec "$@"
        else
            echo "Requesting privileges via sudo..."
            sudo "$@"
        fi
    fi
}

echo "Fixing Wayland/Evdev Permissions (uinput)..."

RULES_FILE="/etc/udev/rules.d/99-xvga-uinput.rules"
RULES_CONTENT='
# XvG Virtual Devices - Grant access to current user
KERNEL=="uinput", SUBSYSTEM=="misc", TAG+="uaccess", OPTIONS+="static_node=uinput"

# Physical Keyboards - Grant access for sniffing (uaccess prevents other users from spying)
SUBSYSTEM=="input", ENV{ID_INPUT_KEYBOARD}=="1", TAG+="uaccess"
'

echo "Updating udev rules..."
echo "$RULES_CONTENT" | elevate tee "$RULES_FILE" > /dev/null

# Reload udev rules
echo "Reloading udev rules..."
elevate udevadm control --reload-rules
elevate udevadm trigger

echo "----------------------------------------------------------------"
echo "Permissions updated successfully!"
echo "Note: A reboot or re-login may be required for udev rules to fully apply."
echo "----------------------------------------------------------------"
