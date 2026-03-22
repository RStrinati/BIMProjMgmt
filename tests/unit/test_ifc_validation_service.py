import os
import pytest

from services.ifc_validation_service import IfcValidationService


def test_validation_missing_files_returns_error(tmp_path):
    service = IfcValidationService(temp_root=tmp_path)
    result = service.validate(str(tmp_path / "missing.ifc"), str(tmp_path / "missing.ids"))
    assert result.success is False
    assert result.errors


def test_validation_success_with_fixture_files():
    ifc_path = os.getenv("IFC_TEST_IFC_PATH")
    ids_path = os.getenv("IFC_TEST_IDS_PATH")
    if not ifc_path or not ids_path:
        pytest.skip("IFC_TEST_IFC_PATH and IFC_TEST_IDS_PATH not set")
    service = IfcValidationService()
    result = service.validate(ifc_path, ids_path)
    assert result.success is True
    assert "summary" in result.summary
