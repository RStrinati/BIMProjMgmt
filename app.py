import threading
import subprocess
import webbrowser
import os
from backend import flask_app
from config import Config

server = Config.DB_SERVER
user = Config.DB_USER
password = Config.DB_PASSWORD
driver = Config.DB_DRIVER

def _open_browser():
    """Open the React frontend in the default web browser."""
    webbrowser.open_new("http://127.0.0.1:5000/")


def _launch_tkinter():
    """Start the Tkinter UI in a separate process."""
    subprocess.Popen(["python", "app-sss.py"])


if __name__ == "__main__":
    print(f"Connected to SQL Server at: {Config.DB_SERVER}")
    # Only start the Tkinter UI when a display is detected. This prevents
    # crashes in headless environments where launching a GUI would fail.
    if os.environ.get("DISPLAY"):
        _launch_tkinter()
    # Start a timer to open the browser after the server starts
    threading.Timer(1.0, _open_browser).start()
    flask_app.run(debug=True, use_reloader=False)


