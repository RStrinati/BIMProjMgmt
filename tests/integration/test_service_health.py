import os

import pytest
import requests

def test_acc_service_health():
    url = os.getenv("ACC_SERVICE_URL", "http://localhost:4000/api/v1/health")
    try:
        resp = requests.get(url, timeout=5)
    except Exception as e:
        pytest.skip(f"ACC service health endpoint not reachable: {e}")
    assert resp.status_code == 200
    print("ACC service health check passed.")

def test_revizto_service_health():
    url = os.getenv("REVIZTO_SERVICE_URL", "http://localhost:5000/api/v1/health")
    try:
        resp = requests.get(url, timeout=5)
    except Exception as e:
        pytest.skip(f"Revizto service health endpoint not reachable: {e}")
    assert resp.status_code == 200
    print("Revizto service health check passed.")

if __name__ == "__main__":
    test_acc_service_health()
    test_revizto_service_health()
