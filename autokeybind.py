import pyautogui
from pynput.keyboard import Key, Listener, Controller
from pynput.mouse import Listener as MouseListener, Controller as MouseController
from input_engine import PynputEngine, EvdevEngine
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Scrollbar, Listbox, Toplevel
from tkinter.ttk import Frame, Label, Entry, Button, Style
import sys
import os
import json
import time
import time
import random
import threading
import pystray
from PIL import Image, ImageTk
from key_utils import get_key_combo_string
import platform
import subprocess
import shutil



# Action Types Constant
ACTION_CLICK_RETURN = "Click & Return"
ACTION_CLICK_STAY = "Click & Stay"
ACTION_DOUBLE_CLICK_RETURN = "Double Click & Return"
ACTION_DRAG_RETURN = "Drag & Return"
ACTION_MACRO = "Macro / Sequence"
ACTION_TEXT = "Text / Type"

ACTION_TYPES = [
    ACTION_CLICK_RETURN,
    ACTION_CLICK_STAY,
    ACTION_DOUBLE_CLICK_RETURN,
    ACTION_DRAG_RETURN,
    ACTION_MACRO
]





class MacroManagerDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Macro Manager")
        self.geometry("500x500")
        self.wm_attributes("-topmost", 1)
        
        # Layout
        self.main_frame = Frame(self, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # List
        Label(self.main_frame, text="Macro Library:", style="Header.TLabel").pack(anchor=tk.W)
        
        list_frame = Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = Listbox(list_frame, height=15, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Buttons
        btn_frame = Frame(self.main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Create New", command=self.create_macro).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_macro).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Duplicate", command=self.duplicate_macro).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_macro).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)
        
        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        macros = self.app.profiles[self.app.active_profile].get('macros', {})
        for name in sorted(macros.keys()):
            self.listbox.insert(tk.END, name)

    def create_macro(self):
        editor = MacroEditorDialog(self, self.app, {"name": "New Macro"})
        if editor.result:
            name = editor.result.get('name')
            if not name: return
            
            # Save to library
            if 'macros' not in self.app.profiles[self.app.active_profile]:
                self.app.profiles[self.app.active_profile]['macros'] = {}
                
            self.app.profiles[self.app.active_profile]['macros'][name] = editor.result
            self.app.save_profiles()
            self.refresh_list()

    def edit_macro(self):
        sel = self.listbox.curselection()
        if not sel: return
        name = self.listbox.get(sel[0])
        
        macros = self.app.profiles[self.app.active_profile].get('macros', {})
        data = macros.get(name)
        
        editor = MacroEditorDialog(self, self.app, data)
        if editor.result:
            new_name = editor.result.get('name')
            
            # Handle Rename
            if new_name != name:
                del macros[name]
                
            macros[new_name] = editor.result
            self.app.save_profiles()
            self.refresh_list()

    def duplicate_macro(self):
        sel = self.listbox.curselection()
        if not sel: return
        name = self.listbox.get(sel[0])
        
        macros = self.app.profiles[self.app.active_profile].get('macros', {})
        data = macros.get(name).copy()
        data['name'] = f"{name} (Copy)"
        
        macros[data['name']] = data
        self.app.save_profiles()
        self.refresh_list()

    def delete_macro(self):
        sel = self.listbox.curselection()
        if not sel: return
        name = self.listbox.get(sel[0])
        
        if messagebox.askyesno("Confirm", f"Delete macro '{name}'?", parent=self):
            del self.app.profiles[self.app.active_profile]['macros'][name]
            self.app.save_profiles()
            self.refresh_list()


class TextTypingDialog(tk.Toplevel):
    def __init__(self, parent, current_data=None):
        super().__init__(parent)
        self.title("Add Text Action")
        self.geometry("450x400")
        self.wm_attributes("-topmost", 1)
        self.resizable(True, True)
        self.result = None
        
        # Main Frame
        main_frame = Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text Input
        Label(main_frame, text="Text to Type:").pack(anchor=tk.W, pady=(0, 5))
        self.text_input = tk.Text(main_frame, height=5, width=40)
        self.text_input.pack(fill=tk.X, pady=(0, 10))
        
        if current_data:
            self.text_input.insert("1.0", current_data.get('content', ''))
            
        # Delay Config
        Label(main_frame, text="Delay Settings:").pack(anchor=tk.W, pady=(0, 5))
        delay_frame = Frame(main_frame)
        delay_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.delay_mode_var = tk.StringVar(value=current_data.get('delay_mode', 'static') if current_data else 'static')
        
        # Static Option
        ttk.Radiobutton(delay_frame, text="Static Delay", variable=self.delay_mode_var, value="static", command=self.update_ui).pack(anchor=tk.W)
        self.static_delay_entry = ttk.Entry(delay_frame, width=10)
        self.static_delay_entry.insert(0, str(current_data.get('delay_static', 0.05)) if current_data else "0.05")
        self.static_delay_entry.pack(anchor=tk.W, padx=20)
        
        # Random Option
        ttk.Radiobutton(delay_frame, text="Random Delay", variable=self.delay_mode_var, value="random", command=self.update_ui).pack(anchor=tk.W, pady=(10, 0))
        rand_frame = Frame(delay_frame)
        rand_frame.pack(anchor=tk.W, padx=20)
        ttk.Label(rand_frame, text="Min:").pack(side=tk.LEFT)
        self.rand_min_entry = ttk.Entry(rand_frame, width=8)
        self.rand_min_entry.insert(0, str(current_data.get('delay_min', 0.05)) if current_data else "0.05")
        self.rand_min_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(rand_frame, text="Max:").pack(side=tk.LEFT)
        self.rand_max_entry = ttk.Entry(rand_frame, width=8)
        self.rand_max_entry.insert(0, str(current_data.get('delay_max', 0.15)) if current_data else "0.15")
        self.rand_max_entry.pack(side=tk.LEFT, padx=5)
        
        self.update_ui()
        
        # Buttons
        btn_frame = Frame(self, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_frame, text="Save", command=self.on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
        
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def update_ui(self):
        mode = self.delay_mode_var.get()
        if mode == 'static':
            self.static_delay_entry.config(state='normal')
            self.rand_min_entry.config(state='disabled')
            self.rand_max_entry.config(state='disabled')
        else:
            self.static_delay_entry.config(state='disabled')
            self.rand_min_entry.config(state='normal')
            self.rand_max_entry.config(state='normal')

    def on_save(self):
        content = self.text_input.get("1.0", "end-1c")
        if not content:
            messagebox.showwarning("Input Required", "Please enter text to type.", parent=self)
            return
            
        self.result = {
            "type": "text",
            "content": content,
            "delay_mode": self.delay_mode_var.get(),
            "delay_static": self.static_delay_entry.get(),
            "delay_min": self.rand_min_entry.get(),
            "delay_max": self.rand_max_entry.get()
        }
        self.destroy()



class ClickInPlaceDialog(tk.Toplevel):
    """Dialog for configuring a Click (In Place) action - clicks at current cursor position."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Click (In Place)")
        self.geometry("350x250")
        self.resizable(False, False)
        self.wm_attributes("-topmost", 1)
        self.result = None

        # Main Frame
        main_frame = Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        Label(main_frame, text="Click at Current Cursor Position", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 15))

        # Mouse Button Selection
        Label(main_frame, text="Mouse Button:").pack(anchor=tk.W, pady=(0, 5))
        self.button_var = tk.StringVar(value="left")
        btn_frame = Frame(main_frame)
        btn_frame.pack(anchor=tk.W, pady=(0, 15))
        ttk.Radiobutton(btn_frame, text="Left", variable=self.button_var, value="left").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(btn_frame, text="Right", variable=self.button_var, value="right").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(btn_frame, text="Middle", variable=self.button_var, value="middle").pack(side=tk.LEFT)

        # Click Type Selection
        Label(main_frame, text="Click Type:").pack(anchor=tk.W, pady=(0, 5))
        self.click_type_var = tk.StringVar(value="single")
        type_frame = Frame(main_frame)
        type_frame.pack(anchor=tk.W, pady=(0, 15))
        ttk.Radiobutton(type_frame, text="Single Click", variable=self.click_type_var, value="single").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(type_frame, text="Double Click", variable=self.click_type_var, value="double").pack(side=tk.LEFT)

        # Buttons
        btn_bar = Frame(self, padding=10)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_bar, text="Add", command=self.on_add).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_bar, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def on_add(self):
        self.result = {
            "type": "click_in_place",
            "button": self.button_var.get(),
            "click_type": self.click_type_var.get()
        }
        self.destroy()


class ActionKeyDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Key Action")
        self.geometry("400x300")
        self.resizable(False, False)
        self.wm_attributes("-topmost", 1)
        self.result = None
        
        self.pressed_keys = set()
        self.listener = None
        
        # Main Frame
        main_frame = Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(main_frame, text="Key to Simulate:", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.key_display_var = tk.StringVar(value="None")
        self.display_lbl = Label(main_frame, textvariable=self.key_display_var, font=("Segoe UI", 14, "bold"), relief="sunken", background="white", anchor="center")
        self.display_lbl.pack(fill=tk.X, pady=(0, 20), ipady=10)
        
        self.record_btn = Button(main_frame, text="Record Key", command=self.toggle_recording)
        self.record_btn.pack(fill=tk.X, pady=(0, 20))
        
        Label(main_frame, text="Click Record, then press a single key.", foreground="#666").pack(anchor=tk.W)
        
        # Buttons
        btn_frame = Frame(self, padding=20)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Add", command=self.on_add).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
        
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
        self.key_display_var.set("Press a key...")
        self.record_btn.configure(text="Stop Recording") 
        # Use pynput listener
        self.listener = Listener(on_press=self.on_press)
        self.listener.start()

    def stop_recording(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.record_btn.configure(text="Record Key")

    def on_press(self, key):
        k_str = ""
        try:
            if hasattr(key, 'char') and key.char:
                k_str = key.char
            elif hasattr(key, 'name'):
                k_str = key.name
            else:
                k_str = str(key).replace('Key.', '')
        except Exception:
            k_str = str(key)
        
        # Update UI and Stop
        self.display_lbl.after(0, lambda: self.finish_recording(k_str))
        return False

    def finish_recording(self, key_str):
        self.key_display_var.set(key_str)
        self.stop_recording()

    def on_close(self):
        self.stop_recording()
        self.destroy()

    def on_add(self):
        key = self.key_display_var.get()
        if not key or key == "None" or key == "Press a key...":
             messagebox.showwarning("Input Required", "Please record a key.", parent=self)
             return
             
        self.result = {"type": "key", "key": key}
        self.destroy()

class MacroEditorDialog(tk.Toplevel):
    def __init__(self, parent, app, current_actions=None):
        super().__init__(parent)
        self.app = app
        self.title("Macro Editor")
        self.geometry("700x600")
        self.wm_attributes("-topmost", 1) # Ensure visible over main window
        self.result = None
        
        self.playback_config = {}
        if isinstance(current_actions, dict) and 'actions' in current_actions:
            self.actions = current_actions.get('actions', [])
            self.playback_config = current_actions.get('playback', {})
        elif isinstance(current_actions, list):
            self.actions = current_actions
        else:
            self.actions = []
        
        # --- Layout Construction ---
        
        # 1. Header: Name Field
        header_frame = Frame(self, padding=10)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        Label(header_frame, text="Macro Name:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value=current_actions.get('name', 'My Macro') if isinstance(current_actions, dict) else "My Macro")
        ttk.Entry(header_frame, textvariable=self.name_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 2. Footer: Playback & Buttons (Pack first to reserve space at bottom)
        bottom_frame = Frame(self, padding=10, relief="groove", borderwidth=1)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Left Side: Playback
        pb_frame = Frame(bottom_frame)
        pb_frame.pack(side=tk.LEFT, fill=tk.X)
        
        Label(pb_frame, text="Playback Mode:").pack(side=tk.LEFT)
        
        modes = ["Play Once", "Loop (Count)", "Loop (Time)", "Infinite Loop"]
        self.mode_map = {
            "Play Once": "once",
            "Loop (Count)": "loop_count", 
            "Loop (Time)": "loop_time",
            "Infinite Loop": "infinite"
        }
        # Reverse map for initial value
        curr_mode = self.playback_config.get('mode', 'once')
        init_mode_text = next((k for k, v in self.mode_map.items() if v == curr_mode), "Play Once")
        
        self.playback_mode_var = tk.StringVar(value=init_mode_text)
        self.mode_combo = ttk.Combobox(pb_frame, textvariable=self.playback_mode_var, values=modes, state="readonly", width=15)
        self.mode_combo.pack(side=tk.LEFT, padx=5)
        self.mode_combo.bind("<<ComboboxSelected>>", self.update_playback_ui)
        
        self.val_frame = Frame(pb_frame)
        self.val_frame.pack(side=tk.LEFT, padx=10)
        
        self.val_label = Label(self.val_frame, text="Count:")
        self.val_label.pack(side=tk.LEFT)
        
        self.playback_val_var = tk.StringVar(value=str(self.playback_config.get('value', 1)))
        self.val_entry = ttk.Entry(self.val_frame, textvariable=self.playback_val_var, width=8)
        self.val_entry.pack(side=tk.LEFT, padx=5)

        # Right Side: Buttons
        btn_box = Frame(bottom_frame)
        btn_box.pack(side=tk.RIGHT)
        
        ttk.Button(btn_box, text="Save", command=self.on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

        # 3. Middle: Actions List (Occupies remaining space)
        self.main_frame = Frame(self, padding=10)
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Action List (Left Side of Middle)
        list_frame = Frame(self.main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        Label(list_frame, text="Action Sequence:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        
        self.listbox = Listbox(list_frame, height=15, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self.refresh_list()
        
        # Buttons (Right Side of Middle)
        btn_frame = Frame(self.main_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        Label(btn_frame, text="Add Actions:", font=("Segoe UI", 10, "bold")).pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(btn_frame, text="Add Delay", command=self.add_delay).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Add Text", command=self.add_text).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Add Click", command=self.add_click).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Add Click (In Place)", command=self.add_click_in_place).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Add Key", command=self.add_key).pack(fill=tk.X, pady=2)
        
        ttk.Separator(btn_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Move Up", command=self.move_up).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Move Down", command=self.move_down).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_action).pack(fill=tk.X, pady=2)
        
        self.update_playback_ui()
        
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def update_playback_ui(self, event=None):
        text_mode = self.playback_mode_var.get()
        mode = self.mode_map.get(text_mode, 'once')
        
        if mode == 'once' or mode == 'infinite':
            self.val_frame.pack_forget()
        else:
            self.val_frame.pack(side=tk.LEFT, padx=10)
            if mode == 'loop_count':
                self.val_label.config(text="Count:")
            else:
                self.val_label.config(text="Seconds:")


    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for i, action in enumerate(self.actions):
            t = action.get('type')
            desc = f"{i+1}. {t.upper()}"
            if t == 'delay':
                if action.get('mode') == 'random':
                    desc += f" (Random: {action.get('min')}-{action.get('max')}s)"
                else:
                    desc += f" ({action.get('time')}s)"
            elif t == 'text':
                content = action.get('content', '')
                short = (content[:15] + '..') if len(content) > 15 else content
                desc += f" '{short}'"
            elif t == 'click':
                desc += f" {action.get('coords')}"
            elif t == 'click_in_place':
                btn = action.get('button', 'left').capitalize()
                click_type = action.get('click_type', 'single').capitalize()
                desc += f" ({click_type} {btn} at Cursor)"
            elif t == 'key':
                desc += f" [{action.get('key')}]"
            
            self.listbox.insert(tk.END, desc)

    def add_delay(self):
        val = simpledialog.askfloat("Add Delay", "Enter delay in seconds:", parent=self, minvalue=0.01, maxvalue=60.0)
        if val is not None:
             self.actions.append({"type": "delay", "mode": "static", "time": val})
             self.refresh_list()

    def add_text(self):
        dialog = TextTypingDialog(self)
        if dialog.result:
            self.actions.append(dialog.result)
            self.refresh_list()

    def add_click(self):
        messagebox.showinfo("Add Click", "Click OK, then click anywhere on screen to capture coordinates.", parent=self)
        self.withdraw()
        
        coords = []
        click_detected = tk.BooleanVar(value=False)
        
        def on_c(x, y, button, pressed):
            if pressed:
                coords.append((x,y))
                # Signal Tkinter loop
                self.after(0, lambda: click_detected.set(True))
                return False # Stop listener
        
        listener = MouseListener(on_click=on_c)
        listener.start()
        
        self.wait_variable(click_detected)
        
        self.deiconify()
        if coords:
            self.actions.append({"type": "click", "coords": [coords[0][0], coords[0][1]], "button": "left"})
            self.refresh_list()

    def add_click_in_place(self):
        d = ClickInPlaceDialog(self)
        if d.result:
            self.actions.append(d.result)
            self.refresh_list()

    def add_key(self):
        d = ActionKeyDialog(self)
        if d.result:
            self.actions.append(d.result)
            self.refresh_list()


    def move_up(self):
        sel = self.listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx > 0:
            self.actions[idx], self.actions[idx-1] = self.actions[idx-1], self.actions[idx]
            self.refresh_list()
            self.listbox.selection_set(idx-1)

    def move_down(self):
        sel = self.listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(self.actions) - 1:
            self.actions[idx], self.actions[idx+1] = self.actions[idx+1], self.actions[idx]
            self.refresh_list()
            self.listbox.selection_set(idx+1)

    def delete_action(self):
        sel = self.listbox.curselection()
        if not sel: return
        idx = sel[0]
        del self.actions[idx]
        self.refresh_list()

    def on_save(self):
        try:
            text_mode = self.playback_mode_var.get()
            mode = self.mode_map.get(text_mode, 'once')
            
            val = float(self.playback_val_var.get()) if mode in ['loop_count', 'loop_time'] else 0
            
            playback_config = {
                "mode": mode,
                "value": val
            }
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for Loop Count or Duration.", parent=self)
            return

        # Return a dict structure for the macro
        self.result = {
            "name": self.name_var.get(),
            "actions": self.actions,
            "playback": playback_config
        }
        self.destroy()

class KeybindEditorDialog(tk.Toplevel):
    def __init__(self, parent, app, edit_mode=False, current_key=None, current_data=None):
        super().__init__(parent)
        self.app = app
        self.title("Edit Keybind" if edit_mode else "Add Keybind")
        self.geometry("500x600")
        self.resizable(False, True)
        self.wm_attributes("-topmost", 1) # Ensure visible over main window
        self.result = None
        self.edit_mode = edit_mode
        self.current_data = current_data
        
        self.pressed_keys = set()
        self.listener = None
        
        # Bottom Buttons (Pack first to ensure visibility)
        btn_frame = Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        ok_text = "Save Changes" if edit_mode else "Set Location & Save"
        self.ok_btn = Button(btn_frame, text=ok_text, command=self.on_ok)
        self.ok_btn.pack(side=tk.RIGHT, padx=(10, 0))
        Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

        # Main Frame (Occupies remaining space)
        main_frame = Frame(self, padding=20)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 1. Key Section
        Label(main_frame, text="Key Combination:", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        self.key_display_var = tk.StringVar(value=current_key if current_key else "None")
        self.display_lbl = Label(main_frame, textvariable=self.key_display_var, font=("Segoe UI", 14, "bold"), relief="sunken", background="white", anchor="center")
        self.display_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipady=10)
        
        self.record_btn = Button(main_frame, text="Record Key", command=self.toggle_recording)
        self.record_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # 2. Action Type Selection
        Label(main_frame, text="Action Type:", style="Header.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        initial_action = current_data.get('type', ACTION_CLICK_RETURN) if current_data else ACTION_CLICK_RETURN
        self.action_var = tk.StringVar(value=initial_action)
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.action_var, values=ACTION_TYPES, state="readonly", font=("Segoe UI", 10))
        self.type_combo.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        self.type_combo.bind("<<ComboboxSelected>>", self.on_type_changed)
        
        # 3. Dynamic Content Frame
        self.content_frame = Frame(main_frame)
        self.content_frame.grid(row=5, column=0, columnspan=2, sticky="nsew")
        
        # Store widgets for dynamic show/hide
        self.loc_widgets = []
        self.text_widgets = []
        
        # -- Location Widgets (Default) --
        current_coords = current_data.get('coords') if current_data else None
        self.coords_var = tk.StringVar(value=f"Location: {current_coords}" if current_coords else "Location: Not Set")
        lbl = Label(self.content_frame, textvariable=self.coords_var, foreground="#666")
        self.loc_widgets.append(lbl)
        
        self.update_loc_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(self.content_frame, text="Update/Reset Location (Click on Save)", variable=self.update_loc_var)
        self.loc_widgets.append(chk)
        
        # -- Text / AutoTyper Widgets -- 
        self.text_input = tk.Text(self.content_frame, height=5, width=40)
        self.text_widgets.append(Label(self.content_frame, text="Text to Type:"))
        self.text_widgets.append(self.text_input)
        
        # Delay Config
        self.delay_mode_var = tk.StringVar(value="static")
        delay_frame = Frame(self.content_frame)
        self.text_widgets.append(delay_frame)
        
        ttk.Radiobutton(delay_frame, text="Static Delay", variable=self.delay_mode_var, value="static", command=self.update_delay_ui).pack(anchor=tk.W)
        self.static_delay_entry = ttk.Entry(delay_frame, width=10)
        self.static_delay_entry.insert(0, "0.05")
        self.static_delay_entry.pack(anchor=tk.W, padx=20)
        
        ttk.Radiobutton(delay_frame, text="Random Delay", variable=self.delay_mode_var, value="random", command=self.update_delay_ui).pack(anchor=tk.W, pady=(10, 0))
        rand_frame = Frame(delay_frame)
        rand_frame.pack(anchor=tk.W, padx=20)
        ttk.Label(rand_frame, text="Min:").pack(side=tk.LEFT)
        self.rand_min_entry = ttk.Entry(rand_frame, width=8)
        self.rand_min_entry.insert(0, "0.05")
        self.rand_min_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(rand_frame, text="Max:").pack(side=tk.LEFT)
        self.rand_max_entry = ttk.Entry(rand_frame, width=8)
        self.rand_max_entry.insert(0, "0.15")
        self.rand_max_entry.pack(side=tk.LEFT, padx=5)
        
        # Initialize UI state
        self.on_type_changed(None)
        
        # Populate exist data if editing text
        self.macro_actions = []
        self.macro_playback = {}
        self.macro_name = "My Macro"
        if current_data and current_data.get('type') == ACTION_MACRO:
            self.macro_actions = current_data.get('actions', [])
            self.macro_playback = current_data.get('playback', {})
            self.macro_name = current_data.get('name', "My Macro")

        if edit_mode and initial_action == ACTION_TEXT and current_data:
             self.text_input.insert("1.0", current_data.get('content', ''))
             self.delay_mode_var.set(current_data.get('delay_mode', 'static'))
             self.static_delay_entry.delete(0, tk.END); self.static_delay_entry.insert(0, str(current_data.get('delay_static', 0.05)))
             self.rand_min_entry.delete(0, tk.END); self.rand_min_entry.insert(0, str(current_data.get('delay_min', 0.05)))
             self.rand_max_entry.delete(0, tk.END); self.rand_max_entry.insert(0, str(current_data.get('delay_max', 0.15)))
             self.update_delay_ui()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)
        self.grab_set()
        
        self.wait_window(self)

    def on_type_changed(self, event):
        action = self.action_var.get()
        
        # Hide all first
        for w in self.loc_widgets: w.grid_remove()
        for w in self.text_widgets: w.pack_forget() if isinstance(w, Frame) else w.grid_remove() 
        for child in self.content_frame.winfo_children():
            child.grid_remove()
            
        if action == ACTION_MACRO:
             # Macro Selection UI
             Label(self.content_frame, text="Select Macro:", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 5))
             
             macros = self.app.profiles[self.app.active_profile].get('macros', {})
             macro_names = sorted(macros.keys())
             
             self.macro_select_var = tk.StringVar()
             if self.current_data and self.current_data.get('type') == ACTION_MACRO:
                 # Check if it was a reference or embedded
                 saved_name = self.current_data.get('macro_name')
                 if saved_name and saved_name in macros:
                     self.macro_select_var.set(saved_name)
                 elif self.current_data.get('name') and self.current_data.get('name') in macros:
                      self.macro_select_var.set(self.current_data.get('name'))
             
             self.macro_combo = ttk.Combobox(self.content_frame, textvariable=self.macro_select_var, values=macro_names, state="readonly")
             self.macro_combo.grid(row=1, column=0, sticky="ew", pady=(0, 10))
             
             btn_frame = Frame(self.content_frame)
             btn_frame.grid(row=2, column=0, sticky="w")
             
             ttk.Button(btn_frame, text="New Macro", command=self.create_new_macro).pack(side=tk.LEFT, padx=(0, 5))
             ttk.Button(btn_frame, text="Edit Selected", command=self.edit_selected_macro).pack(side=tk.LEFT)
             
             self.ok_btn.configure(text="Bind Macro")
             
        else:
            # Mouse Action
            self.loc_widgets[0].grid(row=0, column=0, sticky="w", pady=(0, 10))
            
            if self.edit_mode:
                 self.loc_widgets[1].grid(row=1, column=0, sticky="w", pady=(0, 10))
                 self.ok_btn.configure(text="Save Changes")
            else:
                 self.ok_btn.configure(text="Set Location & Save")

    def create_new_macro(self):
        editor = MacroEditorDialog(self, self.app, {"name": "New Macro"})
        if editor.result:
            name = editor.result.get('name')
            if not name: return
            
            # Save to library (via App reference)
            if 'macros' not in self.app.profiles[self.app.active_profile]:
                self.app.profiles[self.app.active_profile]['macros'] = {}
                
            self.app.profiles[self.app.active_profile]['macros'][name] = editor.result
            self.app.save_profiles()
            
            # Update Combo
            self.on_type_changed(None)
            
            # Force refresh of values
            macros = self.app.profiles[self.app.active_profile].get('macros', {})
            macro_names = sorted(macros.keys())
            self.macro_combo['values'] = macro_names
            
            self.macro_select_var.set(name)

    def edit_selected_macro(self):
        name = self.macro_select_var.get()
        if not name: return
        
        macros = self.app.profiles[self.app.active_profile].get('macros', {})
        data = macros.get(name)
        
        editor = MacroEditorDialog(self, data)
        if editor.result:
            new_name = editor.result.get('name')
            
            if new_name != name:
                del macros[name]
            
            macros[new_name] = editor.result
            self.app.save_profiles()
            
            self.on_type_changed(None)
            
            # Force refresh of values
            macros = self.app.profiles[self.app.active_profile].get('macros', {})
            macro_names = sorted(macros.keys())
            self.macro_combo['values'] = macro_names
            
            self.macro_select_var.set(new_name)

    def update_delay_ui(self):
        mode = self.delay_mode_var.get()
        if mode == 'static':
            self.static_delay_entry.config(state='normal')
            self.rand_min_entry.config(state='disabled')
            self.rand_max_entry.config(state='disabled')
        else:
            self.static_delay_entry.config(state='disabled')
            self.rand_min_entry.config(state='normal')
            self.rand_max_entry.config(state='normal')

    def toggle_recording(self):
        if self.listener:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.pressed_keys.clear()
        self.key_display_var.set("Press keys...")
        self.record_btn.configure(text="Stop Recording") 
        
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
        action_type = self.action_var.get()

        if not key or key == "None" or key == "Press keys...":
            messagebox.showwarning("Input Required", "Please record a key combination.", parent=self)
            return
            
        if action_type == ACTION_MACRO:
            name = self.macro_select_var.get()
            if not name:
                messagebox.showwarning("Selection Required", "Please select a macro.", parent=self)
                return

            data = {
                "type": ACTION_MACRO,
                "macro_name": name
            }
            self.result = (key, data, False)
            self.destroy()
            return




        if action_type == ACTION_TEXT:
            content = self.text_input.get("1.0", "end-1c")
            if not content:
                messagebox.showwarning("Input Required", "Please enter text to type.", parent=self)
                return

            data = {
                "type": ACTION_TEXT,
                "content": content,
                "delay_mode": self.delay_mode_var.get(),
                "delay_static": self.static_delay_entry.get(),
                "delay_min": self.rand_min_entry.get(),
                "delay_max": self.rand_max_entry.get()
            }
            # Text actions don't need location usually
            self.result = (key, data, False)
            self.destroy()
            return

        # Legacy/Mouse Logic
        should_update = self.update_loc_var.get() if self.edit_mode else True
        self.result = (key, action_type, should_update)
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
        
        # Kill-Switch State
        self.kill_switch_active = False
        self.running_macro = False
        self.macro_cancelled = False
        self.current_running_bind = None
        self.capture_key_callback = None # For requesting key capture from dialogs
        
        # Mouse Controller for advanced actions
        self.mouse = MouseController()
        
        # Load Data
        self.load_profiles()

        # Setup UI
        self.setup_ui()

        # Setup System Tray
        self.setup_tray_icon()
        
        # Check Display Server (Linux)
        self.check_display_server()

        # Initialize Input Engine
        self.init_input_engine()
        
        # Check for xdotool
        self.has_xdotool = False
        if platform.system() == 'Linux':
            try:
                subprocess.run(['xdotool', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.has_xdotool = True
                 # print("[INFO] xdotool detected.")
            except FileNotFoundError:
                 pass # print("[WARNING] xdotool not found.")
        
        # Start Input Listeners
        # Start Input Listeners (Only if not already started by init_input_engine)
        # init_input_engine starts them immediately for both Evdev and Pynput (in fallback), 
        # so we don't need to call them again here.
        self.check_listeners_alive() # Just start the heartbeat
    
    def init_input_engine(self):
        # Determine which engine to use
        use_evdev = False
        if platform.system() == 'Linux':
            # Always prefer Evdev on Linux for global input support (Wayland & X11)
            use_evdev = True
            print("[INFO] Linux detected. Attempting to use Evdev Engine.")
        
        self.evdev_init_error = None
        
        if use_evdev:
            try:
                self.input_engine = EvdevEngine()
                self.input_engine.start_listeners(on_press=self.on_key_press, on_release=self.on_key_release)
                self.input_status_var.set("Input: Evdev (Global)")
                print("[INFO] Evdev Engine started successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to init Evdev: {e}")
                self.evdev_init_error = str(e)
                
                # Fallback to Pynput
                self.input_engine = PynputEngine()
                self.input_engine.start_listeners(on_press=self.on_key_press, on_release=self.on_key_release)
                self.input_status_var.set("Input: Pynput (Restricted)")
                
                # Show error dialog to user explaining the situation
                error_msg = self.evdev_init_error or "Unknown Error"
                permission_hint = ""
                if "Permission denied" in error_msg or "uinput" in error_msg:
                    permission_hint = (
                        "\n\nIt looks like a permission issue.\n"
                        "Please run 'sudo bash scripts/install_linux.sh' and restart your computer (or log out/in)."
                    )

                messagebox.showwarning("Input Engine Limitation", 
                    f"Evdev Engine failed to start:\n{error_msg}{permission_hint}\n\n"
                    "The application is running in FALLBACK (Pynput) mode.\n"
                    "Global Hotkeys will NOT work on Wayland windows.\n"
                    "They will only work when this app is focused."
                )
        else:
            self.input_engine = PynputEngine()
            print("[INFO] Using PynputEngine (Default for Windows/macOS)")
            self.input_status_var.set("Input: Pynput")

    def check_engine_health_and_fallback(self):
        # Specific check for Evdev health
        if isinstance(self.input_engine, EvdevEngine) and not self.input_engine.is_healthy():
             error_msg = getattr(self.input_engine, 'last_error', "Unknown Error")
             print(f"[ERROR] Evdev died: {error_msg}")
             
             # Show error once and stop using it
             messagebox.showerror("Input Engine Died", 
                 f"Evdev Engine stopped unexpectedly:\n{error_msg}\n\n"
                 "Falling back to Pynput (Limited Functionality).")
                 
             try:
                 self.input_engine.stop_listeners()
             except: pass
             
             self.input_engine = PynputEngine()
             self.input_engine.start_listeners(on_press=self.on_key_press, on_release=self.on_key_release)
             self.input_status_var.set("Input: Pynput (Fallback)")



    def check_display_server(self):
        pass



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
             self.profiles = {default_profile_name: {'keybinds': {}, 'macros': {}}}
        
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
        self.view_binds_button.pack(fill=tk.X, pady=(0, 5), ipady=5)

        self.manage_macros_button = ttk.Button(self.main_frame, text="Manage Macros", command=self.show_macro_manager)
        self.manage_macros_button.pack(fill=tk.X, pady=(0, 20), ipady=5)

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
        status_frame = Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value=f"Profile: {self.active_profile}")
        Label(status_frame, textvariable=self.status_var, anchor=tk.W).pack(side=tk.LEFT, padx=5)
        
        self.input_status_var = tk.StringVar(value="Input: Init")
        Label(status_frame, textvariable=self.input_status_var, anchor=tk.E).pack(side=tk.RIGHT, padx=5)
        
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
        dialog = KeybindEditorDialog(self.root, self)
        if dialog.result:
            key, action_data, should_update_loc = dialog.result
            
            if not should_update_loc:
                # Immediate Save (Text, Macro, or Edit without loc change)
                if key in self.profiles[self.active_profile]['keybinds']:
                     # This is 'Add' mode, so just overwrite.
                     pass
                # If we are here, we have data ready to save.
                self.profiles[self.active_profile]['keybinds'][key] = action_data
                self.save_profiles()
                self.refresh_profile_list()
                self.update_status(f"Bound '{key}'")
                return

            self.pending_key = key
            self.pending_action_type = action_data
            
            self.add_keybind_mode = True
            # Update button to show state
            self.add_button.config(state=tk.DISABLED, text="Click on Screen...")
            self.update_status(f"Click anywhere to bind '{key}' ({action_data})...")
            
            # Check for Evdev Engine (Wayland Support)
            if isinstance(self.input_engine, EvdevEngine):
                def on_evdev_c(x, y, button, pressed):
                    if pressed:
                        self.root.after(0, lambda: self.handle_click_main_thread(x, y))
                
                try:
                    self.input_engine.capture_single_click(on_evdev_c)
                except Exception as e:
                    pass

    def perform_action(self, x, y, action_type):
        pos = self.input_engine.get_current_position()
        try:
            ox, oy = pos.x, pos.y
        except AttributeError:
            ox, oy = pos[0], pos[1]
            
        print(f"[Keybind] Executing {action_type} at ({x}, {y}) | Returning to ({ox}, {oy})")
        
        if action_type == ACTION_CLICK_RETURN:

            if platform.system() == 'Linux':
                self.perform_linux_action(x, y, action_type, ox, oy)
                return
            
            pyautogui.click(x, y)

            pyautogui.moveTo(ox, oy)
            
        elif action_type == ACTION_CLICK_STAY:
            pyautogui.click(x, y)
            # Do not return
            
        elif action_type == ACTION_DOUBLE_CLICK_RETURN:
            pyautogui.doubleClick(x, y)
            pyautogui.moveTo(ox, oy)
            
        elif action_type == ACTION_DRAG_RETURN:
            # Move to target, hold down, move back, release
            pyautogui.moveTo(x, y)
            pyautogui.mouseDown()
            time.sleep(0.1) # Small delay for stability
            pyautogui.moveTo(ox, oy)
            pyautogui.mouseUp()
            
        else:
            pyautogui.click(x, y)
            pyautogui.moveTo(ox, oy)

    def perform_linux_action(self, x, y, action_type, ox, oy):
        """Dispatches Keybind actions using logical Hybrid moves and UInput clicks."""
        if action_type == ACTION_CLICK_RETURN:
            self.input_engine.simulation_click(x, y, 'left')
            time.sleep(0.1)
            self.input_engine.simulation_move(ox, oy)
            
        elif action_type == ACTION_CLICK_STAY:
            self.input_engine.simulation_click(x, y, 'left')
            
        elif action_type == ACTION_DOUBLE_CLICK_RETURN:
            self.input_engine.simulation_click(x, y, 'left')
            time.sleep(0.08)
            self.input_engine.simulation_click(x, y, 'left')
            time.sleep(0.1)
            self.input_engine.simulation_move(ox, oy)
            
        elif action_type == ACTION_DRAG_RETURN:
            # Drag logic using Hybrid Move + UInput Buttons
            self.input_engine.simulation_move(x, y)
            time.sleep(0.1)
            self.input_engine.simulation_mouse_down('left')
            time.sleep(0.12)
            self.input_engine.simulation_move(ox, oy)
            time.sleep(0.1)
            self.input_engine.simulation_mouse_up('left')
            
        else:
            # Default fallback
            self.input_engine.simulation_click(x, y, 'left')
            time.sleep(0.1)
            self.input_engine.simulation_move(ox, oy)

        # 2. Key Injection (if any was intended by this action type in future)
        # currently perform_action is mostly mouse-centric based on the Action Types.
        # But if we had a Key Action here, we'd use self.input_engine.simulation_key()


    # --- Kill-Switch Implementation ---
    def emergency_stop(self):
        if self.kill_switch_active:
            return
            
        self.kill_switch_active = True
        print("EMERGENCY STOP TRIGGERED")
        
        # Stop listeners immediately
        if hasattr(self, 'input_engine') and self.input_engine:
            self.input_engine.stop_listeners()

        if hasattr(self, 'mouse_listener') and self.mouse_listener:
            self.mouse_listener.stop()
            
        # Notify user (using after to be thread-safe with tkinter)
        self.root.after(0, lambda: messagebox.showerror("Emergency Stop", "Kill-Switch Activated! Application is closing."))
        self.root.after(0, self.on_close)

    def on_key_press(self, key):
        # DEBUG LOG
        # print(f"DEBUG: Key Pressed: {key}")
        
        if self.kill_switch_active:
            return

        if self.capture_key_callback:
    
            # Pass key to the requester (return True to keep listening, False to stop)
            keep_listening = self.capture_key_callback(key)
            if not keep_listening:
                self.capture_key_callback = None
            return

        self.current_pressed_keys.add(key)
        
        # Check Kill Switch (Ctrl+Alt+K)
        # Note: get_key_combo_string sorts keys. 'Alt' comes before 'Ctrl'.
        combo = get_key_combo_string(self.current_pressed_keys)
        if combo == "Alt+Ctrl+K":
            self.emergency_stop()
            return
            
        # Check Esc for stopping active macros
        if key == Key.esc and self.running_macro:
            self.emergency_stop()
            return

    def on_key_release(self, key):
        # print(f"DEBUG: Key Released: {key}")
        
        # Check for bind BEFORE removing the key
        self.check_and_perform_action()

        if key in self.current_pressed_keys:
            self.current_pressed_keys.remove(key)

    def check_and_perform_action(self):
        try:
            if not self.active_profile or self.kill_switch_active:
                return

            current_combo_str = get_key_combo_string(self.current_pressed_keys)
            
            # Check against binds
            binds = self.profiles[self.active_profile]['keybinds']
            
            if current_combo_str in binds:
                  if self.running_macro:
                      if self.current_running_bind == current_combo_str:
                          self.macro_cancelled = True
                      return
                  
                  self.macro_cancelled = False
                  self.current_running_bind = current_combo_str
                  self.running_macro = True
                  # Run in separate thread to not block listener
                  t = threading.Thread(target=self.execute_bind, args=(binds[current_combo_str],), daemon=True)
                  t.start()
                  return
            
            # Fallback for legacy binds
            if current_combo_str.lower() in binds:
                  if self.running_macro:
                      if self.current_running_bind == current_combo_str.lower():
                          self.macro_cancelled = True
                      return
                  
                  self.running_macro = True
                  self.macro_cancelled = False
                  self.current_running_bind = current_combo_str.lower()
                  # Run in separate thread to not block listener
                  threading.Thread(target=self.execute_bind, args=(binds[current_combo_str.lower()],), daemon=True).start()
                  return
        except Exception as e:
            print(f"Error in listener callback: {e}")
            import traceback
            traceback.print_exc()
        
    def execute_bind(self, bind_data):
        if self.kill_switch_active:
            self.running_macro = False
            return
            
        try:
            # wait for physical key release (up to 1.0s)
            # This prevents modifier interference (e.g. holding Ctrl while macro types 'c' -> Ctrl+C)
            start_wait = time.time()
            while self.current_pressed_keys and (time.time() - start_wait) < 1.0:
                 time.sleep(0.05)
                 
            # Force release modifiers via software just in case
            if self.input_engine:
                 self.input_engine.release_all_modifiers()
            
            # Detect Data Structure Type
            if isinstance(bind_data, list):
                 # Legacy: [x, y]
                 self.perform_action(bind_data[0], bind_data[1], ACTION_CLICK_RETURN)
            
            else:
                 # Dict Structure
                 action_type = bind_data.get('type')
                 
                 if action_type == ACTION_MACRO:
                    # Check for Macro Reference
                    if 'macro_name' in bind_data:
                        macro_name = bind_data['macro_name']
                        macros = self.profiles[self.active_profile].get('macros', {})
                        if macro_name in macros:
                            # Use the referenced macro data
                            bind_data = macros[macro_name]
                        else:
                            print(f"Macro '{macro_name}' not found!")
                            return
                    
                    actions = bind_data.get('actions', [])
                    playback = bind_data.get('playback', {})
                    mode = playback.get('mode', 'once')
                    val = playback.get('value', 0)
                    
                    if mode == 'once':
                        self.execute_macro(actions)
                    elif mode == 'loop_count':
                        count = int(val)
                        for _ in range(count):
                            if self.kill_switch_active or self.macro_cancelled: break
                            self.execute_macro(actions)
                    elif mode == 'loop_time':
                        end_time = time.time() + float(val)
                        while time.time() < end_time:
                            if self.kill_switch_active or self.macro_cancelled: break
                            self.execute_macro(actions)
                    elif mode == 'infinite':
                        while not self.kill_switch_active and not self.macro_cancelled:
                             self.execute_macro(actions)
                     
                 else:
                     # Standard single action (Legacy Dict)
                     coords = bind_data.get('coords')
                     if coords and len(coords) == 2:
                        if not self.kill_switch_active and not self.macro_cancelled:
                             self.perform_action(coords[0], coords[1], action_type or ACTION_CLICK_RETURN)
        finally:
            self.running_macro = False
            self.current_running_bind = None
            self.macro_cancelled = False

    def execute_macro(self, actions_list):
        for action in actions_list:
            if self.kill_switch_active or self.macro_cancelled:
                return
                
            a_type = action.get('type')
            
            if a_type == 'delay':
                # Pure Delay Action
                d_mode = action.get('mode', 'static')
                if d_mode == 'random':
                     time.sleep(random.uniform(action.get('min', 0.1), action.get('max', 0.5)))
                else:
                     time.sleep(action.get('time', 0.1))
                     
            elif a_type == 'text':
                self.execute_text_action(action)
                
            elif a_type == 'click':
                # Simplified click action in macro
                coords = action.get('coords')
                btn = action.get('button', 'left')
                if coords:
                    self.input_engine.simulation_click(coords[0], coords[1], btn)

                    
            elif a_type == 'click_in_place':
                # Click at current cursor position without moving the mouse.
                # Using simulation_click_in_place avoids sending EV_ABS events
                # that cause aim drift in 3D games (e.g. Minecraft).
                btn = action.get('button', 'left')
                click_type = action.get('click_type', 'single')
                
                self.input_engine.simulation_click_in_place(btn)
                if click_type == 'double':
                    time.sleep(0.08)
                    self.input_engine.simulation_click_in_place(btn)

            elif a_type == 'key':
                 k = action.get('key')
                 if k:
                     self.input_engine.simulation_key(k)

    def execute_text_action(self, action_data):
        content = action_data.get('content', '')
        # Handle literal \n if user typed it
        content = content.replace('\\n', '\n')
        
        delay_mode = action_data.get('delay_mode', 'static') # static, random, none
        delay_min = float(action_data.get('delay_min', 0.05))
        delay_max = float(action_data.get('delay_max', 0.15))
        static_delay = float(action_data.get('delay_static', 0.05))
        
        # Define checker for kill switch
        checker = lambda: self.kill_switch_active or self.macro_cancelled
        
        self.input_engine.simulation_text(
            text=content,
            delay_mode=delay_mode,
            delay_static=static_delay,
            delay_min=delay_min,
            delay_max=delay_max,
            kill_switch_checker=checker
        )
            
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
    # Connect listeners
    def start_listeners(self):
        # Keyboard (via InputEngine)
        self.input_engine.start_listeners(on_press=self.on_key_press, on_release=self.on_key_release)
        
        # Mouse (Keep Pynput for now, but handle failure on Wayland gracefully?)
        # On Wayland, this might not work for global sniffing, but we leave it for X11/Windows.
        try:
            self.mouse_listener = MouseListener(on_click=self.on_click)
            self.mouse_listener.start()
        except Exception as e:
             print(f"[WARNING] Mouse listener failed to start: {e}")
             
        # Start Heartbeat
        self.check_listeners_alive()

    def check_listeners_alive(self):
        # Check Input Engine (Keyboard/Global)
        if hasattr(self, 'input_engine') and self.input_engine:
             self.check_engine_health_and_fallback()
        
        # Check Mouse Listener (Pynput)
        if hasattr(self, 'mouse_listener') and self.mouse_listener:
             if not self.mouse_listener.is_alive():
                 print("[WARNING] Mouse listener died. Restarting...")
                 try:
                     # Re-create and start
                     self.mouse_listener = MouseListener(on_click=self.on_click)
                     self.mouse_listener.start()
                 except Exception as e:
                     print(f"[ERROR] Failed to restart mouse listener: {e}")

        # Schedule next check (every 5 seconds)
        self.root.after(5000, self.check_listeners_alive)

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

    def show_macro_manager(self):
        MacroManagerDialog(self.root, self)

    def show_keybinds(self):
        win = tk.Toplevel(self.root)
        win.title(f"Keybinds: {self.active_profile}")
        win.geometry("600x400")
        win.wm_attributes("-topmost", 1) # Ensure visible over main window
        
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
            dialog = KeybindEditorDialog(win, self, edit_mode=True, current_key=key, current_data=current_data)
            
            if dialog.result:
                new_key, new_action_data, should_update_loc = dialog.result
                
                # If key changed, we need to remove old entry
                if new_key != key:
                    del self.profiles[self.active_profile]['keybinds'][key]
                
                # Decide next steps
                if should_update_loc:
                     # Enter "Click to Set" mode
                     self.pending_key = new_key
                     self.pending_action_type = new_action_data
                     self.add_keybind_mode = True
                     self.add_button.config(state=tk.DISABLED, text="Click on Screen...")
                     self.update_status(f"Click anywhere to update '{new_key}'...")
                     
                     # Check for Evdev Engine (Wayland Support)
                     if isinstance(self.input_engine, EvdevEngine):
                         def on_evdev_edit_c(x, y, button, pressed):
                             if pressed:
                                 self.root.after(0, lambda: self.handle_click_main_thread(x, y))
                         
                         try:
                             self.input_engine.capture_single_click(on_evdev_edit_c)
                         except Exception as e:
                             print(f"[ERROR] Failed to start evdev edit capture: {e}", file=sys.stderr)

                     # Close this window so they can click
                     win.destroy() 
                else:
                    # Just update data in place
                    # If new_action_data is a dict (Text/Macro), use it directly
                    if isinstance(new_action_data, dict):
                        self.profiles[self.active_profile]['keybinds'][new_key] = new_action_data
                    else:
                        new_data = {
                            "coords": current_data.get('coords'),
                            "type": new_action_data
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
        if hasattr(self, 'input_engine') and self.input_engine:
            self.input_engine.stop_listeners()
            
        if hasattr(self, 'mouse_listener') and self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except:
                pass
                
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

    # --- Linux Capability Checks ---
    if platform.system() == "Linux":
        # Evdev Engine handles native input simulation on Linux/Wayland.
        pass
    # -------------------------------

    app = KeybindApp(root)
    root.mainloop()
