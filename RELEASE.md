# Release v0.0.4

## 🚀 Wayland Support & Stability

This release brings full compatibility for Wayland sessions on Linux, removing previous input simulation restrictions.

- **Native Wayland Support**: Implemented `EvdevEngine` to bypass security restrictions via `/dev/input` and `/dev/uinput`.
- **Absolute Mouse Synchronization**: Implemented hardware-level injection for both moves and clicks. This ensures pixel-perfect accuracy on high-resolution Wayland environments.
- **Automatic Engine Selection**: Intelligent fallback between `evdev` (Wayland/Linux) and `pynput` (X11/Windows).
- **Enhanced Stability**: Added a "Heartbeat" mechanism to automatically restart input listeners if they become unresponsive.

## 🛠 Enhancements

- **Input Handling**: Abstracted input logic into a flexible `InputEngine` architecture.
- **Project Organization**: Cleaned up the `scripts/` directory and moved essential verification tools to a new `tests/` directory.
- **Build System**: Resolved Linux binary build failures by including `fix_wayland_permissions.sh` script in the distribution.

## 📦 Installation & Setup (Linux)

**Important**: Wayland support requires kernel-level permissions.

1. **Install Dependencies**:

   ```bash
   # Sets up libraries, groups, and udev rules
   ./scripts/install_linux.sh
   ```

2. **Grant Permissions**:
   If the installer didn't handle it or you prefer manual setup, run:

   ```bash
   ./scripts/fix_wayland_permissions.sh
   ```

   **Log out and back in** for group changes to stay active.

3. **Run**:
   ```bash
   # For the pre-compiled release:
   cd dist/release
   sudo ./install.sh
   ./XvG-AutoKeybind
   ```
