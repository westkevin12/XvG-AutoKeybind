
import evdev
from evdev import ecodes
import sys

def dump_device(path):
    try:
        dev = evdev.InputDevice(path)
        print(f"Name: {dev.name}")
        print(f"ID: bus={dev.info.bustype}, vendor={dev.info.vendor}, product={dev.info.product}, version={dev.info.version}")
        
        caps = dev.capabilities()
        for cap, type_caps in caps.items():
            cap_name = ecodes.EV.get(cap, str(cap))
            print(f"Cap type: {cap_name} ({cap})")
            for c in type_caps:
                if isinstance(c, tuple):
                    code, info = c
                    code_name = ecodes.bytype.get(cap, {}).get(code, str(code))
                    print(f"  {code_name} ({code}): {info}")
                else:
                    code_name = ecodes.bytype.get(cap, {}).get(c, str(c))
                    print(f"  {code_name} ({c})")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        dump_device(sys.argv[1])
    else:
        for i in range(20):
            try:
                p = f"/dev/input/event{i}"
                d = evdev.InputDevice(p)
                if "Razer" in d.name:
                    print(f"\n--- DUMPING {p} ---")
                    dump_device(p)
            except:
                continue
