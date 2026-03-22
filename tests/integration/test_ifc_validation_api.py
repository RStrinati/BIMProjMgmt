import os
import sys

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import app  # noqa: E402


@pytest.mark.integration
def test_ifc_validation_requires_ifc_file():
    client = app.test_client()
    response = client.post(
        "/api/projects/1/ifc-validation/run",
        data={},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
