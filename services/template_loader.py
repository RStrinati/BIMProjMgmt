import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_TEMPLATE_PATH = PROJECT_ROOT / "backend" / "data" / "service_templates.json"
LEGACY_TEMPLATE_PATH = PROJECT_ROOT / "templates" / "service_templates.json"


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        logging.error("Invalid JSON in template file %s: %s", path, exc)
        return None
    except Exception as exc:
        logging.exception("Failed to read template file %s: %s", path, exc)
        return None


def load_service_template_sources() -> Dict[str, Any]:
    """Load canonical and legacy template payloads via a single loader."""
    canonical = _read_json(CANONICAL_TEMPLATE_PATH)
    legacy = _read_json(LEGACY_TEMPLATE_PATH)

    payload: Dict[str, Any] = {
        "canonical_path": str(CANONICAL_TEMPLATE_PATH),
        "legacy_path": str(LEGACY_TEMPLATE_PATH),
    }

    if canonical:
        payload["canonical"] = canonical
        payload["schema_version"] = canonical.get("schema_version")
        templates = canonical.get("templates")
        payload["templates"] = templates if isinstance(templates, list) else []

    if legacy:
        payload["legacy"] = legacy
        legacy_templates = legacy.get("templates")
        payload["legacy_templates"] = legacy_templates if isinstance(legacy_templates, list) else []

    return payload
