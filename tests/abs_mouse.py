
import evdev
from evdev import ecodes
import time
from pynput.mouse import Controller

def test_abs_mouse():
    mouse = Controller()
    WIDTH = 3840
    HEIGHT = 1080
    
    cap = {
        ecodes.EV_ABS: [
            (ecodes.ABS_X, evdev.AbsInfo(value=0, min=0, max=WIDTH-1, fuzz=0, flat=0, resolution=1)),
            (ecodes.ABS_Y, evdev.AbsInfo(value=0, min=0, max=HEIGHT-1, fuzz=0, flat=0, resolution=1)),
        ],
        ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE, ecodes.BTN_SIDE, ecodes.BTN_EXTRA]
    }
    
    try:
        # PURE CLONE OF RAZER IDENTIFIERS
        ui = evdev.UInput(
            cap, 
            name="Razer Razer Naga V2 HyperSpeed",
            vendor=0x1532, product=0x00B4, version=0x0111, bustype=ecodes.BUS_USB
        )
        print("[TEST] Absolute Mouse created. Waiting 2s...")
        time.sleep(2)
        
        targets = [(500, 500), (3000, 500)]
        for tx, ty in targets:
            print(f"[TEST] Injecting Absolute {tx}, {ty}...")
            ui.write(ecodes.EV_ABS, ecodes.ABS_X, tx)
            ui.write(ecodes.EV_ABS, ecodes.ABS_Y, ty)
            ui.syn()
            time.sleep(1.0) # Long wait for compositor sync
            
            p = mouse.position
            print(f"[TEST] Result: {p} (Delta: {p[0]-tx}, {p[1]-ty})")
            
            # Test click
            ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 1)
            ui.syn()
            time.sleep(0.1)
            ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0)
            ui.syn()

        ui.close()
    except Exception as e:
        print(f"[TEST] Error: {e}")

if __name__ == "__main__":
    test_abs_mouse()
