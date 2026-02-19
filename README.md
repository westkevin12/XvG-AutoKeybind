# XvG-AutoKeybind

A simple Python GUI application that allows users to bind keys to specific mouse click coordinates.

## Features

- **Keybinding**: Bind any key combination to specific screen coordinates.
- **Action Types**: Support for Click, Double-Click, Drag, and more.
- **Macro Suite**: Create and save complex sequences of clicks, keystrokes, and delays.
- **Auto-Typer**: Integrated text typing with human-like random delay support.
- **Profile Management**: Save multiple sets of keybinds for different applications or games.
- **Safety Kill-Switch**: Global emergency stop (`Ctrl + Alt + K`) or `Esc` to halt all actions.
- **System Tray Integration**: Runs quietly in the background with a tray icon.
- **Cross-Platform Support**: Optimized for Windows (Pynput) and Linux (Evdev/UInput).
- **Wayland Native**: Pixel-perfect click synchronization on Wayland using hardware-level absolute coordinate injection.

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`
- (Linux) `libevdev` and `uinput` kernel support.

## Installation

### 1. Clone & Setup

```bash
git clone https://github.com/westkevin12/XvG-AutoKeybind.git
cd XvG-AutoKeybind
```

### 2. Linux System Setup (Wayland & X11)

On Linux, the application uses **Evdev** to bypass compositor restrictions and **UInput** for hardware-level injection.

**Automatic Setup (Ubuntu/Debian)**:

```bash
# Installs system libraries, sets up groups, and configures udev rules
./scripts/install_linux.sh
```

**Manual Setup**:

1. **Dependencies**: `sudo apt-get install build-essential python3-dev libevdev-dev python3-tk xdotool`
2. **Permissions**: Add your user to the `input` and `uinput` groups.
3. **UDev Rules**: Ensure `/dev/uinput` is accessible. You can use the helper script:
   ```bash
   ./scripts/fix_wayland_permissions.sh
   ```
4. **Login**: You **must log out and log back in** (or restart) for group changes to take effect. If you're in a hurry, run `newgrp input` in your terminal.

### 3. Python Dependencies

**Recommended (UV)**:

```bash
uv venv
uv pip install -r requirements.txt
```

**Standard Pip**:

```bash
pip install -r requirements.txt
```

## Usage

1.  **Launch the Application**:
    - Run `uv run autokeybind.py` or `python autokeybind.py`.
    - Check the status bar:
      - `Input: Evdev (Global)` -> Full Wayland/Background support.
      - `Input: Pynput (Restricted)` -> Fallback mode (mostly X11/Windows).

2.  **Manage Profiles**:
    - Create new profiles or use the "Default" one.
    - Profiles are saved automatically to `profiles.json`.
3.  **Add Keybinds**:
    - Click **"Add Keybind"**.
    - **Action Type**:
      - **Click/Double-Click**: Basic mouse actions.
      - **Drag & Return**: Hardware-synced drag operations.
4.  **Macro Editor**:
    - Use the **"Manage Macros"** button to build sequences.
    - **Tip**: In the text editor, use **`\n`** for **Enter**.
5.  **Global Kill-Switch**:
    - Press **`Ctrl + Alt + K`** to exit immediately.
    - Press **`Esc`** to stop a running macro.

## Project Structure

- `autokeybind.py`: Main GUI and application logic.
- `input_engine.py`: Core input sniffing and injection (Pynput & Evdev).
- `scripts/`: Production build and installation tools.
- `tests/`: Essential regression and verification tests.
- `profiles.json`: Saved configurations.

## Automation & Building

- **Linux**: `./scripts/build_linux.sh` (Output in `dist/release/`)
- **Windows**: `./scripts/build_installer.sh`

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[GPLv3](LICENSE)
