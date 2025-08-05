import threading
import subprocess
import webbrowser
import os
import platform

from backend import flask_app
from config import Config

def is_gui_available():
    """Check if the environment supports GUI for Tkinter."""
    return platform.system() == "Windows" or os.environ.get("DISPLAY")

def _open_browser():
    """Open the React frontend in the default web browser."""
    webbrowser.open_new("http://127.0.0.1:5000/")

def _launch_tkinter():
    """Start the Tkinter UI in a separate process."""
    subprocess.Popen(["python", "app-sss.py"])

if __name__ == "__main__":
    print(f"Connected to SQL Server at: {Config.DB_SERVER}")

    try:
        print("🔍 Checking and autofixing schema...")
        subprocess.run(["python", "check_schema.py", "--autofix", "--update-constants"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Schema check failed: {e}")
        exit(1)

    if is_gui_available():
        _launch_tkinter()

    threading.Timer(1.0, _open_browser).start()
    flask_app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
