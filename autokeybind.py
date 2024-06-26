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
import pickle

# Initialize profiles dictionary
profiles = {}
coords = []
active_profile = None

# Function to load profiles from a .dat file and set the active profile
def load_profiles():
    global active_profile, coords, profiles
    default_profile_name = "Default"

    # Check if the profiles file exists
    if os.path.exists('profiles.dat'):
        try:
            with open('profiles.dat', 'rb') as file:
                profiles = pickle.load(file)

            if not active_profile:
                active_profile = default_profile_name

        except FileNotFoundError:
            pass  # Failed to open the profiles file

# Function to save profiles to a .dat file
def save_profiles():
    global profiles
    with open('profiles.dat', 'wb') as file:
        pickle.dump(profiles, file)

# Function to add a profile
def add_profile(profile_name):
    global active_profile, profiles
    if profile_name not in profiles:
        profiles[profile_name] = {'keybinds': {}}
        save_profiles()
    else:
        print("Profile already exists.")
        load_profiles()

# Function to remove a profile
def remove_profile(profile_name):
    global active_profile, profiles
    if profile_name in profiles:
        del profiles[profile_name]
        save_profiles()
    else:
        print("Profile does not exist.")

# Function to rename a profile
def rename_profile(old_name, new_name):
    global active_profile, profiles
    if old_name in profiles:
        profiles[new_name] = profiles.pop(old_name)
        save_profiles()
    else:
        print("Profile does not exist.")

# Function to click a coordinate from the active profile
def click_coordinate(x, y):
    original_position = pyautogui.position()
    pyautogui.click(x, y)
    pyautogui.moveTo(original_position)

# Function to add a keybind
def add_keybind():
    add_keybind_mode[0] = True
    key_entry.delete(0, tk.END)
    add_button.config(state=tk.DISABLED)

# Function to handle key releases and click the corresponding coordinate
def on_key_release(key):
    global active_profile, coords
    try:
        key_str = key.char
        if active_profile and 'keybinds' in profiles[active_profile] and key_str in profiles[active_profile]['keybinds']:
            index = profiles[active_profile]['keybinds'][key_str]
            if 0 <= index < len(coords):
                x, y = coords[index]
                click_coordinate(x, y)
    except AttributeError:
        pass

# Function to capture mouse position
def capture_mouse_position(x, y, button, pressed):
    global active_profile, coords
    if pressed and add_keybind_mode[0]:
        coords.append((x, y))
        key = key_entry.get()
        if key and key not in profiles[active_profile]['keybinds']:
            profiles[active_profile]['keybinds'][key] = len(coords) - 1
            save_profiles()
        key_entry.delete(0, tk.END)
        add_keybind_mode[0] = False
        add_button.config(state=tk.NORMAL)

# Function to clear keybinds
def clear_keybinds():
    global active_profile
    profiles[active_profile]['keybinds'].clear()
    save_profiles()

# Function to show and edit keybinds
def show_keybinds():
    global active_profile, coords
    if active_profile in profiles:
        keybind_window = tk.Toplevel()
        keybind_window.title("Edit Keybinds")
        keybind_window.wm_attributes("-topmost", 2)
        keybind_listbox = Listbox(keybind_window, selectmode=tk.SINGLE)
        keybind_listbox.pack()

        for key, index in profiles[active_profile]['keybinds'].items():
            index = profiles[active_profile]['keybinds'][key]
            if 0 <= index < len(coords):
                keybind_listbox.insert(tk.END, f"{key}: coords: {coords[index]}")

        def delete_keybind():
            global active_profile, coords
            selected_index = keybind_listbox.curselection()
            if selected_index:
                selected_index = int(selected_index[0])
                key = list(profiles[active_profile]['keybinds'].keys())[selected_index]
                del profiles[active_profile]['keybinds'][key]
                keybind_listbox.delete(selected_index)
                save_profiles()

        delete_button = Button(keybind_window, text="Delete", command=delete_keybind)
        delete_button.pack()

        instruction_label = Label(keybind_window, text="Select a keybind to delete")
        instruction_label.pack()

# Function to handle the application exit
def on_close():
    listener.stop()
    mouse_listener.stop()
    save_profiles()
    sys.exit(0)

# Function to create the system tray icon
def create_system_tray_icon():
    menu = (
        pystray.MenuItem('Exit', on_exit),
    )

    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
    else:
        icon_path = 'icon.ico'

    icon_image = Image.open(icon_path)
    icon = pystray.Icon("name", icon_image, menu=menu)
    return icon

# Function to handle exit from system tray
def on_exit(icon, item):
    icon.stop()
    on_close()

if not profiles:
    load_profiles()
    if not profiles:
        default_profile_name = "Default"
        add_profile(default_profile_name)
        active_profile = default_profile_name

# Create a variable to store the keybind mode
add_keybind_mode = [False]

if __name__ == "__main__":
    icon = create_system_tray_icon()
    load_profiles()

    with Listener(on_release=on_key_release) as listener, MouseListener(on_click=capture_mouse_position) as mouse_listener:
        autokeybind = tk.Tk()
        autokeybind.title("XvG Auto Keybind")
        autokeybind.wm_attributes("-topmost", 1)
        autokeybind.geometry("275x430+100+100")
        autokeybind.protocol("WM_DELETE_WINDOW", on_close)

        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = 'icon.ico'

        icon = Image.open(icon_path)
        icon_photo = ImageTk.PhotoImage(icon)
        autokeybind.tk.call('wm', 'iconphoto', autokeybind._w, icon_photo)

        key_label = Label(autokeybind, text="Enter Key:")
        key_label.pack()

        key_entry = Entry(autokeybind)
        key_entry.pack()

        add_button = Button(autokeybind, text="Add Keybind", command=add_keybind)
        add_button.pack()

        reset_button = Button(autokeybind, text="Reset Keybinds", command=clear_keybinds)
        reset_button.pack()

        binds_button = Button(autokeybind, text="Binds", command=show_keybinds)
        binds_button.pack()

        profile_listbox = Listbox(autokeybind, selectmode=tk.SINGLE)
        profile_listbox.pack()

        add_profile_button = Button(autokeybind, text="Add Profile")
        add_profile_button.pack(side='left')

        remove_profile_button = Button(autokeybind, text="Remove Profile")
        remove_profile_button.pack(side='left')

        rename_profile_button = Button(autokeybind, text="Rename Profile")
        rename_profile_button.pack(side='left')

        for profile_name in profiles:
            profile_listbox.insert(tk.END, profile_name)

        def add_profile_action():
            profile_name = simpledialog.askstring("Add Profile", "Enter Profile Name:")
            if profile_name:
                add_profile(profile_name)
                profile_listbox.insert(tk.END, profile_name)

        def remove_profile_action():
            selected_index = profile_listbox.curselection()
            if selected_index:
                selected_index = int(selected_index[0])
                profile_name = profile_listbox.get(selected_index)
                response = messagebox.askyesno("Remove Profile", f"Are you sure you want to remove the profile '{profile_name}'?")
                if response == tk.YES:
                    remove_profile(profile_name)
                    profile_listbox.delete(selected_index)

        def rename_profile_action():
            selected_index = profile_listbox.curselection()
            if selected_index:
                selected_index = int(selected_index[0])
                profile_name = profile_listbox.get(selected_index)
                new_name = simpledialog.askstring("Rename Profile", f"Enter new name for profile '{profile_name}':")
                if new_name:
                    rename_profile(profile_name, new_name)
                    profile_listbox.delete(selected_index)
                    profile_listbox.insert(selected_index, new_name)

        def activate_profile(event):
            global active_profile
            selected_index = profile_listbox.curselection()
            if selected_index:
                selected_index = int(selected_index[0])
                profile_name = profile_listbox.get(selected_index)
                active_profile = profile_name

        add_profile_button.config(command=add_profile_action)
        remove_profile_button.config(command=remove_profile_action)
        rename_profile_button.config(command=rename_profile_action)
        profile_listbox.bind("<<ListboxSelect>>", activate_profile)

        listener_thread = threading.Thread(target=listener.join)
        listener_thread.start()

        mouse_listener_thread = threading.Thread(target=mouse_listener.join)
        mouse_listener_thread.start()

        if not profiles:
            load_profiles()
            if not profiles:
                default_profile_name = "Default"
                add_profile(default_profile_name)
                active_profile = default_profile_name

        autokeybind.mainloop()
