# Release v0.0.5

### Improvements & Fixes

- **Macro Reliability**:
  - Macros now wait for physical keys to be released before firing (1.0s timeout) to prevent modifier interference (e.g., unintended combinations like Ctrl+C when holding Ctrl).
  - Explicit software release of modifiers (Shift, Ctrl, Alt, Cmd) before each macro execution.
- **Keybind Engine**:
  - Moved bind checks to the key release event for more consistent behavior.
- **Wayland / Linux Setup**:
  - Shifted to `uaccess`-based `udev` rules for device permissions, removing the need for manually managing `input`/`uinput` group membership.
- **Input Engine**:
  - Added `get_current_position` method to `PynputEngine` with fallback to `pyautogui`.
