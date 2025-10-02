# ui/ui_helpers.py

from tkinter import ttk
import tkinter as tk
from typing import Iterable, List, Optional, Sequence, Tuple

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

def create_scrollable_frame(parent, scroll_x=False, scroll_y=True):
    """Create a scrollable frame that supports vertical and optionally horizontal scrolling."""
    container = ttk.Frame(parent, width=1280)
    container.pack(fill="both", expand=True)
    # Prevent children from expanding the container beyond its width
    container.pack_propagate(False)

    canvas = tk.Canvas(container, highlightthickness=0)
    scrollable = ttk.Frame(canvas)

    v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview) if scroll_y else None
    h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview) if scroll_x else None

    if scroll_y:
        canvas.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side="right", fill="y")
    if scroll_x:
        canvas.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x")

    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    return scrollable


# Additional small helpers used across tabs

def clear_treeview(tree: ttk.Treeview) -> None:
    """Efficiently remove all rows from a Treeview."""
    children = tree.get_children()
    if children:
        tree.delete(*children)


def format_id_name_list(rows: Sequence[Tuple[object, object]]) -> List[str]:
    """Format (id, name) pairs into 'id - name' display strings for Comboboxes."""
    values: List[str] = []
    for _id, name in rows:
        try:
            values.append(f"{int(_id)} - {name}")
        except Exception:
            values.append(f"{_id} - {name}")
    return values


def parse_id_from_display(value: str) -> Optional[int]:
    """Extract the integer id from a 'id - name' style string."""
    if not value or " - " not in value:
        return None
    head = value.split(" - ", 1)[0].strip()
    try:
        return int(head)
    except ValueError:
        return None


def set_combo_from_pairs(combo: ttk.Combobox, rows: Sequence[Tuple[object, object]]) -> None:
    """Set combobox values from (id, name) pairs using the standard display format."""
    combo["values"] = format_id_name_list(rows)

