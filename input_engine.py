
import abc
import threading
import time
import sys
import os
import platform
from typing import Callable, Optional, Set

try:
    from pynput.keyboard import Key, Listener, Controller, KeyCode
    from pynput.mouse import Controller as MouseController, Button
except ImportError:
    pass 

# Conditional Import for Evdev
try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
except ImportError:
    evdev = None

class InputEngine(abc.ABC):
    """
    Abstract base class for Input Handling (Sniffing and Injection).
    """
    def __init__(self):
        self.on_press_callback = None
        self.on_release_callback = None
        self.is_running = False

    @abc.abstractmethod
    def start_listeners(self, on_press: Callable, on_release: Callable):
        pass

    @abc.abstractmethod
    def stop_listeners(self):
        pass
    
    @abc.abstractmethod
    def get_current_position(self):
        pass

    @abc.abstractmethod
    def simulation_click(self, x: int, y: int, button='left'):
        pass

    @abc.abstractmethod
    def simulation_move(self, x: int, y: int):
        pass

    @abc.abstractmethod
    def simulation_mouse_down(self, button='left'):
        pass

    @abc.abstractmethod
    def simulation_mouse_up(self, button='left'):
        pass

    @abc.abstractmethod
    def simulation_text(self, text: str, delay_mode: str = 'static', 
                       delay_static: float = 0.05, delay_min: float = 0.05, 
                       delay_max: float = 0.15, kill_switch_checker: Callable = None):
        pass
    
    @abc.abstractmethod
    def simulation_key(self, key_string: str):
        pass
        
    def is_healthy(self):
        """Returns True if the engine is running properly."""
        return self.is_running


class PynputEngine(InputEngine):
    """
    Implementation using pynput (Best for Windows/X11).
    """
    def __init__(self):
        super().__init__()
        self.keyboard_listener = None
        self.keyboard_controller = Controller()
        
    def is_healthy(self):
        if not self.is_running: return False
        if self.keyboard_listener and not self.keyboard_listener.is_alive():
            return False
        return True
        
    def start_listeners(self, on_press: Callable, on_release: Callable):
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        self.is_running = True
        
        self.keyboard_listener = Listener(on_press=self._on_press, on_release=self._on_release)
        self.keyboard_listener.start()
        
    def stop_listeners(self):
        self.is_running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
    def _on_press(self, key):
        if self.on_press_callback:
            self.on_press_callback(key)
            
    def _on_release(self, key):
        if self.on_release_callback:
            self.on_release_callback(key)

    def simulation_text(self, text: str, delay_mode: str = 'static', 
                        delay_static: float = 0.05, delay_min: float = 0.05, 
                        delay_max: float = 0.15, kill_switch_checker: Callable = None):
        import random
        for char in text:
            if kill_switch_checker and kill_switch_checker():
                return

            try:
                if char == '\n':
                    self.keyboard_controller.press(Key.enter)
                    self.keyboard_controller.release(Key.enter)
                else:
                    self.keyboard_controller.type(char)
            except Exception as e:
                print(f"[Pynput] Error typing char '{char}': {e}")
            
            if delay_mode == 'static':
                time.sleep(delay_static)
            elif delay_mode == 'random':
                time.sleep(random.uniform(delay_min, delay_max))

    def simulation_click(self, x: int, y: int, button='left'):
        import pyautogui
        pyautogui.click(x, y, button=button)

    def simulation_move(self, x: int, y: int):
        import pyautogui
        pyautogui.moveTo(x, y)

    def simulation_mouse_down(self, button='left'):
        import pyautogui
        pyautogui.mouseDown(button=button)

    def simulation_mouse_up(self, button='left'):
        import pyautogui
        pyautogui.mouseUp(button=button)

    def simulation_key(self, key_string: str):
        print(f"[Pynput] Simulating Key: {key_string}")
        try:
            if hasattr(Key, key_string):
                k = getattr(Key, key_string)
                self.keyboard_controller.press(k)
                time.sleep(0.01)
                self.keyboard_controller.release(k)
            else:
                self.keyboard_controller.press(key_string)
                time.sleep(0.01)
                self.keyboard_controller.release(key_string)
        except Exception as e:
            print(f"[Pynput] Error simulating key '{key_string}': {e}")


class EvdevEngine(InputEngine):
    """
    Implementation using evdev (Best for Linux/Wayland).
    """
    def __init__(self):
        super().__init__()
        if not evdev:
            raise ImportError("evdev library not found.")
        self.uinput_kb = None 
        self.uinput_mouse = None
        self._pynput_mouse = None
        self._pynput_kb = None
        try:
            from pynput.mouse import Controller as MouseController
            from pynput.keyboard import Controller as KBController
            self._pynput_mouse = MouseController()
            self._pynput_kb = KBController()
        except ImportError:
            pass
            
        self.stop_event = threading.Event()
        self.thread = None
        
        # Mapping for Injection (Char -> Ecode)
        # This is a basic US Layout mapping
        self.char_map = {
            'a': ecodes.KEY_A, 'b': ecodes.KEY_B, 'c': ecodes.KEY_C, 'd': ecodes.KEY_D,
            'e': ecodes.KEY_E, 'f': ecodes.KEY_F, 'g': ecodes.KEY_G, 'h': ecodes.KEY_H,
            'i': ecodes.KEY_I, 'j': ecodes.KEY_J, 'k': ecodes.KEY_K, 'l': ecodes.KEY_L,
            'm': ecodes.KEY_M, 'n': ecodes.KEY_N, 'o': ecodes.KEY_O, 'p': ecodes.KEY_P,
            'q': ecodes.KEY_Q, 'r': ecodes.KEY_R, 's': ecodes.KEY_S, 't': ecodes.KEY_T,
            'u': ecodes.KEY_U, 'v': ecodes.KEY_V, 'w': ecodes.KEY_W, 'x': ecodes.KEY_X,
            'y': ecodes.KEY_Y, 'z': ecodes.KEY_Z,
            '1': ecodes.KEY_1, '2': ecodes.KEY_2, '3': ecodes.KEY_3, '4': ecodes.KEY_4,
            '5': ecodes.KEY_5, '6': ecodes.KEY_6, '7': ecodes.KEY_7, '8': ecodes.KEY_8,
            '9': ecodes.KEY_9, '0': ecodes.KEY_0,
            '\n': ecodes.KEY_ENTER, ' ': ecodes.KEY_SPACE,
            '\t': ecodes.KEY_TAB, '\x1b': ecodes.KEY_ESC,
            '.': ecodes.KEY_DOT, ',': ecodes.KEY_COMMA, '/': ecodes.KEY_SLASH,
            '-': ecodes.KEY_MINUS, '=': ecodes.KEY_EQUAL,
            '[': ecodes.KEY_LEFTBRACE, ']': ecodes.KEY_RIGHTBRACE,
            '\\': ecodes.KEY_BACKSLASH, ';': ecodes.KEY_SEMICOLON, '\'': ecodes.KEY_APOSTROPHE,
            '`': ecodes.KEY_GRAVE
        }
        
        self._setup_uinput()

    def get_current_position(self):
        """Unified pixel-perfect coordinate source (Wayland Compatible)."""
        if self._pynput_mouse:
            return self._pynput_mouse.position
        import pyautogui
        return pyautogui.position()
        
    def is_healthy(self):
        if not self.is_running: return False
        if self.thread and not self.thread.is_alive():
             return False
        return True

    def _setup_uinput(self):
        # 1. Keyboard Device (Macro Injection)
        kb_keys = list(range(ecodes.KEY_RESERVED, ecodes.KEY_PRINT))
        kb_cap = {
            ecodes.EV_KEY: kb_keys,
            ecodes.EV_MSC: [ecodes.MSC_SCAN],
        }
        
        # 2. Mouse Device (Button + Absolute + Relative Injection)
        # We include Absolute (EV_ABS) for Wayland pixel-perfect sync
        # and Relative (EV_REL) for cross-compatibility.
        
        # Get Screen Size for Absolute Mapping
        try:
            import pyautogui
            width, height = pyautogui.size()
        except:
            width, height = 1920, 1080 # Fallback

        mouse_cap = {
            ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE, ecodes.BTN_SIDE, ecodes.BTN_EXTRA],
            ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y, ecodes.REL_WHEEL],
            ecodes.EV_ABS: [
                (ecodes.ABS_X, evdev.AbsInfo(value=0, min=0, max=width, fuzz=0, flat=0, resolution=1)),
                (ecodes.ABS_Y, evdev.AbsInfo(value=0, min=0, max=height, fuzz=0, flat=0, resolution=1)),
            ]
        }
        
        try:
            self.uinput_kb = evdev.UInput(kb_cap, name="XvG-Macro-Keyboard")
            self.uinput_mouse = evdev.UInput(mouse_cap, name="XvG-Virtual-Mouse")
            time.sleep(1.0) # Registration delay
            print(f"[INFO] Kernel-level input devices initialized (KB + Mouse {width}x{height})")
        except OSError as e:
            print(f"[Evdev] Error: Cannot open /dev/uinput: {e}", file=sys.stderr)
            raise 

    def _is_keyboard(self, device):
        caps = device.capabilities()
        if ecodes.EV_KEY not in caps: return False
        
        # Check for ANY common keyboard key, not just KEY_A
        # This is more robust for keypads or non-standard keyboards.
        common_keys = [
            ecodes.KEY_A, ecodes.KEY_Z, ecodes.KEY_0, ecodes.KEY_9, 
            ecodes.KEY_SPACE, ecodes.KEY_ENTER, ecodes.KEY_ESC
        ]
        supported_keys = caps[ecodes.EV_KEY]
        for k in common_keys:
            if k in supported_keys:
                return True
        return False

    def _is_mouse(self, device):
        caps = device.capabilities()
        if ecodes.EV_KEY in caps:
            if ecodes.BTN_LEFT in caps[ecodes.EV_KEY]:
                return True
            if ecodes.BTN_MOUSE in caps[ecodes.EV_KEY]:
                return True
        return False

    def capture_single_click(self, callback):
        def _run():
            import sys
            try:
                import asyncio
                import pyautogui
                

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    paths = evdev.list_devices()
                    mice = []
                    for path in paths:
                        try:
                            d = evdev.InputDevice(path)
                            if self._is_mouse(d):
                                mice.append(d)
                        except: continue
                except Exception as e: 
                    print(f"[Evdev] ERROR: Scan failed: {e}", file=sys.stderr)
                    return
                
                if not mice:
                    print("[Evdev] ERROR: No mice found for capture!", file=sys.stderr)
                    return

                stop_event = asyncio.Event()

                async def monitor(dev):
                    try:
                        async for event in dev.async_read_loop():
                             if stop_event.is_set(): break
                             if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_LEFT and event.value == 1:
                                 stop_event.set()
                                 # Standardize on Pynput for coordinate truth on Wayland
                                 x, y = self.get_current_position()
                                 callback(x, y, 'left', True)
                                 return
                    except Exception as e:
                        # Device might disconnect or error out
                        pass

                tasks = [loop.create_task(monitor(m)) for m in mice]
                try:
                    loop.run_until_complete(asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED))
                finally:
                    # Explicitly cancel pending tasks to avoid "Task was destroyed but it is pending!"
                    for task in tasks:
                        task.cancel()
                    
                    # Gracefully wait for cancellations
                    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                    
                    loop.close()
                    for m in mice: m.close()
            except Exception as e:
                import traceback
                traceback.print_exc(file=sys.stderr)
                print(f"[Evdev] FATAL THREAD ERROR: {e}", file=sys.stderr)

        threading.Thread(target=_run, daemon=True).start()

    def simulation_move(self, x: int, y: int):
        """Moves cursor using hardware injection (UInput) for reliable Wayland synchronization."""
        try:
            if self.uinput_mouse:
                # Inject Hardware Absolute Move
                self.uinput_mouse.write(ecodes.EV_ABS, ecodes.ABS_X, int(x))
                self.uinput_mouse.write(ecodes.EV_ABS, ecodes.ABS_Y, int(y))
                self.uinput_mouse.syn()
                
                # Keep logical pointer updated for app-level queries
                if self._pynput_mouse:
                    self._pynput_mouse.position = (int(x), int(y))
            elif self._pynput_mouse:
                self._pynput_mouse.position = (int(x), int(y))
            else:
                import pyautogui
                pyautogui.moveTo(x, y)
        except Exception as e:
            print(f"[Hybrid] Move failed: {e}", file=sys.stderr)

    def simulation_mouse_down(self, button='left'):
        """Infects mouse down via uinput to ensure background bypass on Wayland."""
        if self.uinput_mouse:
            btn_map = {'left': ecodes.BTN_LEFT, 'right': ecodes.BTN_RIGHT, 'middle': ecodes.BTN_MIDDLE}
            code = btn_map.get(button.lower(), ecodes.BTN_LEFT)
            self.uinput_mouse.write(ecodes.EV_KEY, code, 1)
            self.uinput_mouse.syn()
        else:
            import pyautogui
            pyautogui.mouseDown(button=button)

    def simulation_mouse_up(self, button='left'):
        """Infects mouse up via uinput to ensure background bypass on Wayland."""
        if self.uinput_mouse:
            btn_map = {'left': ecodes.BTN_LEFT, 'right': ecodes.BTN_RIGHT, 'middle': ecodes.BTN_MIDDLE}
            code = btn_map.get(button.lower(), ecodes.BTN_LEFT)
            self.uinput_mouse.write(ecodes.EV_KEY, code, 0)
            self.uinput_mouse.syn()
        else:
            import pyautogui
            pyautogui.mouseUp(button=button)
            
    def simulation_click(self, x: int, y: int, button='left'):
        """Hardware-synced click using consolidated UInput event stream."""
        try:
            # Consolidate Move and Click in immediate succession on the same virtual stream
            self.simulation_move(x, y)
            time.sleep(0.05) # Reduced delay now that we have hardware sync
            self.simulation_mouse_down(button)
            time.sleep(0.05)
            self.simulation_mouse_up(button)
        except Exception as e:
            print(f"[Hybrid] Click failed: {e}", file=sys.stderr)

    def simulation_key(self, key_string: str):
        """Simulates key press via evdev for background macros, falls back to pynput."""
        if self.uinput_kb:
            # Normalize key mapping
            clean_key = key_string.strip().upper()
            mapping = {
                'CTRL_L': 'LEFTCTRL', 'CTRL_R': 'RIGHTCTRL',
                'ALT_L': 'LEFTALT', 'ALT_R': 'RIGHTALT',
                'SHIFT': 'LEFTSHIFT', 'SHIFT_R': 'RIGHTSHIFT',
                'CAPS_LOCK': 'CAPSLOCK', 'ESCAPE': 'ESC',
                'ENTER': 'ENTER', 'TAB': 'TAB', 'SPACE': 'SPACE',
                'BACKSPACE': 'BACKSPACE'
            }
            clean_key = mapping.get(clean_key, clean_key)
            code = getattr(ecodes, f"KEY_{clean_key}", None)
            if code:
                self.uinput_kb.write(ecodes.EV_KEY, code, 1)
                self.uinput_kb.syn()
                time.sleep(0.05)
                self.uinput_kb.write(ecodes.EV_KEY, code, 0)
                self.uinput_kb.syn()
                return

        # Fallback to pynput keyboard
        try:
            if self._pynput_kb:
                self._pynput_kb.press(key_string)
                time.sleep(0.05)
                self._pynput_kb.release(key_string)
        except:
            import pyautogui
            pyautogui.press(key_string)

    def start_listeners(self, on_press, on_release):
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        self.stop_event.clear()
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop_listeners(self):
        self.stop_event.set()
        self.is_running = False
        if self.uinput_kb: self.uinput_kb.close()

    def _run_loop(self):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Check permissions by listing first
            paths = evdev.list_devices()
            devices = []
            for path in paths:
                try:
                    d = evdev.InputDevice(path)
                    devices.append(d)
                except PermissionError:
                    print(f"[Evdev] Warning: Permission denied for {path}")
                    continue
                except Exception as e:
                    continue
            
            keyboards = []
            for d in devices:
                if self._is_keyboard(d):
                    keyboards.append(d)
                    print(f"[Evdev] Monitoring device: {d.name} ({d.path})")
            
            if not keyboards:
                 msg = "[Evdev] No accessible keyboards found! (Check permissions?)"
                 print(msg)
                 self.last_error = msg
                 return
        except Exception as e:
            msg = f"[Evdev] Critical Error scanning devices: {e}"
            print(msg)
            self.last_error = msg
            return

        tasks = [self._monitor_device(dev) for dev in keyboards]
        
        try:
            loop.run_until_complete(asyncio.gather(*tasks))
        except Exception as e:
            msg = f"[Evdev] ERROR in async loop: {e}"
            print(msg)
            self.last_error = msg
        finally:
            loop.close()

    async def _monitor_device(self, device):
        # NOTE: We do NOT use device.grab() here.
        # grab() gives exclusive access, processing keys before the OS.
        # Since we are an AutoKeybind app, we usually want to LISTEN ("sniff")
        # while letting the OS still receive the keys (Passthrough).
        # If we wanted to REMAP (block A, send B), we would need grab().
        try:
            async for event in device.async_read_loop():
                if self.stop_event.is_set(): break
                
                if event.type == ecodes.EV_KEY:
                    # Ignore repeat events (value=2)
                    if event.value == 2: continue
                    
                    pynput_key = self._map_evdev_to_pynput(event.code)
                    
                    if event.value == 1: # Down
                        if self.on_press_callback: self.on_press_callback(pynput_key)
                    elif event.value == 0: # Up
                        if self.on_release_callback: self.on_release_callback(pynput_key)
        except Exception as e:
             # Device might have been unplugged
             print(f"[Evdev] Device {device.name} error: {e}")

    def _map_evdev_to_pynput(self, code):
        # 1. Map Special Keys
        KEY_MAP = {
            ecodes.KEY_ESC: Key.esc,
            ecodes.KEY_ENTER: Key.enter,
            ecodes.KEY_LEFTCTRL: Key.ctrl_l, ecodes.KEY_RIGHTCTRL: Key.ctrl_r,
            ecodes.KEY_LEFTALT: Key.alt_l, ecodes.KEY_RIGHTALT: Key.alt_r,
            ecodes.KEY_LEFTSHIFT: Key.shift, ecodes.KEY_RIGHTSHIFT: Key.shift_r,
            ecodes.KEY_TAB: Key.tab, ecodes.KEY_BACKSPACE: Key.backspace,
            ecodes.KEY_SPACE: Key.space,
            ecodes.KEY_F1: Key.f1, ecodes.KEY_F2: Key.f2, ecodes.KEY_F3: Key.f3,
            ecodes.KEY_F4: Key.f4, ecodes.KEY_F5: Key.f5, ecodes.KEY_F6: Key.f6,
            ecodes.KEY_F7: Key.f7, ecodes.KEY_F8: Key.f8, ecodes.KEY_F9: Key.f9,
            ecodes.KEY_F10: Key.f10, ecodes.KEY_F11: Key.f11, ecodes.KEY_F12: Key.f12,
            ecodes.KEY_UP: Key.up, ecodes.KEY_DOWN: Key.down,
            ecodes.KEY_LEFT: Key.left, ecodes.KEY_RIGHT: Key.right
        }
        
        if code in KEY_MAP:
            return KEY_MAP[code]
            
        # 2. Map Alphanumeric / Others
        try:
            # Use evdev's internal mapping to get key name (e.g., 'KEY_A')
            # ecodes.keys is {code: 'KEY_NAME'} or {code: ['KEY_NAME', ...]}
            key_name_or_list = evdev.ecodes.keys[code]
            key_name = key_name_or_list[0] if isinstance(key_name_or_list, list) else key_name_or_list
            
            clean_name = key_name.replace("KEY_", "").lower()
            
            # Helper for common symbol names
            symbol_map = {
                'min_interesting': 'val',
                'dot': '.', 'comma': ',', 'slash': '/', 'minus': '-', 'equal': '=',
                'leftbrace': '[', 'rightbrace': ']', 'backslash': '\\', 'semicolon': ';',
                'apostrophe': '\'', 'grave': '`'
            }
            if clean_name in symbol_map:
                return KeyCode.from_char(symbol_map[clean_name])
                
            if len(clean_name) == 1:
                return KeyCode.from_char(clean_name)
                
            return KeyCode(vk=code) # Fallback
            
        except:
            return KeyCode(vk=code)

    def release_all_modifiers(self):
        """Helper to force-release common modifiers to prevent interference."""
        if not self.uinput_kb: return
        
        modifiers = [
            ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT,
            ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL,
            ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT,
            ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA
        ]
        
        for mod in modifiers:
            self.uinput_kb.write(ecodes.EV_KEY, mod, 0)
            
        self.uinput_kb.syn()

    def simulation_text(self, text: str, delay_mode='static', delay_static=0.05, delay_min=0.05, delay_max=0.15, kill_switch_checker=None):
        if not self.uinput_kb: return
        
        # Scrub modifiers first to prevent "Alt+Space" issues if user is holding Alt
        self.release_all_modifiers()
        
        import random

        # Extended Mapping for US Layout
        # Char -> (Key Name Suffix, Shift Required)
        # We use a comprehensive map to cover symbols that aren't just A-Z or 0-9
        
        # Base mappings (Copy from existing logic but formalized)
        char_map = {}
        
        # 1. Letters a-z
        for i in range(ord('a'), ord('z') + 1):
            c = chr(i)
            char_map[c] = (c.upper(), False)
            char_map[c.upper()] = (c.upper(), True)
            
        # 2. Numbers 0-9
        for i in range(0, 10):
            s = str(i)
            char_map[s] = (s, False)
            
        # 3. Special Symbols (US Layout)
        # Format: Symbol: (KeySuffix, Shift)
        special_map = {
            ' ': ('SPACE', False), '\n': ('ENTER', False), '\t': ('TAB', False), '\x1b': ('ESC', False),
            '`': ('GRAVE', False), '~': ('GRAVE', True),
            '-': ('MINUS', False), '_': ('MINUS', True),
            '=': ('EQUAL', False), '+': ('EQUAL', True),
            '[': ('LEFTBRACE', False), '{': ('LEFTBRACE', True),
            ']': ('RIGHTBRACE', False), '}': ('RIGHTBRACE', True),
            '\\': ('BACKSLASH', False), '|': ('BACKSLASH', True),
            ';': ('SEMICOLON', False), ':': ('SEMICOLON', True),
            '\'': ('APOSTROPHE', False), '"': ('APOSTROPHE', True),
            ',': ('COMMA', False), '<': ('COMMA', True),
            '.': ('DOT', False), '>': ('DOT', True),
            '/': ('SLASH', False), '?': ('SLASH', True),
            '!': ('1', True), '@': ('2', True), '#': ('3', True), '$': ('4', True),
            '%': ('5', True), '^': ('6', True), '&': ('7', True), '*': ('8', True),
            '(': ('9', True), ')': ('0', True)
        }
        char_map.update(special_map)

        for char in text:
            if kill_switch_checker and kill_switch_checker(): return
            
            mapping = char_map.get(char)
            if not mapping:
                # Fallback check?
                print(f"[Evdev] Warning: No mapping for char '{char}'")
                continue
                
            suffix, shift_needed = mapping
            code = ecodes.ecodes.get(f"KEY_{suffix}")
            
            if code:
                if shift_needed:
                    self.uinput_kb.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
                    self.uinput_kb.syn()
                    
                self.uinput_kb.write(ecodes.EV_KEY, code, 1)
                self.uinput_kb.syn()
                self.uinput_kb.write(ecodes.EV_KEY, code, 0)
                self.uinput_kb.syn()
                
                if shift_needed:
                    self.uinput_kb.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
                    self.uinput_kb.syn()
                
            if delay_mode == 'static': time.sleep(delay_static)
            elif delay_mode == 'random': time.sleep(random.uniform(delay_min, delay_max))

