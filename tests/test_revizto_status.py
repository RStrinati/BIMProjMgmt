import json
import os

import requests


def test_revizto_status_endpoint():
    """Smoke test: ensure Revizto exporter status endpoint responds successfully."""
    base_url = os.getenv("BIM_API_BASE_URL", "http://localhost:5000/api")
    url = f"{base_url}/revizto/status"
    resp = requests.get(url, timeout=15)

    assert resp.status_code == 200, f"Unexpected status code {resp.status_code}: {resp.text}"

    data = resp.json()
    assert data.get("success"), f"API reported failure: {data}"

    result = data.get("result", {})
    assert result.get("returncode") == 0, f"CLI returned error: {json.dumps(result, indent=2)}"

    parsed = result.get("parsed") or {}
    status = parsed.get("status") or {}

    # Basic sanity checks
    assert "projectCount" in status, f"Missing projectCount in status: {status}"
    assert "databaseConnected" in status, f"Missing databaseConnected in status: {status}"
