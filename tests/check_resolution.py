
import pyautogui
from pynput.mouse import Controller as MouseController
import evdev
from evdev import ecodes

def check():
    print(f"PyAutoGUI Size: {pyautogui.size()}")
    
    mouse = MouseController()
    print(f"Pynput Position: {mouse.position}")
    
    # Check screen size via xrandr if possible
    import subprocess
    try:
        res = subprocess.check_output(["xrandr", "--current"]).decode()
        for line in res.splitlines():
            if " connected" in line:
                print(f"Monitor: {line}")
    except:
        pass

if __name__ == "__main__":
    check()
