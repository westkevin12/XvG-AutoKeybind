# XvG-AutoKeybind

A simple Python GUI application that allows users to bind keys to specific mouse click coordinates.

## Features
- Create multiple profiles for different keybind sets.
- Bind any key to a screen coordinate.
- System tray integration for background operation.
- GUI interface built with Tkinter.

## Requirements
- Python 3.x
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

1.  **Launch the Application**: Run `autokeybind.py`.
2.  **Manage Profiles**: 
    - Create new profiles or use the "Default" one.
    - Profiles are saved automatically to `profiles.json`.
3.  **Add Keybinds**:
    - Click **"Add Keybind"**.
    - A dialog will appear:
        - **Key**: Enter the key you want to bind (e.g., `a`, `F1`).
        - **Action Type**: Select the behavior you want:
            - **Click & Return**: Clicks the target and returns cursor to original position (Default).
            - **Click & Stay**: Clicks the target and leaves the cursor there.
            - **Double Click & Return**: Double-clicks the target and returns.
            - **Drag & Return**: Moves to target, holds mouse down, returns to original pos, releases (simulates dragging item back).
    - Click **"Set Location"**.
    - Click anywhere on your screen to define the target coordinate.
4.  **Test**: Press your bound key to execute the action.
5.  **System Tray**: The app minimizes to the tray. Right-click the tray icon to exit.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
