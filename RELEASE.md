# Release v0.0.02

## 🚀 New Features

### Macro Suite
- **Complex Macros**: Create sequences of actions including Clicks, Keypresses, Delays, and Text Typing.
- **Macro Editor**: A dedicated UI to build, reorder, and save your action sequences.
- **Auto-Typer Integration**: Add text actions within macros with advanced delay configurations:
    - **Static Delay**: Fixed time between keystrokes.
    - **Random Delay**: Human-like typing with variable delays (Min/Max).

### Safety & Stability
- **Global Kill-Switch**: Press `Ctrl + Alt + K` to immediately stop all running macros and close the application.
- **Esc Interruption**: Pressing `Esc` while a macro is running will also trigger the emergency stop.

### User Interface
- **Top-Level Windows**: "Manage Binds" and Editor windows now stay on top of the main application.
- **Improved Layout**: Better button visibility and resizing behavior.

### Automation & Deployment
- **Cross-Platform Build Scripts**: New scripts in `scripts/` for building Windows and Linux binaries.
- **Installer Automation**: Automated Inno Setup installer creation via scripts.
- **Publishing Workflow**: Unified scripts to tag and publish releases to GitHub.

## 🛠 Fixes & Improvements
- Fixed Z-Order issues where popup windows would appear behind the main window.
- Refactored internal action handling for better performance and stability.
- Added Linux binary support for cross-platform usage (via WSL build).
- Improved error handling for missing dependencies during startup.
