# ui/ui_helpers.py

from tkinter import ttk

def create_labeled_entry(parent, label_text):
    """Creates a labeled entry field"""
    frame = ttk.Frame(parent)
    frame.pack(fill="x", padx=10, pady=2)
    label = ttk.Label(frame, text=label_text, width=25, anchor="w")
    label.pack(side="left")
    entry = ttk.Entry(frame)
    entry.pack(side="left", fill="x", expand=True)
    return frame, entry

def create_labeled_combobox(parent, label_text, values):
    """Creates a labeled combobox"""
    frame = ttk.Frame(parent)
    frame.pack(fill="x", padx=10, pady=2)
    label = ttk.Label(frame, text=label_text, width=25, anchor="w")
    label.pack(side="left")
    combo = ttk.Combobox(frame, values=values, state="readonly")
    combo.pack(side="left", fill="x", expand=True)
    return frame, combo

def create_horizontal_button_group(parent, buttons):
    """Creates a horizontal group of buttons. `buttons` is a list of tuples (label, command)."""
    frame = ttk.Frame(parent)
    frame.pack(padx=10, pady=10, anchor="w")
    for label, command in buttons:
        button = ttk.Button(frame, text=label, command=command)
        button.pack(side="left", padx=5)
    return frame
