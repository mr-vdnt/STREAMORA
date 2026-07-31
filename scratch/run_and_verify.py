import subprocess
import time
import sys
import os

print("Starting FastAPI server...")
server = subprocess.Popen([sys.executable, "services/agent/main.py"])
time.sleep(3) # Wait for server to start

try:
    print("Running verification script...")
    result = subprocess.run([sys.executable, "scratch/verify_rc2_2.py"], capture_output=True, text=True)
    print("Verification Script Output:")
    print(result.stdout)
    if result.stderr:
        print("Verification Script Errors:")
        print(result.stderr)
finally:
    print("Terminating server...")
    server.terminate()
    server.wait()
    print("Done.")
