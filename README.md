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
   ```bash
   pip install -r requirements.txt
   ```

## Usage

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
    - Reorder actions using "Move Up/Down".
5.  **Global Kill-Switch**: 
    - Press **`Ctrl + Alt + K`** at any time to immediately stop all execution and exit.
    - Press **`Esc`** to stop a running macro.

## Automation & Building

The project includes scripts in the `scripts/` directory for building and publishing:

### Building Binaries
- **Windows/Linux (Bash)**: Run `./scripts/build_installer.sh`. (Requires PyInstaller and Inno Setup for installer).
- **Windows (PowerShell)**: Run `.\scripts\build_installer.ps1`.

### Publishing Releases
- **Bash**: `./scripts/publish_release.sh <version>` (e.g., `./scripts/publish_release.sh v0.0.2`).
- **PowerShell**: `.\scripts\publish_release.ps1 -Version v0.0.2`.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[GPLv3](LICENSE)
