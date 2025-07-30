import threading
import webbrowser

from backend.app import app


def _open_browser():
    """Open the React frontend in the default web browser."""
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    # Start a timer to open the browser after the server starts
    threading.Timer(1.0, _open_browser).start()
    app.run(debug=True)
