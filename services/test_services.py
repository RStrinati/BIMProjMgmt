import requests
import os

def test_acc_service_health():
    url = os.getenv("ACC_SERVICE_URL", "http://localhost:4000/api/v1/health")
    try:
        resp = requests.get(url)
        assert resp.status_code == 200
        print("ACC service health check passed.")
    except Exception as e:
        print(f"ACC service health check failed: {e}")
        assert False

def test_revizto_service_health():
    url = os.getenv("REVIZTO_SERVICE_URL", "http://localhost:5000/api/v1/health")
    try:
        resp = requests.get(url)
        assert resp.status_code == 200
        print("Revizto service health check passed.")
    except Exception as e:
        print(f"Revizto service health check failed: {e}")
        assert False

if __name__ == "__main__":
    test_acc_service_health()
    test_revizto_service_health()
