"""Native desktop launcher for the Kobo → Anki Streamlit app."""

import atexit
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request

import webview


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def wait_for_server(port: int, timeout: float = 15.0) -> bool:
    """Poll localhost:{port} until the Streamlit server is ready."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/_stcore/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    port = find_free_port()
    app_dir = os.path.dirname(os.path.abspath(__file__))

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            os.path.join(app_dir, "main.py"),
            f"--server.port={port}",
            "--server.headless=true",
            "--global.developmentMode=false",
        ],
        cwd=app_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    def cleanup():
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    if not wait_for_server(port):
        print("Streamlit server failed to start.", file=sys.stderr)
        cleanup()
        sys.exit(1)

    window = webview.create_window(
        "Kobo → Anki Flashcards",
        f"http://localhost:{port}",
        width=900,
        height=800,
    )
    webview.start()


if __name__ == "__main__":
    main()
