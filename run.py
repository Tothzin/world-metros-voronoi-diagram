"""
Script to easily run the application
"""
import subprocess
import sys
import webbrowser
import time
from threading import Timer

def open_browser():
    """Open browser after a few seconds"""
    time.sleep(2)
    webbrowser.open('http://localhost:8000')

if __name__ == "__main__":
    print("Starting Metro Voronoi Diagrams...")
    print("Server: http://localhost:8000")
    print("Wait for the server to start...\n")

    # Open browser automatically after 2 seconds
    Timer(2.0, open_browser).start()

    # Start server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped!")

