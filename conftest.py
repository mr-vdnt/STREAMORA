"""
Global Test Session Fixtures for Streamora Suite.

Provides session-scoped Uvicorn server fixture for Playwright Chromium browser tests.
"""
import os
import time
import socket
import threading
import pytest
import uvicorn
from services.agent.main import app

PORT = 8899
SERVER_URL = f"http://127.0.0.1:{PORT}"


@pytest.fixture(scope="session", autouse=True)
def run_global_server():
    """Spin up a single local FastAPI Uvicorn server for the entire test session on PORT 8899."""
    os.environ["ENVIRONMENT"] = "test"
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_bound = sock.connect_ex(('127.0.0.1', PORT)) == 0
    sock.close()

    if not is_bound:
        config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        time.sleep(1.5)
    yield
