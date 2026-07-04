import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Scrollbar, Listbox
from tkinter.ttk import Frame, Label, Entry, Button
from pynput.keyboard import Key, Listener
from pynput.mouse import Listener as MouseListener
from key_utils import get_key_combo_string
from input_engine import EvdevEngine
from constants import (
    ACTION_CLICK_RETURN,
    ACTION_CLICK_STAY,
    ACTION_DOUBLE_CLICK_RETURN,
    ACTION_DRAG_RETURN,
    ACTION_MACRO,
    ACTION_TEXT,
    ACTION_TYPES
)

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
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Click (In Place)")
        self.geometry("350x320")
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
        self.app = parent.app
        self.title("Add Key Action")
        self.geometry("400x300")
        self.resizable(False, False)
        self.wm_attributes("-topmost", 1)
        self.result = None
        
        self.pressed_keys = set()
        
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
        if getattr(self.app, 'capture_key_callback', None) == self.on_press_capture:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.key_display_var.set("Press a key...")
        self.record_btn.configure(text="Stop Recording") 
        
        # Use main app capture callback exclusively
        self.app.capture_key_callback = self.on_press_capture

    def stop_recording(self):
        if getattr(self.app, 'capture_key_callback', None) == self.on_press_capture:
            self.app.capture_key_callback = None
        self.record_btn.configure(text="Record Key")

    def on_press_capture(self, key):
        self.on_press(key)
        return False

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
        self.wm_attributes("-topmost", 1)
        self.result = None
        
        self.playback_config = {}
        if isinstance(current_actions, dict) and 'actions' in current_actions:
            self.actions = current_actions.get('actions', [])
            self.playback_config = current_actions.get('playback', {})
        elif isinstance(current_actions, list):
            self.actions = current_actions
        else:
            self.actions = []
        
        # 1. Header: Name Field
        header_frame = Frame(self, padding=10)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        Label(header_frame, text="Macro Name:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value=current_actions.get('name', 'My Macro') if isinstance(current_actions, dict) else "My Macro")
        ttk.Entry(header_frame, textvariable=self.name_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 2. Footer: Playback & Buttons
        bottom_frame = Frame(self, padding=10, relief="groove", borderwidth=1)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
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

        btn_box = Frame(bottom_frame)
        btn_box.pack(side=tk.RIGHT)
        
        ttk.Button(btn_box, text="Save", command=self.on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

        # 3. Middle: Actions List
        self.main_frame = Frame(self, padding=10)
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        list_frame = Frame(self.main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        Label(list_frame, text="Action Sequence:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        
        self.listbox = Listbox(list_frame, height=15, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self.refresh_list()
        
        # Buttons
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
                self.after(0, lambda: click_detected.set(True))
                return False
        
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
        self.wm_attributes("-topmost", 1)
        self.result = None
        self.edit_mode = edit_mode
        self.current_data = current_data
        
        self.pressed_keys = set()
        
        # Bottom Buttons
        btn_frame = Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        ok_text = "Save Changes" if edit_mode else "Set Location & Save"
        self.ok_btn = Button(btn_frame, text=ok_text, command=self.on_ok)
        self.ok_btn.pack(side=tk.RIGHT, padx=(10, 0))
        Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

        # Main Frame
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
        
        self.loc_widgets = []
        self.text_widgets = []
        
        # -- Location Widgets --
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
        
        self.on_type_changed(None)
        
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
        
        for w in self.loc_widgets: w.grid_remove()
        for w in self.text_widgets: w.pack_forget() if isinstance(w, Frame) else w.grid_remove() 
        for child in self.content_frame.winfo_children():
            child.grid_remove()
            
        if action == ACTION_MACRO:
             Label(self.content_frame, text="Select Macro:", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 5))
             
             macros = self.app.profiles[self.app.active_profile].get('macros', {})
             macro_names = sorted(macros.keys())
             
             self.macro_select_var = tk.StringVar()
             if self.current_data and self.current_data.get('type') == ACTION_MACRO:
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
            if 'macros' not in self.app.profiles[self.app.active_profile]:
                self.app.profiles[self.app.active_profile]['macros'] = {}
            self.app.profiles[self.app.active_profile]['macros'][name] = editor.result
            self.app.save_profiles()
            self.on_type_changed(None)
            macros = self.app.profiles[self.app.active_profile].get('macros', {})
            macro_names = sorted(macros.keys())
            self.macro_combo['values'] = macro_names
            self.macro_select_var.set(name)

    def edit_selected_macro(self):
        name = self.macro_select_var.get()
        if not name: return
        macros = self.app.profiles[self.app.active_profile].get('macros', {})
        data = macros.get(name)
        editor = MacroEditorDialog(self, self.app, data)
        if editor.result:
            new_name = editor.result.get('name')
            if new_name != name:
                del macros[name]
            macros[new_name] = editor.result
            self.app.save_profiles()
            self.on_type_changed(None)
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
        if getattr(self.app, 'capture_key_callback', None) == self.on_press:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.pressed_keys.clear()
        self.key_display_var.set("Press keys...")
        self.record_btn.configure(text="Stop Recording") 
        self.app.capture_key_callback = self.on_press

    def stop_recording(self):
        if getattr(self.app, 'capture_key_callback', None) == self.on_press:
            self.app.capture_key_callback = None
        self.record_btn.configure(text="Record Key")
        
    def on_press(self, key):
        self.pressed_keys.add(key)
        self.update_display()
        return True

    def on_release(self, key):
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
            self.result = (key, data, False)
            self.destroy()
            return

        should_update = self.update_loc_var.get() if self.edit_mode else True
        self.result = (key, action_type, should_update)
        self.destroy()
