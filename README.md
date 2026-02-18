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
- **Cross-Platform Support**: Built for Windows and Linux.

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/westkevin12/XvG-AutoKeybind.git
   cd XvG-AutoKeybind
   ```

2. Install dependencies:

   **Option 1: Using `uv` (Recommended)**

   ```bash
   # Install uv (if not installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # OR via snap: sudo snap install astral-uv --classic

   # Setup environment & install
   uv venv
   uv pip install -r requirements.txt
   ```

   **Option 2: Using standard pip**

   ```bash
   pip install -r requirements.txt
   ```

   **Linux Requirements**:
   On Linux (Ubuntu/Debian), you need system libraries:

   ```bash
   sudo apt-get install build-essential python3-dev libevdev-dev python3-tk xdotool
   ```

   **Permissions & Troubleshooting**:
   - **Display Server**: Ensure you are running an **X11 session** (select "Ubuntu on Xorg" at login). Wayland is not supported for global input simulation.
   - **Input Permissions**: You may need to add your user to the `input` group to detect keypresses:
     ```bash
     sudo usermod -aG input $USER
     # Log out and back in for changes to take effect
     ```

## Usage

> [!IMPORTANT]
> **Linux Users**: This application **requires an X11 session** to function correctly due to Wayland's security restrictions on global input simulation.
> If you are on Ubuntu, log out and select "Ubuntu on Xorg" at the login screen.

1.  **Launch the Application**: Run `python autokeybind.py`.
2.  **Manage Profiles**:
    - Create new profiles or use the "Default" one.
    - Profiles are saved automatically to `profiles.json`.
3.  **Add Keybinds**:
    - Click **"Add Keybind"**.
    - **Key**: Record your key combination (e.g., `Ctrl+F1`).
    - **Action Type**:
      - **Click/Double-Click**: Basic mouse actions at a location.
      - **Drag & Return**: Hold and move mouse back to starting point.
      - **Macro / Sequence**: Select a saved macro or create a new one.
4.  **Macro Editor**:
    - Use the **"Manage Macros"** button to build complex sequences.
    - Add delays, text typing, and keypresses to your sequence.
    - **Tip**: In the text editor, you can use **`\n`** to simulate an **Enter** keypress after typing text.
    - Reorder actions using "Move Up/Down".
5.  **Global Kill-Switch**:
    - Press **`Ctrl + Alt + K`** at any time to immediately stop all execution and exit.
    - Press **`Esc`** to stop a running macro.

## Automation & Building

The project includes scripts in the `scripts/` directory for building and publishing:

### Building Binaries

- **Linux (Bash)**:
  1. Ensure dependencies are installed: `./scripts/install_linux.sh`
  2. Build binary: `./scripts/build_linux.sh`  
     (Output binary will be in `dist/XvG-AutoKeybind`)
- **Windows (Bash)**: Run `./scripts/build_installer.sh`. (Requires PyInstaller and Inno Setup).
- **Windows (PowerShell)**: Run `.\scripts\build_installer.ps1`.

### Publishing Releases

- **Bash**: `./scripts/publish_release.sh <version>` (e.g., `./scripts/publish_release.sh v0.0.2`).
- **PowerShell**: `.\scripts\publish_release.ps1 -Version v0.0.2`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[GPLv3](LICENSE)
