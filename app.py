import threading
import subprocess
import webbrowser

from backend.app import app


def _open_browser():
    """Open the React frontend in the default web browser."""
    webbrowser.open_new("http://127.0.0.1:5000/")


def _launch_tkinter():
    """Start the Tkinter UI in a separate process."""
    subprocess.Popen(["python", "app-sss.py"])


if __name__ == "__main__":
    _launch_tkinter()
    # Start a timer to open the browser after the server starts
    threading.Timer(1.0, _open_browser).start()
    app.run(debug=True)
