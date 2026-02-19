#!/bin/bash
set -e

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

echo "Installing System Dependencies for $APP_NAME on Linux..."

# Check for apt
if command -v apt-get &> /dev/null; then
    # We need root for apt-get
    elevate apt-get update
    elevate apt-get install -y build-essential python3-dev libevdev-dev python3-tk xdotool python3-pip kbd
else
    echo "Warning: apt-get not found. Please ensure dependencies are installed (including kbd for dumpkeys)."
fi

# Setup udev rules for scoped access (Security: uaccess tag)
echo "Setting up udev rules for XvG devices..."

RULES_FILE="/etc/udev/rules.d/99-xvga-uinput.rules"
RULES_CONTENT='
# XvG Virtual Devices - Grant access to current user
KERNEL=="uinput", SUBSYSTEM=="misc", TAG+="uaccess", OPTIONS+="static_node=uinput"

# XvG Mouse/Keyboard specific tags (if we adding reliable IDs later)
# For now, uinput rule covers creation.

# Physical Keyboards - Grant access for sniffing (uaccess prevents other users from spying)
SUBSYSTEM=="input", ENV{ID_INPUT_KEYBOARD}=="1", TAG+="uaccess"
'

# Write rules using elevation
echo "$RULES_CONTENT" | elevate tee "$RULES_FILE" > /dev/null

# Reload rules
echo "Reloading udev rules..."
elevate udevadm control --reload-rules
elevate udevadm trigger

echo "Installing Python Dependencies..."
if command -v uv &> /dev/null; then
    uv venv
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

# Fix ownership if run as root/sudo (legacy check, less relevant with elevate() but good to keep)
if [ "$SUDO_USER" ]; then
    echo "Fixing permissions for $SUDO_USER..."
    chown -R $SUDO_USER:$SUDO_USER .venv 2>/dev/null || true
    chown -R $SUDO_USER:$SUDO_USER . 2>/dev/null || true
fi

echo ""
echo "----------------------------------------------------------------"
echo "Installation Complete!"
echo "----------------------------------------------------------------"
echo "Note: A reboot or re-login may be required for udev rules to fully apply to existing devices."
echo "Running 'udevadm trigger' should have applied them, but if issues persist, reboot."
echo ""
echo "You can now run the app:"
echo "    uv run python autokeybind.py"
echo "----------------------------------------------------------------"
