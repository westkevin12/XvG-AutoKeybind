
import time
import sys
import os
from input_engine import EvdevEngine

def verify_sync():
    print("[VERIFY] Starting EvdevEngine...")
    try:
        engine = EvdevEngine()
    except Exception as e:
        print(f"[VERIFY] Failed to init engine: {e}")
        return

    # Targets to click
    targets = [(500, 500), (1000, 800)]
    
    print("[VERIFY] Running synchronized clicks...")
    for x, y in targets:
        print(f"[VERIFY] Clicking at ({x}, {y})...")
        engine.simulation_click(x, y, 'left')
        time.sleep(1)
        
    print("[VERIFY] Verification complete.")
    engine.stop_listeners()

if __name__ == "__main__":
    verify_sync()
