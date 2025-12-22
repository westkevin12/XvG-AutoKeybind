import pyautogui
from pynput.keyboard import Listener
from pynput.mouse import Listener as MouseListener
import tkinter as tk
from tkinter import Entry, Button, Label, Listbox, messagebox, simpledialog
import threading
import pystray
from PIL import Image, ImageTk
import os
import sys
import json

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

        # Key Entry Section
        tk.Label(main_frame, text="Enter Key:").pack(pady=(0, 5))
        self.key_entry = Entry(main_frame)
        self.key_entry.pack(fill=tk.X, pady=(0, 10))

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
        self.add_keybind_mode = True
        self.key_entry.delete(0, tk.END)
        self.add_button.config(state=tk.DISABLED, text="Press Key & Click...")
        self.update_status("Press a key then click a location...")

    def click_coordinate(self, x, y):
        original_position = pyautogui.position()
        pyautogui.click(x, y)
        pyautogui.moveTo(original_position)

    def on_key_release(self, key):
        try:
            key_str = getattr(key, 'char', None) # Handle special keys gracefully
            if not key_str: return

            if self.active_profile and key_str in self.profiles[self.active_profile]['keybinds']:
                index = self.profiles[self.active_profile]['keybinds'][key_str]
                if 0 <= index < len(self.coords):
                    x, y = self.coords[index]
                    self.click_coordinate(x, y)
        except Exception:
            pass 

    def capture_mouse_position(self, x, y, button, pressed):
        pass

    def on_click(self, x, y, button, pressed):
        if pressed and self.add_keybind_mode:
            self.coords.append((x, y))
            
            # Save bind
            profile_data = self.profiles[self.active_profile]
            profile_data['keybinds'][self.pending_key] = len(self.coords) - 1
            self.save_profiles()
            
            # Reset UI
            self.key_entry.delete(0, tk.END)
            self.add_keybind_mode = False
            self.add_button.config(state=tk.NORMAL, text="Add Keybind")
            self.update_status(f"Bound '{self.pending_key}' to ({x}, {y})")

    # Connect listeners
    def start_listeners(self):
        self.keyboard_listener = Listener(on_release=self.on_key_release)
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
        win.geometry("300x300")
        
        lb = Listbox(win)
        lb.pack(fill=tk.BOTH, expand=True)

        current_binds = self.profiles[self.active_profile]['keybinds']
        for key, val in current_binds.items():
             lb.insert(tk.END, f"Key '{key}' -> {val}")

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

