# Release v0.0.3

## 🐧 Linux Support & Compatibility

- **Native Wayland Detection**: The application now detects Wayland sessions and warns users about compatibility issues with global input.
- **Dependency Checks**: Added startup checks for `xdotool` to ensure input simulation works correctly.
- **Improved Documentation**: Updated README with specific instructions for Ubuntu/Linux users regarding X11 sessions and permissions.
- **Linux Binary Release**: This release includes a standalone Linux binary for easier distribution.

## 🛠 Enhancements

- **Release Script**: Updated build and release scripts to support Linux-only environments and CI/CD workflows.
- **Error Handling**: Better error messages for missing system dependencies.

## 📦 Installation (Linux)

1. Download `XvG-AutoKeybind` from assets.
2. Make it executable: `chmod +x XvG-AutoKeybind`
3. Run it: `./XvG-AutoKeybind`
   _Note: Ensure you are in an X11 session._
