import subprocess
import time
import requests
import sys
import pytest

@pytest.mark.skip(reason="Standalone live integration script")
def test_live_health_standalone():
    pass

if __name__ == "__main__":
    print("Starting microservices...")
    processes = []
    try:
        processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "services.ranking.main:app", "--port", "8001"]))
        processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "services.event-processor.main:app", "--port", "8002"]))
        processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "services.rag.main:app", "--port", "8003"]))
        processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "services.agent.main:app", "--port", "8004"]))
        
        time.sleep(18)
        
        print("Querying Agent Gateway health endpoint...")
        r = requests.get("http://127.0.0.1:8004/health", timeout=5)
        print("Status Code:", r.status_code)
        print("Response JSON:", r.json())
        
        data = r.json()
        assert r.status_code == 200
        assert data["status"] == "healthy"
        assert data["microservices"]["ranking"] == "healthy"
        assert data["microservices"]["event_processor"] == "healthy"
        assert data["microservices"]["rag"] == "healthy"
        print("\n[OK] Integration Check PASSED: All microservices are healthy.")
    except Exception as e:
        print("\n[FAIL] Integration Check FAILED:", e)
        sys.exit(1)
    finally:
        print("Stopping microservices...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                p.kill()
    print("Cleanup done.")
