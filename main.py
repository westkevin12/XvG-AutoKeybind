import tkinter as tk
from autokeybind import KeybindApp

if __name__ == "__main__":
    root = tk.Tk()
    app = KeybindApp(root)
    root.mainloop()