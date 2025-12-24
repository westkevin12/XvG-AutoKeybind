import pyautogui
from pynput.keyboard import Listener, Key, KeyCode
from pynput.mouse import Listener as MouseListener, Button as MouseButton, Controller as MouseController
import tkinter as tk
from tkinter import Entry, Listbox, messagebox, simpledialog, ttk
import tkinter as tk
from tkinter.ttk import Button, Label, Frame, Style
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





class KeybindEditorDialog(tk.Toplevel):
    def __init__(self, parent, edit_mode=False, current_key=None, current_data=None):
        super().__init__(parent)
        self.title("Edit Keybind" if edit_mode else "Add Keybind")
        self.geometry("400x450")
        self.resizable(False, True)
        self.result = None
        self.edit_mode = edit_mode
        
        self.pressed_keys = set()
        self.listener = None
        
        # Main Frame
        main_frame = Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Key Section
        Label(main_frame, text="Key Combination:", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        self.key_display_var = tk.StringVar(value=current_key if current_key else "None")
        self.display_lbl = Label(main_frame, textvariable=self.key_display_var, font=("Segoe UI", 14, "bold"), relief="sunken", background="white", anchor="center")
        self.display_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipady=10)
        
        self.record_btn = Button(main_frame, text="Record Key", command=self.toggle_recording)
        self.record_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # 2. Action Section
        Label(main_frame, text="Action Type:", style="Header.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        initial_action = current_data.get('type', ACTION_CLICK_RETURN) if current_data else ACTION_CLICK_RETURN
        self.action_var = tk.StringVar(value=initial_action)
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.action_var, values=ACTION_TYPES, state="readonly", font=("Segoe UI", 10))
        self.type_combo.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # 3. Location info
        current_coords = current_data.get('coords') if current_data else None
        self.coords_var = tk.StringVar(value=f"Location: {current_coords}" if current_coords else "Location: Not Set")
        Label(main_frame, textvariable=self.coords_var, foreground="#666").grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # 4. Update Location Checkbox (Only for Edit Mode)
        self.update_loc_var = tk.BooleanVar(value=False)
        if edit_mode:
            ttk.Checkbutton(main_frame, text="Update/Reset Location (Click on Save)", variable=self.update_loc_var).grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Bottom Buttons
        btn_frame = Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ok_text = "Save Changes" if edit_mode else "Set Location & Save"
        Button(btn_frame, text=ok_text, command=self.on_ok).pack(side=tk.RIGHT, padx=(10, 0))
        Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)
        self.grab_set()
        
        # If editing, we just wait. If adding, we wait.
        self.wait_window(self)

    def toggle_recording(self):
        if self.listener:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.pressed_keys.clear()
        self.key_display_var.set("Press keys...")
        self.record_btn.configure(text="Stop Recording") # Style change handled by theme usually, or we can use state
        
        self.listener = Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def stop_recording(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.record_btn.configure(text="Record Key")
        
    def on_press(self, key):
        self.pressed_keys.add(key)
        self.update_display()
        
    def on_release(self, key):
        if key in self.pressed_keys:
            # Optional: Auto-stop on full release? For now, manual stop is safer for complex combos.
            pass
        
    def update_display(self):
        combo = get_key_combo_string(self.pressed_keys)
        if combo:
            self.display_lbl.after(0, lambda: self.key_display_var.set(combo))

    def on_close(self):
        self.stop_recording()
        self.destroy()

    def on_ok(self):
        self.stop_recording()
        key = self.key_display_var.get()
        if not key or key == "None" or key == "Press keys...":
            messagebox.showwarning("Input Required", "Please record a key combination.")
            return
            
        # If we are editing and didn't change location, we keep old coords?
        # The logic in KeybindApp handles setting location for new binds.
        # For edits, if we want to change location, we might need a separate button?
        # The current flow "Set Location & Save" implies re-setting location.
        # Let's assume OK always returns data, and App handles what to do.
        
        # Return format: (Key, Action, ShouldUpdateLocation)
        # For Add mode, ShouldUpdateLocation is implicitly True usually, but we can make it explicit.
        should_update = self.update_loc_var.get() if self.edit_mode else True
        
        self.result = (key, self.action_var.get(), should_update)
        self.destroy()

class KeybindApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XvG Auto Keybind")
        self.root.wm_attributes("-topmost", 1)
        
        # Setup Styles
        self.style = Style()
        try:
            self.style.theme_use('clam')
        except:
            pass # Fallback if clam not available
        self.style.configure('TButton', font=('Segoe UI', 10), padding=5)
        self.style.configure('TLabel', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))

        self.root.geometry("300x550")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Application State
        self.profiles = {}
        self.coords = []
        self.active_profile = None
        self.add_keybind_mode = False
        self.pending_action_type = None
        self.mini_mode = False
        self.normal_geometry = "300x550"
        
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
        self.main_frame = Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Action Buttons
        button_frame = Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Big Add Button
        self.add_button = ttk.Button(button_frame, text="Add Keybind", command=self.add_keybind)
        self.add_button.pack(fill=tk.X, ipady=5)
        
        self.view_binds_button = ttk.Button(self.main_frame, text="Manage Binds", command=self.show_keybinds)
        self.view_binds_button.pack(fill=tk.X, pady=(0, 20), ipady=5)

        # Profile Section
        ttk.Label(self.main_frame, text="Active Profile:", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        self.profile_frame = Frame(self.main_frame)
        self.profile_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(self.profile_frame)
        self.profile_listbox = Listbox(self.profile_frame, selectmode=tk.SINGLE, height=6, relief="flat", borderwidth=1, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.profile_listbox.yview)
        
        self.profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.profile_listbox.bind("<<ListboxSelect>>", self.activate_profile)
        self.refresh_profile_list()

        # Profile Buttons
        profile_btn_frame = Frame(self.main_frame)
        profile_btn_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Button(profile_btn_frame, text="New", width=6, command=self.add_profile_action).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(profile_btn_frame, text="Rename", width=8, command=self.rename_profile_action).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(profile_btn_frame, text="Delete", width=8, command=self.remove_profile_action).pack(side=tk.LEFT)
        
        # Mini Mode / Reset
        bottom_frame = Frame(self.main_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(bottom_frame, text="Toggle Mini Mode", command=self.toggle_mini_mode).pack(side=tk.LEFT)
        ttk.Button(bottom_frame, text="Clear All", command=self.clear_keybinds).pack(side=tk.RIGHT)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Active Profile: {self.active_profile}")
        self.status_label = Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def toggle_mini_mode(self):
        if not self.mini_mode:
            # Switch to Mini
            self.normal_geometry = self.root.geometry()
            self.root.geometry("250x100")
            self.main_frame.pack_forget()
            
            self.mini_frame = Frame(self.root, padding=10)
            self.mini_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(self.mini_frame, text=f"Active: {self.active_profile}", font=("Segoe UI", 12, "bold")).pack(pady=(5, 10))
            ttk.Button(self.mini_frame, text="Expand to Normal View", command=self.toggle_mini_mode).pack(fill=tk.X)
            
            self.status_label.pack_forget() # Hide status bar in mini mode
            self.mini_mode = True
        else:
            # Switch to Normal
            self.mini_frame.destroy()
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
            self.root.geometry(self.normal_geometry)
            self.mini_mode = False

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
        # Pass nothing for new bind
        dialog = KeybindEditorDialog(self.root)
        if dialog.result:
            key, action_type, should_update_loc = dialog.result
            self.pending_key = key
            self.pending_action_type = action_type
            
            self.add_keybind_mode = True
            # Update button to show state
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
            # Update mini mode label if active
            if self.mini_mode:
                # Re-render or just update? Simple approach: toggle back and forth or update widget children.
                # Since I used a hardcoded label in toggle_mini_mode, I should probably store it.
                # Or just lazy refresh:
                self.toggle_mini_mode() # To Normal
                self.toggle_mini_mode() # Back to Mini (updates label)

    def clear_keybinds(self):
        if messagebox.askyesno("Confirm", f"Clear all keybinds in '{self.active_profile}'?"):
            self.profiles[self.active_profile]['keybinds'].clear()
            self.save_profiles()
            self.update_status("Keybinds cleared.")

    def show_keybinds(self):
        win = tk.Toplevel(self.root)
        win.title(f"Keybinds: {self.active_profile}")
        win.geometry("600x400")
        
        # Frame for Treeview and Scrollbar
        list_frame = Frame(win, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("key", "action", "coords")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        tree.heading("key", text="Key Combination")
        tree.heading("action", text="Action Type")
        tree.heading("coords", text="Coordinates")
        
        tree.column("key", width=150)
        tree.column("action", width=150)
        tree.column("coords", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def populate_tree():
            for item in tree.get_children():
                tree.delete(item)
                
            current_binds = self.profiles[self.active_profile]['keybinds']
            for key, val in current_binds.items():
                if isinstance(val, list):
                    action = "Legacy (Click & Return)"
                    coords = str(val)
                else:
                    action = val.get('type')
                    coords = str(val.get('coords'))
                
                tree.insert("", tk.END, iid=key, values=(key, action, coords))

        populate_tree()

        # Action Buttons
        btn_frame = Frame(win, padding=10)
        btn_frame.pack(fill=tk.X)

        def on_edit():
            selected = tree.selection()
            if not selected: return
            key = selected[0]
            
            # Get current data
            binds = self.profiles[self.active_profile]['keybinds']
            if key not in binds: return # Should not happen
            
            current_data = binds[key]
            # Normalize data if legacy
            if isinstance(current_data, list):
                 current_data = {"coords": current_data, "type": ACTION_CLICK_RETURN}
            
            # Open Dialog in Edit Mode
            dialog = KeybindEditorDialog(win, edit_mode=True, current_key=key, current_data=current_data)
            
            if dialog.result:
                new_key, new_action, should_update_loc = dialog.result
                
                # If key changed, we need to remove old entry
                if new_key != key:
                    del self.profiles[self.active_profile]['keybinds'][key]
                
                # Decide next steps
                if should_update_loc:
                     # Enter "Click to Set" mode
                     self.pending_key = new_key
                     self.pending_action_type = new_action
                     self.add_keybind_mode = True
                     self.add_button.config(state=tk.DISABLED, text="Click on Screen...")
                     self.update_status(f"Click anywhere to update '{new_key}'...")
                     # Close this window so they can click
                     win.destroy() 
                else:
                    # Just update data in place
                    new_data = {
                        "coords": current_data['coords'], # Keep existing coords
                        "type": new_action
                    }
                    self.profiles[self.active_profile]['keybinds'][new_key] = new_data
                    self.save_profiles()
                    populate_tree()

        def on_delete():
            selected = tree.selection()
            if not selected: return
            key = selected[0]
            if messagebox.askyesno("Confirm", f"Delete bind for '{key}'?", parent=win):
                 del self.profiles[self.active_profile]['keybinds'][key]
                 self.save_profiles()
                 populate_tree()

        ttk.Button(btn_frame, text="Edit Selected", command=on_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=on_delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=win.destroy).pack(side=tk.RIGHT)

        tree.bind("<Double-1>", lambda e: on_edit())

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
