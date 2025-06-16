# ui/ui_helpers.py

from tkinter import ttk

def create_labeled_entry(parent, label_text, pack=True):
    """Create a labeled entry field.

    Parameters
    ----------
    parent : tk.Widget
        Parent widget for the entry field.
    label_text : str
        Text for the label.
    pack : bool, optional
        If True (default) the created frame will be packed into the parent.
        When False the caller is responsible for placing the frame using
        `grid` or another geometry manager.
    """
    frame = ttk.Frame(parent)
    if pack:
        frame.pack(fill="x", padx=10, pady=2)
    label = ttk.Label(frame, text=label_text, width=25, anchor="w")
    label.pack(side="left")
    entry = ttk.Entry(frame)
    entry.pack(side="left", fill="x", expand=True)
    return frame, entry

def create_labeled_combobox(parent, label_text, values, pack=True):
    """Create a labeled combobox.

    Parameters
    ----------
    parent : tk.Widget
        Parent widget for the combobox.
    label_text : str
        Text for the label.
    values : list
        Values for the combobox.
    pack : bool, optional
        If True (default) the frame is packed. Set to False when using grid.
    """
    frame = ttk.Frame(parent)
    if pack:
        frame.pack(fill="x", padx=10, pady=2)
    label = ttk.Label(frame, text=label_text, width=25, anchor="w")
    label.pack(side="left")
    combo = ttk.Combobox(frame, values=values, state="readonly")
    combo.pack(side="left", fill="x", expand=True)
    return frame, combo

def create_horizontal_button_group(parent, buttons, pack=True):
    """Create a horizontal group of buttons.

    Parameters
    ----------
    parent : tk.Widget
        Parent widget.
    buttons : list[tuple]
        Each tuple contains the button label and command.
    pack : bool, optional
        Pack the frame if True (default). When False the caller should place
        the frame manually (e.g. using ``grid``).
    """
    frame = ttk.Frame(parent)
    if pack:
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
