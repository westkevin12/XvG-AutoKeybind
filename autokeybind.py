import pyautogui
from pynput.keyboard import Listener, Key, KeyCode
from pynput.mouse import Listener as MouseListener, Button as MouseButton, Controller as MouseController
import tkinter as tk
from tkinter import Entry, Button, Label, Listbox, messagebox, simpledialog, ttk
import threading
import pystray
from PIL import Image, ImageTk
import os
import sys
import json
import time
from key_utils import get_key_name, get_key_combo_string

# Action Types Constant
ACTION_CLICK_RETURN = "Click & Return"
ACTION_CLICK_STAY = "Click & Stay"
ACTION_DOUBLE_CLICK_RETURN = "Double Click & Return"
ACTION_DRAG_RETURN = "Drag & Return"

ACTION_TYPES = [
    ACTION_CLICK_RETURN,
    ACTION_CLICK_STAY,
    ACTION_DOUBLE_CLICK_RETURN,
    ACTION_DRAG_RETURN
]




class AddKeybindDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Keybind")
        self.geometry("300x250")
        self.result = None
        
        self.pressed_keys = set()
        self.listener = None
        
        tk.Label(self, text="Key Combination:", font=("Arial", 10)).pack(pady=(10, 5))
        
        self.key_display_var = tk.StringVar(value="None")
        self.display_lbl = tk.Label(self, textvariable=self.key_display_var, font=("Arial", 14, "bold"), relief="sunken", bg="white", width=20)
        self.display_lbl.pack(pady=(0, 10), ipady=10)
        
        self.record_btn = Button(self, text="Record Key", command=self.toggle_recording)
        self.record_btn.pack(pady=(0, 15))
        
        tk.Label(self, text="Action Type:").pack()
        self.action_var = tk.StringVar(value=ACTION_CLICK_RETURN)
        self.type_combo = ttk.Combobox(self, textvariable=self.action_var, values=ACTION_TYPES, state="readonly")
        self.type_combo.pack(pady=(0, 15))
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)
        
        Button(btn_frame, text="Set Location", command=self.on_ok).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def toggle_recording(self):
        if self.listener:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.pressed_keys.clear()
        self.key_display_var.set("Press keys...")
        self.record_btn.config(text="Stop Recording", bg="#ffcccc")
        
        self.listener = Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def stop_recording(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.record_btn.config(text="Record Key", bg="SystemButtonFace")
        
    def on_press(self, key):
        self.pressed_keys.add(key)
        self.update_display()
        
    def on_release(self, key):
        if key in self.pressed_keys:
            # We don't remove from set immediately during recording to allow "Ctrl+A" logic 
            # effectively logic captures the "Max" combo active.
            # But simpler: Remove it to show current state?
            # User wants to capture a "Stroke".
            # Let's stop recording when ALL keys are released if at least one was pressed.
            pass
            
        # Check if all keys are released to auto-stop? 
        # Actually, let's just show what's currently held.
        # But if user holds Ctrl, then presses A, then releases A, then releases Ctrl.
        # Max combo was Ctrl+A.
        # If I remove A on release, display goes back to Ctrl.
        # If I stop on release?
        pass
        
    def update_display(self):
        combo = get_key_combo_string(self.pressed_keys)
        if combo:
            self.after(0, lambda: self.key_display_var.set(combo))

    def on_close(self):
        self.stop_recording()
        self.destroy()

    def on_ok(self):
        self.stop_recording()
        key = self.key_display_var.get()
        if not key or key == "None" or key == "Press keys...":
            messagebox.showwarning("Input Required", "Please record a key combination.")
            return
        self.result = (key, self.action_var.get())
        self.destroy()

class KeybindApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XvG Auto Keybind")
        self.root.wm_attributes("-topmost", 1)
        self.root.geometry("300x550")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Application State
        self.profiles = {}
        self.coords = []
        self.active_profile = None
        self.add_keybind_mode = False
        self.pending_key = None
        self.pending_action_type = None
        
        self.current_pressed_keys = set()
        
        # Mouse Controller for advanced actions
        self.mouse = MouseController()
        
        # Load Data
        self.load_profiles()

        # Setup UI
        self.setup_ui()

        # Setup System Tray
        self.setup_tray_icon()

        # Start Input Listeners
        self.start_listeners()

    def load_profiles(self):
        self.profiles = {}
        default_profile_name = "Default"
        
        if os.path.exists('profiles.json'):
            try:
                with open('profiles.json', 'r') as file:
                    self.profiles = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                pass # Handle empty or corrupt file gracefully

        if not self.profiles:
             self.profiles = {default_profile_name: {'keybinds': {}}}
        
        # Ensure active profile is valid
        if self.active_profile not in self.profiles:
            if default_profile_name in self.profiles:
                self.active_profile = default_profile_name
            else:
                self.active_profile = list(self.profiles.keys())[0]
        
        self.save_profiles() # Ensure consistent state on disk

    def save_profiles(self):
        with open('profiles.json', 'w') as file:
            json.dump(self.profiles, file, indent=4)

    def setup_ui(self):
        # Icon
        self.set_window_icon()

        # Main Layout Frame
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Action Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.add_button = Button(button_frame, text="Add Keybind", command=self.add_keybind)
        self.add_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.reset_button = Button(button_frame, text="Reset Profile", command=self.clear_keybinds)
        self.reset_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        self.view_binds_button = Button(main_frame, text="View/Edit Binds", command=self.show_keybinds)
        self.view_binds_button.pack(fill=tk.X, pady=(0, 20))

        # Profile Section
        tk.Label(main_frame, text="Profiles:").pack(anchor=tk.W)
        self.profile_listbox = Listbox(main_frame, selectmode=tk.SINGLE, height=6)
        self.profile_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.profile_listbox.bind("<<ListboxSelect>>", self.activate_profile)
        self.refresh_profile_list()

        # Profile Buttons
        profile_btn_frame = tk.Frame(main_frame)
        profile_btn_frame.pack(fill=tk.X, pady=(0, 10))

        Button(profile_btn_frame, text="Add", command=self.add_profile_action).pack(side=tk.LEFT, fill=tk.X, expand=True)
        Button(profile_btn_frame, text="Rename", command=self.rename_profile_action).pack(side=tk.LEFT, fill=tk.X, expand=True)
        Button(profile_btn_frame, text="Remove", command=self.remove_profile_action).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Active Profile: {self.active_profile}")
        status_label = Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#f0f0f0")
        status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def set_window_icon(self):
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
            else:
                icon_path = 'icon.ico'
            
            if os.path.exists(icon_path):
                icon = Image.open(icon_path)
                icon_photo = ImageTk.PhotoImage(icon)
                self.root.tk.call('wm', 'iconphoto', self.root._w, icon_photo)
        except Exception as e:
            print(f"Failed to load icon: {e}")

    def refresh_profile_list(self):
        self.profile_listbox.delete(0, tk.END)
        for profile_name in self.profiles:
            self.profile_listbox.insert(tk.END, profile_name)
            if profile_name == self.active_profile:
                self.profile_listbox.selection_set(tk.END)

    def update_status(self, message):
         self.status_var.set(message)

    # --- Logic Methods ---

    def add_keybind(self):
        dialog = AddKeybindDialog(self.root)
        if dialog.result:
            key, action_type = dialog.result
            self.pending_key = key
            self.pending_action_type = action_type
            
            self.add_keybind_mode = True
            self.add_button.config(state=tk.DISABLED, text="Click on Screen...")
            self.update_status(f"Click anywhere to bind '{key}' ({action_type})...")

    def perform_action(self, x, y, action_type):
        original_position = pyautogui.position()
        
        if action_type == ACTION_CLICK_RETURN:
            pyautogui.click(x, y)
            pyautogui.moveTo(original_position)
            
        elif action_type == ACTION_CLICK_STAY:
            pyautogui.click(x, y)
            # Do not return
            
        elif action_type == ACTION_DOUBLE_CLICK_RETURN:
            pyautogui.doubleClick(x, y)
            pyautogui.moveTo(original_position)
            
        elif action_type == ACTION_DRAG_RETURN:
            # Move to target, hold down, move back, release
            pyautogui.moveTo(x, y)
            pyautogui.mouseDown()
            time.sleep(0.1) # Small delay for stability
            pyautogui.moveTo(original_position)
            pyautogui.mouseUp()
            
        else:
            # Fallback
            pyautogui.click(x, y)
            pyautogui.moveTo(original_position)

    def on_key_press(self, key):
        self.current_pressed_keys.add(key)
        self.check_and_perform_action()

    def on_key_release(self, key):
        if key in self.current_pressed_keys:
            self.current_pressed_keys.remove(key)

    def check_and_perform_action(self):
        if not self.active_profile:
            return

        current_combo_str = get_key_combo_string(self.current_pressed_keys)
        
        # Check against binds
        # We also need to check "Legacy" single keys just in case, but get_key_combo_string should handle single keys too (e.g. "A")
        
        binds = self.profiles[self.active_profile]['keybinds']
        
        if current_combo_str in binds:
             self.execute_bind(binds[current_combo_str])
             return
        
        # Fallback for legacy binds (often lowercase)
        # Note: This might match "a" when "A" is pressed, which is usually desired for simple binds.
        if current_combo_str.lower() in binds:
             self.execute_bind(binds[current_combo_str.lower()])
             return
             
        # Fallback check for single keys if combo string includes modifiers but bind is simple?
        # No, strict matching is better.
        
    def execute_bind(self, bind_data):
        if isinstance(bind_data, list):
            coords = bind_data
            action_type = ACTION_CLICK_RETURN
        else:
            coords = bind_data.get('coords')
            action_type = bind_data.get('type', ACTION_CLICK_RETURN)
        
        if coords and len(coords) == 2:
            self.perform_action(coords[0], coords[1], action_type)

    def on_click(self, x, y, button, pressed):
        if pressed and self.add_keybind_mode and self.pending_key:
             self.root.after(0, lambda: self.handle_click_main_thread(x, y))

    def handle_click_main_thread(self, x, y):
        # Data Structure: { "coords": [x, y], "type": "Action Name" }
        bind_data = {
            "coords": [x, y],
            "type": self.pending_action_type
        }
        
        # Save bind
        profile_data = self.profiles[self.active_profile]
        profile_data['keybinds'][self.pending_key] = bind_data
        self.save_profiles()
        
        # Reset UI
        self.add_keybind_mode = False
        self.pending_key = None
        self.pending_action_type = None
        self.add_button.config(state=tk.NORMAL, text="Add Keybind")
        self.update_status(f"Bound '{self.active_profile}' to ({x}, {y})")

    # Connect listeners
    def start_listeners(self):
        self.keyboard_listener = Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.mouse_listener = MouseListener(on_click=self.on_click)
        
        self.keyboard_listener.start()
        self.mouse_listener.start()

    # Profile Management methods
    def add_profile_action(self):
        name = simpledialog.askstring("Add Profile", "Enter Profile Name:")
        if name:
            if name in self.profiles:
                messagebox.showerror("Error", "Profile already exists.")
                return
            self.profiles[name] = {'keybinds': {}}
            self.save_profiles()
            self.refresh_profile_list()
            self.update_status(f"Created profile '{name}'")

    def remove_profile_action(self):
        name = self.get_selected_profile()
        if name:
            if name == "Default" and len(self.profiles) == 1:
                messagebox.showwarning("Warning", "Cannot delete the last profile.")
                return
            
            if messagebox.askyesno("Confirm", f"Remove profile '{name}'?"):
                del self.profiles[name]
                
                if self.active_profile == name:
                    self.active_profile = list(self.profiles.keys())[0] # Switch to another
                
                self.save_profiles()
                self.refresh_profile_list()
                self.update_status(f"Removed profile '{name}'")

    def rename_profile_action(self):
        name = self.get_selected_profile()
        if name:
            new_name = simpledialog.askstring("Rename", f"New name for '{name}':")
            if new_name and new_name not in self.profiles:
                self.profiles[new_name] = self.profiles.pop(name)
                if self.active_profile == name:
                    self.active_profile = new_name
                self.save_profiles()
                self.refresh_profile_list()
                self.update_status(f"Renamed '{name}' to '{new_name}'")

    def get_selected_profile(self):
        selection = self.profile_listbox.curselection()
        if selection:
            return self.profile_listbox.get(selection[0])
        return None

    def activate_profile(self, event):
        selection = self.get_selected_profile()
        if selection:
            self.active_profile = selection
            self.update_status(f"Active Profile: {self.active_profile}")

    def clear_keybinds(self):
        if messagebox.askyesno("Confirm", f"Clear all keybinds in '{self.active_profile}'?"):
            self.profiles[self.active_profile]['keybinds'].clear()
            self.save_profiles()
            self.update_status("Keybinds cleared.")

    def show_keybinds(self):
        win = tk.Toplevel(self.root)
        win.title(f"Keybinds: {self.active_profile}")
        win.geometry("400x300")
        
        lb = Listbox(win)
        lb.pack(fill=tk.BOTH, expand=True)

        current_binds = self.profiles[self.active_profile]['keybinds']
        for key, val in current_binds.items():
             # Display format depends on version
             if isinstance(val, list):
                 display_text = f"Key '{key}' -> Coord: {val} (Legacy)"
             else:
                 coords = val.get('coords')
                 action = val.get('type')
                 display_text = f"Key '{key}' -> {action} @ {coords}"
                 
             lb.insert(tk.END, display_text)

    def on_close(self):
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
        self.tray_icon.stop()
        self.root.destroy()
        sys.exit(0)

    # System Tray
    def setup_tray_icon(self):
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = 'icon.ico'
        
        image = Image.open(icon_path) if os.path.exists(icon_path) else Image.new('RGB', (64, 64), color='red')
        
        menu = (pystray.MenuItem('Exit', lambda: self.root.after(0, self.on_close)),)
        self.tray_icon = pystray.Icon("AutoKeybind", image, "XvG AutoKeybind", menu)
        
        # Run in separate thread so it doesn't block TK
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = KeybindApp(root)
    root.mainloop()
