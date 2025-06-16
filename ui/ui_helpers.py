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

# Helper to create a scrollable frame within a tab
import tkinter as tk

def create_scrollable_frame(parent):
    """Return a frame with vertical scrolling enabled."""
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable = ttk.Frame(canvas)

    scrollable.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return scrollable
