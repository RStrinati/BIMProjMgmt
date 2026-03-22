import logging
import os
import tempfile
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ifcopenshell

logger = logging.getLogger(__name__)


@dataclass
class IfcValidationResult:
    success: bool
    ifc_filename: str
    ids_filename: str
    summary: Dict[str, Any]
    specifications: List[Dict[str, Any]]
    errors: List[str]
    html_report: Optional[str] = None


class IfcValidationService:
    def __init__(self, temp_root: Optional[Path] = None) -> None:
        if temp_root is None:
            temp_root = Path(__file__).resolve().parent.parent / ".tmp" / "ifc_validation"
        self.temp_root = temp_root
        self.temp_root.mkdir(parents=True, exist_ok=True)

    def create_temp_dir(self, run_id: Optional[int] = None) -> Path:
        prefix = f"run_{run_id}_" if run_id else "run_"
        path = Path(tempfile.mkdtemp(prefix=prefix, dir=self.temp_root))
        return path

    def cleanup_temp_dir(self, path: Path) -> None:
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception as exc:
            logger.warning("Failed to cleanup temp dir %s: %s", path, exc)

    def validate_paths(self, ifc_path: str, ids_path: str) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not ifc_path or not os.path.exists(ifc_path):
            errors.append("IFC file not found.")
        if not ids_path or not os.path.exists(ids_path):
            errors.append("IDS file not found.")
        return (len(errors) == 0), errors

    def validate(self, ifc_path: str, ids_path: str) -> IfcValidationResult:
        is_valid, errors = self.validate_paths(ifc_path, ids_path)
        if not is_valid:
            return IfcValidationResult(
                success=False,
                ifc_filename=os.path.basename(ifc_path or ""),
                ids_filename=os.path.basename(ids_path or ""),
                summary=self._empty_summary(),
                specifications=[],
                errors=errors,
            )

        try:
            ifc_file = ifcopenshell.open(ifc_path)
        except Exception as exc:
            logger.exception("Failed to open IFC file")
            return IfcValidationResult(
                success=False,
                ifc_filename=os.path.basename(ifc_path),
                ids_filename=os.path.basename(ids_path),
                summary=self._empty_summary(),
                specifications=[],
                errors=[f"IFC parsing failure: {exc}"],
            )

        try:
            ids_doc = self._load_ids(ids_path)
        except Exception as exc:
            logger.exception("Failed to load IDS file")
            return IfcValidationResult(
                success=False,
                ifc_filename=os.path.basename(ifc_path),
                ids_filename=os.path.basename(ids_path),
                summary=self._empty_summary(),
                specifications=[],
                errors=[f"IDS parsing failure: {exc}"],
            )

        try:
            report = self._run_validation(ids_doc, ifc_file)
        except Exception as exc:
            logger.exception("Validation runtime failure")
            return IfcValidationResult(
                success=False,
                ifc_filename=os.path.basename(ifc_path),
                ids_filename=os.path.basename(ids_path),
                summary=self._empty_summary(),
                specifications=[],
                errors=[f"Validation runtime failure: {exc}"],
            )

        specifications = self._normalize_report(ids_doc, report, ifc_file)
        summary = self._summarize(specifications)
        html_report = self._render_html_report(
            ifc_filename=os.path.basename(ifc_path),
            ids_filename=os.path.basename(ids_path),
            summary=summary,
            specifications=specifications,
        )

        return IfcValidationResult(
            success=True,
            ifc_filename=os.path.basename(ifc_path),
            ids_filename=os.path.basename(ids_path),
            summary=summary,
            specifications=specifications,
            errors=[],
            html_report=html_report,
        )

    def _load_ids(self, ids_path: str) -> Any:
        # Support multiple ifctester API versions
        try:
            from ifctester import ids as ids_module  # type: ignore
        except Exception as exc:
            raise RuntimeError("ifctester is not installed") from exc

        if hasattr(ids_module, "open"):
            return ids_module.open(ids_path)
        if hasattr(ids_module, "Ids"):
            ids_cls = getattr(ids_module, "Ids")
            if hasattr(ids_cls, "open"):
                return ids_cls.open(ids_path)
        raise RuntimeError("Unsupported ifctester IDS API. Cannot load IDS file.")

    def _run_validation(self, ids_doc: Any, ifc_file: Any) -> Any:
        if hasattr(ids_doc, "validate"):
            return ids_doc.validate(ifc_file)
        if hasattr(ids_doc, "apply"):
            return ids_doc.apply(ifc_file)
        raise RuntimeError("Unsupported ifctester IDS API. Cannot run validation.")

    def _normalize_report(self, ids_doc: Any, report: Any, ifc_file: Any) -> List[Dict[str, Any]]:
        # Best-effort normalization across ifctester versions
        specs: List[Any] = []
        if hasattr(report, "specifications"):
            specs = list(getattr(report, "specifications") or [])
        elif hasattr(ids_doc, "specifications"):
            specs = list(getattr(ids_doc, "specifications") or [])

        normalized: List[Dict[str, Any]] = []
        for spec in specs:
            normalized.append(self._normalize_spec(spec, ifc_file))
        return normalized

    def _normalize_spec(self, spec: Any, ifc_file: Any) -> Dict[str, Any]:
        name = getattr(spec, "name", None) or getattr(spec, "title", None) or "Unnamed specification"
        description = getattr(spec, "description", None) or ""
        status = self._coerce_status(getattr(spec, "status", None))
        failures = self._extract_failures(spec, ifc_file)
        fail_count = len(failures)
        passed_count = max(0, int(getattr(spec, "passed", 0) or 0))
        if status is None:
            status = "fail" if fail_count > 0 else "pass"

        return {
            "name": str(name),
            "description": str(description) if description is not None else "",
            "status": status,
            "fail_count": fail_count,
            "passed_count": passed_count,
            "failed_entities": failures,
        }

    def _extract_failures(self, spec: Any, ifc_file: Any) -> List[Dict[str, Any]]:
        failures: List[Dict[str, Any]] = []
        candidates = []
        for attr in ("failed_entities", "failures", "failed"):
            if hasattr(spec, attr):
                candidates = getattr(spec, attr) or []
                break
        # ifctester sometimes exposes results with status + elements
        if not candidates and hasattr(spec, "results"):
            results = getattr(spec, "results") or []
            for result in results:
                status = str(getattr(result, "status", "")).lower()
                if status not in ("fail", "failed"):
                    continue
                candidates.extend(self._result_to_failures(result))
        for entry in candidates or []:
            failures.append(self._normalize_failure(entry, ifc_file))
        return failures

    def _result_to_failures(self, result: Any) -> List[Any]:
        entries: List[Any] = []
        for attr in ("failed_entities", "failures", "failed"):
            if hasattr(result, attr):
                entries.extend(getattr(result, attr) or [])
        if entries:
            return entries
        # Try to expand elements/entities lists
        for attr in ("elements", "entities", "items"):
            if hasattr(result, attr):
                entities = getattr(result, attr) or []
                message = (
                    getattr(result, "message", None)
                    or getattr(result, "reason", None)
                    or getattr(result, "description", None)
                    or getattr(result, "requirement", None)
                )
                for entity in entities:
                    entries.append({
                        "element": entity,
                        "message": message,
                    })
        return entries

    def _normalize_failure(self, entry: Any, ifc_file: Any) -> Dict[str, Any]:
        # Extract only requested fields: spec name, message, ifc class, object name
        if isinstance(entry, dict):
            element = entry.get("element") or entry.get("entity") or entry.get("item")
            ifc_class = entry.get("ifc_class") or entry.get("ifcClass")
            object_name = entry.get("name") or entry.get("object_name")
            message = entry.get("message") or entry.get("reason") or entry.get("description") or entry.get("requirement")
            resolved = self._resolve_entity_context(entry, element, ifc_file)
            ifc_class = ifc_class or resolved.get("ifc_class")
            object_name = object_name or resolved.get("object_name")
            if message is None:
                message = "Requirement not met"
            return {
                "ifc_class": ifc_class,
                "object_name": object_name,
                "message": message,
            }

        ifc_class = getattr(entry, "ifc_class", None) or getattr(entry, "ifcClass", None)
        object_name = getattr(entry, "name", None) or getattr(entry, "object_name", None)
        message = (
            getattr(entry, "message", None)
            or getattr(entry, "reason", None)
            or getattr(entry, "description", None)
            or getattr(entry, "requirement", None)
        )
        element = getattr(entry, "element", None) or getattr(entry, "entity", None) or getattr(entry, "item", None)
        resolved = self._resolve_entity_context(entry, element, ifc_file)
        ifc_class = ifc_class or resolved.get("ifc_class")
        object_name = object_name or resolved.get("object_name")
        if message is None:
            message = "Requirement not met"
        return {
            "ifc_class": ifc_class,
            "object_name": object_name,
            "message": message,
        }

    def _resolve_entity_context(self, entry: Any, element: Any, ifc_file: Any) -> Dict[str, Optional[str]]:
        ifc_class = None
        object_name = None

        if element is not None:
            try:
                ifc_class = element.is_a()
            except Exception:
                pass
            object_name = getattr(element, "Name", None) or getattr(element, "name", None)
            if ifc_class or object_name:
                return {"ifc_class": ifc_class, "object_name": object_name}

        # Try resolve by STEP id
        step_id = None
        if isinstance(entry, dict):
            step_id = entry.get("step_id") or entry.get("id") or entry.get("stepId")
        else:
            step_id = getattr(entry, "step_id", None) or getattr(entry, "id", None) or getattr(entry, "stepId", None)

        if step_id is not None:
            try:
                entity = ifc_file.by_id(int(step_id))
                if entity:
                    return {
                        "ifc_class": entity.is_a(),
                        "object_name": getattr(entity, "Name", None) or getattr(entity, "name", None),
                    }
            except Exception:
                pass

        # Try resolve by GlobalId
        global_id = None
        if isinstance(entry, dict):
            global_id = entry.get("global_id") or entry.get("GlobalId")
        else:
            global_id = getattr(entry, "global_id", None) or getattr(entry, "GlobalId", None)

        if global_id:
            try:
                matches = ifc_file.by_guid(str(global_id))
                if matches:
                    entity = matches[0] if isinstance(matches, list) else matches
                    return {
                        "ifc_class": entity.is_a(),
                        "object_name": getattr(entity, "Name", None) or getattr(entity, "name", None),
                    }
            except Exception:
                pass

        return {"ifc_class": None, "object_name": None}

    def _coerce_status(self, status: Any) -> Optional[str]:
        if status is None:
            return None
        value = str(status).lower()
        if "pass" in value:
            return "pass"
        if "fail" in value:
            return "fail"
        if "warn" in value:
            return "warn"
        return None

    def _summarize(self, specifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(specifications)
        passed = sum(1 for s in specifications if s.get("status") == "pass")
        failed = sum(1 for s in specifications if s.get("status") == "fail")
        failures_total = sum(int(s.get("fail_count") or 0) for s in specifications)
        return {
            "total_specifications": total,
            "passed_specifications": passed,
            "failed_specifications": failed,
            "total_entities_checked": None,
            "total_failures": failures_total,
        }

    def _empty_summary(self) -> Dict[str, Any]:
        return {
            "total_specifications": 0,
            "passed_specifications": 0,
            "failed_specifications": 0,
            "total_entities_checked": 0,
            "total_failures": 0,
        }

    def _render_html_report(
        self,
        ifc_filename: str,
        ids_filename: str,
        summary: Dict[str, Any],
        specifications: List[Dict[str, Any]],
    ) -> str:
        timestamp = datetime.utcnow().isoformat()
        rows = []
        for spec in specifications:
            status = spec.get("status", "unknown")
            fail_count = spec.get("fail_count", 0)
            rows.append(
                f"<tr><td>{self._escape(str(spec.get('name')))}</td>"
                f"<td>{self._escape(status)}</td>"
                f"<td>{fail_count}</td></tr>"
            )
        details = []
        for spec in specifications:
            failures = spec.get("failed_entities", [])
            if not failures:
                continue
            detail_rows = []
            for failure in failures:
                detail_rows.append(
                    "<tr>"
                    f"<td>{self._escape(str(failure.get('ifc_class') or ''))}</td>"
                    f"<td>{self._escape(str(failure.get('object_name') or ''))}</td>"
                    f"<td>{self._escape(str(failure.get('message') or ''))}</td>"
                    "</tr>"
                )
            details.append(
                f"<h3>{self._escape(str(spec.get('name')))}</h3>"
                "<table><thead><tr><th>IFC Class</th><th>Object Name</th><th>Message</th></tr></thead>"
                f"<tbody>{''.join(detail_rows)}</tbody></table>"
            )
        html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>IFC IDS Validation Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 16px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f3f4f6; }}
    h1, h2, h3 {{ margin-bottom: 8px; }}
  </style>
</head>
<body>
  <h1>IFC IDS Validation Report</h1>
  <p><strong>IFC:</strong> {self._escape(ifc_filename)}<br/>
     <strong>IDS:</strong> {self._escape(ids_filename)}<br/>
     <strong>Generated:</strong> {self._escape(timestamp)}</p>
  <h2>Summary</h2>
  <ul>
    <li>Total specifications: {summary.get("total_specifications")}</li>
    <li>Passed specifications: {summary.get("passed_specifications")}</li>
    <li>Failed specifications: {summary.get("failed_specifications")}</li>
    <li>Total failures: {summary.get("total_failures")}</li>
  </ul>
  <h2>Specification Results</h2>
  <table>
    <thead><tr><th>Specification</th><th>Status</th><th>Failures</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <h2>Failure Details</h2>
  {''.join(details) if details else "<p>No failures detected.</p>"}
</body>
</html>
"""
        return html

    def _escape(self, value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
