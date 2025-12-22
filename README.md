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

1. Run the application:
   ```bash
   python main.py
   ```
   Or directly:
   ```bash
   python autokeybind.py
   ```

2. **Add a Profile**: Click "Add Profile" to create a new profile.
3. **Add Keybind**:
   - Enter the key you want to bind in the "Enter Key" field.
   - Click "Add Keybind" (or press the button).
   - Click anywhere on the screen to capture the coordinates.
4. **Use Keybinds**: When the application is running, pressing the bound key will simulate a mouse click at the saved location.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
