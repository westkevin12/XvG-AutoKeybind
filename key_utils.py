from pynput.keyboard import Key, KeyCode

def get_key_name(key):
    if isinstance(key, KeyCode):
        return key.char.upper() if key.char else str(key)
    elif isinstance(key, Key):
        return key.name.title()
    return str(key)

def get_key_combo_string(keys):
    sorted_keys = sorted(keys, key=lambda k: (
        0 if isinstance(k, Key) and k.name in ['ctrl', 'ctrl_l', 'ctrl_r', 'shift', 'shift_l', 'shift_r', 'alt', 'alt_l', 'alt_r', 'cmd', 'cmd_l', 'cmd_r'] else 1,
        str(k)
    ))
    return "+".join([get_key_name(k) for k in sorted_keys])
