# ui/status_bar.py

import datetime

def update_status(status_var, message):
    """
    Update the status bar with a timestamped message.
    """
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    status_var.set(f"[{timestamp}] {message}")
