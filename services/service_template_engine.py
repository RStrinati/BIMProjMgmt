import json
import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from constants import schema as S
from database_pool import get_db_connection
from services.template_loader import CANONICAL_TEMPLATE_PATH, load_service_template_sources

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_FILE_PATH = CANONICAL_TEMPLATE_PATH
SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1"}

_TEMPLATE_CACHE: Optional[Dict[str, Any]] = None
_TEMPLATE_MTIME: Optional[float] = None


def _fetch_first_row(cursor) -> Optional[Tuple[Any, ...]]:
    """Advance through nextsets until a row is available (OUTPUT INTO batches)."""
    while True:
        try:
            row = cursor.fetchone()
            return row
        except Exception as exc:
            message = str(exc).lower()
            if "no results" in message:
                if cursor.nextset():
                    continue
                return None
            raise


@dataclass
class TemplateCatalog:
    templates: List[Dict[str, Any]]
    catalog: Dict[str, Any]


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_template(template: Dict[str, Any]) -> str:
    payload = _canonical_json(template)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_template_file() -> Dict[str, Any]:
    global _TEMPLATE_CACHE, _TEMPLATE_MTIME

    template_sources = load_service_template_sources()
    data = template_sources.get("canonical")
    if not data:
        raise ValueError(f"Template file not found: {TEMPLATE_FILE_PATH}")

    mtime = TEMPLATE_FILE_PATH.stat().st_mtime
    if _TEMPLATE_CACHE is not None and _TEMPLATE_MTIME == mtime:
        return _TEMPLATE_CACHE

    # Refresh cache from canonical loader payload to keep a single source of truth.
    data = dict(data)

    schema_version = data.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(f"Unsupported service template schema_version: {schema_version}")

    templates = data.get("templates") or []
    if not isinstance(templates, list):
        raise ValueError("service_templates.json templates must be a list")

    data["templates"] = templates
    _TEMPLATE_CACHE = data
    _TEMPLATE_MTIME = mtime
    return data


def _build_catalog(templates: List[Dict[str, Any]], raw_catalog: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    catalog = dict(raw_catalog or {})
    bill_rules = set(catalog.get("bill_rules") or [])
    unit_types = set(catalog.get("unit_types") or [])
    phases = set(catalog.get("phases") or [])

    for template in templates:
        defaults = template.get("defaults") or {}
        pricing = template.get("pricing") or {}
        if defaults.get("bill_rule"):
            bill_rules.add(defaults["bill_rule"])
        if defaults.get("unit_type"):
            unit_types.add(defaults["unit_type"])
        if defaults.get("phase"):
            phases.add(defaults["phase"])
        if pricing.get("unit_type"):
            unit_types.add(pricing["unit_type"])

        for item in (template.get("items") or []):
            if item.get("bill_rule"):
                bill_rules.add(item["bill_rule"])
            if item.get("unit_type"):
                unit_types.add(item["unit_type"])
            if item.get("phase"):
                phases.add(item["phase"])

        for option in (template.get("options") or []):
            for item in (option.get("items") or []):
                if item.get("bill_rule"):
                    bill_rules.add(item["bill_rule"])
                if item.get("unit_type"):
                    unit_types.add(item["unit_type"])
                if item.get("phase"):
                    phases.add(item["phase"])

    catalog["bill_rules"] = sorted(bill_rules)
    catalog["unit_types"] = sorted(unit_types)
    catalog["phases"] = sorted(phases)
    return catalog


def get_service_template_catalog() -> Dict[str, Any]:
    data = _load_template_file()
    templates: List[Dict[str, Any]] = []

    for template in data.get("templates", []):
        if not isinstance(template, dict):
            continue
        template_id = template.get("template_id")
        name = template.get("name")
        version = template.get("version")
        if not template_id or not name or not version:
            continue

        template_copy = dict(template)
        template_copy["template_hash"] = _hash_template(template_copy)
        templates.append(template_copy)

    catalog = _build_catalog(templates, data.get("catalog"))
    return {"templates": templates, "catalog": catalog}


def _get_template_by_id(template_id: str) -> Dict[str, Any]:
    data = _load_template_file()
    for template in data.get("templates", []):
        if template.get("template_id") == template_id:
            template_copy = dict(template)
            template_copy["template_hash"] = _hash_template(template_copy)
            return template_copy
    raise ValueError(f"Template '{template_id}' not found")


def _resolve_number(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_service_payload(template: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    defaults = template.get("defaults") or {}
    pricing = template.get("pricing") or {}
    payload = {
        "service_code": overrides.get("service_code") or defaults.get("service_code"),
        "service_name": overrides.get("service_name") or defaults.get("service_name"),
        "phase": overrides.get("phase") or defaults.get("phase"),
        "unit_type": overrides.get("unit_type") or pricing.get("unit_type") or defaults.get("unit_type"),
        "unit_qty": overrides.get("unit_qty", pricing.get("unit_qty", defaults.get("unit_qty"))),
        "unit_rate": overrides.get("unit_rate", pricing.get("unit_rate", defaults.get("unit_rate"))),
        "lump_sum_fee": overrides.get("lump_sum_fee", pricing.get("lump_sum_fee", defaults.get("lump_sum_fee"))),
        "agreed_fee": overrides.get("agreed_fee", pricing.get("agreed_fee", defaults.get("agreed_fee"))),
        "bill_rule": overrides.get("bill_rule") or defaults.get("bill_rule"),
        "notes": overrides.get("notes") or defaults.get("notes"),
        "assigned_user_id": overrides.get("assigned_user_id", defaults.get("assigned_user_id")),
        "status": overrides.get("status", defaults.get("status")),
        "progress_pct": overrides.get("progress_pct", defaults.get("progress_pct")),
        "claimed_to_date": overrides.get("claimed_to_date", defaults.get("claimed_to_date")),
    }

    if not payload["service_code"] or not payload["service_name"]:
        raise ValueError("Template defaults must include service_code and service_name")

    unit_qty = _resolve_number(payload.get("unit_qty"))
    unit_rate = _resolve_number(payload.get("unit_rate"))
    lump_sum_fee = _resolve_number(payload.get("lump_sum_fee"))
    agreed_fee = _resolve_number(payload.get("agreed_fee"))

    derive_agreed_fee = bool(pricing.get("derive_agreed_fee"))
    if overrides.get("agreed_fee") is not None:
        agreed_fee = _resolve_number(overrides.get("agreed_fee"))
    elif derive_agreed_fee:
        if unit_qty is not None and unit_rate is not None:
            agreed_fee = unit_qty * unit_rate
        elif payload.get("unit_type") == "lump_sum" and lump_sum_fee is not None:
            agreed_fee = lump_sum_fee

    if agreed_fee is None:
        if payload.get("unit_type") == "lump_sum" and lump_sum_fee is not None:
            agreed_fee = lump_sum_fee
        elif unit_qty is not None and unit_rate is not None:
            agreed_fee = unit_qty * unit_rate
        else:
            agreed_fee = 0.0

    payload["unit_qty"] = unit_qty
    payload["unit_rate"] = unit_rate
    payload["lump_sum_fee"] = lump_sum_fee
    payload["agreed_fee"] = agreed_fee

    return payload


def _resolve_date(base: date, value: Optional[str], offset_days: Optional[int]) -> date:
    if value:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass
    offset = int(offset_days or 0)
    return base + timedelta(days=offset)


def _coerce_date(value: Optional[Any]) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _iter_template_reviews(template: Dict[str, Any], options_enabled: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
    reviews = []
    for entry in template.get("reviews") or []:
        if isinstance(entry, dict):
            reviews.append(("base", entry))
    for option in template.get("options") or []:
        option_id = option.get("option_id")
        if option_id and option_id in options_enabled:
            for entry in option.get("reviews") or []:
                if isinstance(entry, dict):
                    reviews.append((option_id, entry))
    return reviews


def _iter_template_items(template: Dict[str, Any], options_enabled: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
    items = []
    for entry in template.get("items") or []:
        if isinstance(entry, dict):
            items.append(("base", entry))
    for option in template.get("options") or []:
        option_id = option.get("option_id")
        if option_id and option_id in options_enabled:
            for entry in option.get("items") or []:
                if isinstance(entry, dict):
                    items.append((option_id, entry))
    return items


def _derive_template_review_cadence(template: Dict[str, Any], options_enabled: List[str]) -> Tuple[Optional[int], Optional[int]]:
    review_entries = _iter_template_reviews(template, options_enabled)
    if not review_entries:
        return None, None
    interval_candidates = []
    total_count = 0
    for _option_id, review in review_entries:
        count = int(review.get("count") or 1)
        total_count += count
        interval = review.get("interval_days")
        if interval is not None:
            try:
                interval_candidates.append(int(interval))
            except (TypeError, ValueError):
                continue
    interval_days = interval_candidates[0] if interval_candidates else None
    return interval_days, total_count


def _review_generated_key(option_id: str, template_id: str, index: int) -> str:
    if option_id == "base":
        return f"{template_id}:{index}"
    return f"{option_id}:{template_id}:{index}"


def _item_generated_key(option_id: str, template_entry: Dict[str, Any], suffix: Optional[str] = None) -> str:
    template_key = template_entry.get("item_template_id") or template_entry.get("template_id") or "item"
    if option_id == "base":
        return template_key if suffix is None else f"{template_key}:{suffix}"
    return f"{option_id}:{template_key}" if suffix is None else f"{option_id}:{template_key}:{suffix}"


def _review_template_node_key(
    template_id: str,
    template_version: str,
    option_id: str,
    review_template_id: str,
    index: int,
) -> str:
    option_key = option_id or "base"
    return f"{template_id}:{template_version}:{option_key}:{review_template_id}:{index}"


def _item_template_node_key(
    template_id: str,
    template_version: str,
    option_id: str,
    template_entry: Dict[str, Any],
) -> str:
    template_key = template_entry.get("item_template_id") or template_entry.get("template_id") or "item"
    option_key = option_id or "base"
    return f"{template_id}:{template_version}:{option_key}:{template_key}"


def _insert_service(cursor, project_id: int, payload: Dict[str, Any]) -> int:
    columns = [
        S.ProjectServices.PROJECT_ID,
        S.ProjectServices.SERVICE_CODE,
        S.ProjectServices.SERVICE_NAME,
        S.ProjectServices.PHASE,
        S.ProjectServices.UNIT_TYPE,
        S.ProjectServices.UNIT_QTY,
        S.ProjectServices.UNIT_RATE,
        S.ProjectServices.LUMP_SUM_FEE,
        S.ProjectServices.AGREED_FEE,
        S.ProjectServices.BILL_RULE,
        S.ProjectServices.NOTES,
        S.ProjectServices.ASSIGNED_USER_ID,
        S.ProjectServices.START_DATE,
        S.ProjectServices.END_DATE,
        S.ProjectServices.REVIEW_ANCHOR_DATE,
        S.ProjectServices.REVIEW_INTERVAL_DAYS,
        S.ProjectServices.REVIEW_COUNT_PLANNED,
        S.ProjectServices.SOURCE_TEMPLATE_ID,
        S.ProjectServices.SOURCE_TEMPLATE_VERSION,
        S.ProjectServices.SOURCE_TEMPLATE_HASH,
        S.ProjectServices.TEMPLATE_MODE,
    ]
    values = [
        project_id,
        payload.get("service_code"),
        payload.get("service_name"),
        payload.get("phase"),
        payload.get("unit_type"),
        payload.get("unit_qty"),
        payload.get("unit_rate"),
        payload.get("lump_sum_fee"),
        payload.get("agreed_fee"),
        payload.get("bill_rule"),
        payload.get("notes"),
        payload.get("assigned_user_id"),
        payload.get("start_date"),
        payload.get("end_date"),
        payload.get("review_anchor_date"),
        payload.get("review_interval_days"),
        payload.get("review_count_planned"),
        payload.get("source_template_id"),
        payload.get("source_template_version"),
        payload.get("source_template_hash"),
        payload.get("template_mode"),
    ]
    placeholders = ", ".join("?" for _ in values)
    column_list = ", ".join(columns)

    cursor.execute(
        f"""
        DECLARE @Inserted TABLE (id INT);
        INSERT INTO {S.ProjectServices.TABLE} ({column_list})
        OUTPUT INSERTED.{S.ProjectServices.SERVICE_ID} INTO @Inserted(id)
        VALUES ({placeholders});
        SELECT id FROM @Inserted;
        """,
        values,
    )
    row = _fetch_first_row(cursor)
    if not row or row[0] is None:
        raise ValueError("Failed to create service from template")
    return int(row[0])


def _update_service_metadata(cursor, service_id: int, payload: Dict[str, Any]) -> None:
    updates = []
    values = []
    for key, column in [
        ("status", S.ProjectServices.STATUS),
    ]:
        if payload.get(key) is not None:
            updates.append(f"{column} = ?")
            values.append(payload[key])

    if not updates:
        return

    values.append(service_id)
    set_clause = ", ".join(updates)
    cursor.execute(
        f"UPDATE {S.ProjectServices.TABLE} SET {set_clause}, {S.ProjectServices.UPDATED_AT} = GETDATE() WHERE {S.ProjectServices.SERVICE_ID} = ?",
        values,
    )


def _update_service_template_source(cursor, service_id: int, template: Dict[str, Any], template_mode: Optional[str]) -> None:
    cursor.execute(
        f"""
        UPDATE {S.ProjectServices.TABLE}
        SET {S.ProjectServices.SOURCE_TEMPLATE_ID} = ?,
            {S.ProjectServices.SOURCE_TEMPLATE_VERSION} = ?,
            {S.ProjectServices.SOURCE_TEMPLATE_HASH} = ?,
            {S.ProjectServices.TEMPLATE_MODE} = ?
        WHERE {S.ProjectServices.SERVICE_ID} = ?
        """,
        (
            template.get("template_id"),
            template.get("version"),
            template.get("template_hash"),
            template_mode,
            service_id,
        ),
    )


def _fetch_project_start_date(cursor, project_id: int) -> Optional[date]:
    cursor.execute(
        f"""
        SELECT {S.Projects.START_DATE}
        FROM {S.Projects.TABLE}
        WHERE {S.Projects.ID} = ?
        """,
        (project_id,),
    )
    row = cursor.fetchone()
    return _coerce_date(row[0]) if row else None


def _fetch_service_schedule(cursor, service_id: int) -> Dict[str, Any]:
    cursor.execute(
        f"""
        SELECT {S.ProjectServices.START_DATE},
               {S.ProjectServices.REVIEW_ANCHOR_DATE},
               {S.ProjectServices.REVIEW_INTERVAL_DAYS},
               {S.ProjectServices.REVIEW_COUNT_PLANNED}
        FROM {S.ProjectServices.TABLE}
        WHERE {S.ProjectServices.SERVICE_ID} = ?
        """,
        (service_id,),
    )
    row = cursor.fetchone()
    return {
        "start_date": _coerce_date(row[0]) if row else None,
        "review_anchor_date": _coerce_date(row[1]) if row else None,
        "review_interval_days": row[2] if row else None,
        "review_count_planned": row[3] if row else None,
    }

def _upsert_template_binding(
    cursor,
    project_id: int,
    service_id: int,
    template: Dict[str, Any],
    options_enabled: List[str],
    applied_by_user_id: Optional[int],
) -> Dict[str, Any]:
    options_json = json.dumps(sorted(options_enabled), separators=(",", ":"), ensure_ascii=True)
    binding_payload = {
        "template_id": template["template_id"],
        "template_version": template["version"],
        "template_hash": template["template_hash"],
        "options_enabled": options_json,
        "options_enabled_json": options_json,
        "applied_at": datetime.utcnow(),
        "applied_by_user_id": applied_by_user_id,
    }

    cursor.execute(
        f"""
        SELECT {S.ProjectServiceTemplateBindings.BINDING_ID}
        FROM {S.ProjectServiceTemplateBindings.TABLE}
        WHERE {S.ProjectServiceTemplateBindings.SERVICE_ID} = ?
        """,
        (service_id,),
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            f"""
            UPDATE {S.ProjectServiceTemplateBindings.TABLE}
            SET {S.ProjectServiceTemplateBindings.PROJECT_ID} = ?,
                {S.ProjectServiceTemplateBindings.TEMPLATE_ID} = ?,
                {S.ProjectServiceTemplateBindings.TEMPLATE_VERSION} = ?,
                {S.ProjectServiceTemplateBindings.TEMPLATE_HASH} = ?,
                {S.ProjectServiceTemplateBindings.OPTIONS_ENABLED} = ?,
                {S.ProjectServiceTemplateBindings.OPTIONS_ENABLED_JSON} = ?,
                {S.ProjectServiceTemplateBindings.APPLIED_AT} = ?,
                {S.ProjectServiceTemplateBindings.APPLIED_BY_USER_ID} = ?
            WHERE {S.ProjectServiceTemplateBindings.SERVICE_ID} = ?
            """,
            (
                project_id,
                binding_payload["template_id"],
                binding_payload["template_version"],
                binding_payload["template_hash"],
                binding_payload["options_enabled"],
                binding_payload["options_enabled_json"],
                binding_payload["applied_at"],
                binding_payload["applied_by_user_id"],
                service_id,
            ),
        )
        binding_id = int(row[0])
    else:
        cursor.execute(
            f"""
            DECLARE @Inserted TABLE (id INT);
            INSERT INTO {S.ProjectServiceTemplateBindings.TABLE} (
                {S.ProjectServiceTemplateBindings.PROJECT_ID},
                {S.ProjectServiceTemplateBindings.SERVICE_ID},
                {S.ProjectServiceTemplateBindings.TEMPLATE_ID},
                {S.ProjectServiceTemplateBindings.TEMPLATE_VERSION},
                {S.ProjectServiceTemplateBindings.TEMPLATE_HASH},
                {S.ProjectServiceTemplateBindings.OPTIONS_ENABLED},
                {S.ProjectServiceTemplateBindings.OPTIONS_ENABLED_JSON},
                {S.ProjectServiceTemplateBindings.APPLIED_AT},
                {S.ProjectServiceTemplateBindings.APPLIED_BY_USER_ID}
            )
            OUTPUT INSERTED.{S.ProjectServiceTemplateBindings.BINDING_ID} INTO @Inserted(id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            SELECT id FROM @Inserted;
            """,
            (
                project_id,
                service_id,
                binding_payload["template_id"],
                binding_payload["template_version"],
                binding_payload["template_hash"],
                binding_payload["options_enabled"],
                binding_payload["options_enabled_json"],
                binding_payload["applied_at"],
                binding_payload["applied_by_user_id"],
            ),
        )
        row = _fetch_first_row(cursor)
        if not row or row[0] is None:
            raise ValueError("Failed to bind template to service")
        binding_id = int(row[0])

    return {"binding_id": binding_id, **binding_payload}


def _insert_review(
    cursor,
    project_id: int,
    service_id: int,
    template: Dict[str, Any],
    generated_key: str,
    template_node_key: str,
    payload: Dict[str, Any],
) -> int:
    cursor.execute(
        f"""
        DECLARE @Inserted TABLE (id INT);
        INSERT INTO {S.ServiceReviews.TABLE} (
            {S.ServiceReviews.PROJECT_ID},
            {S.ServiceReviews.SERVICE_ID},
            {S.ServiceReviews.CYCLE_NO},
            {S.ServiceReviews.PLANNED_DATE},
            {S.ServiceReviews.DUE_DATE},
            {S.ServiceReviews.DISCIPLINES},
            {S.ServiceReviews.DELIVERABLES},
            {S.ServiceReviews.STATUS},
            {S.ServiceReviews.WEIGHT_FACTOR},
            {S.ServiceReviews.EVIDENCE_LINKS},
            {S.ServiceReviews.INVOICE_REFERENCE},
            {S.ServiceReviews.SOURCE_PHASE},
            {S.ServiceReviews.BILLING_PHASE},
            {S.ServiceReviews.BILLING_RATE},
            {S.ServiceReviews.BILLING_AMOUNT},
            {S.ServiceReviews.IS_BILLED},
            {S.ServiceReviews.GENERATED_FROM_TEMPLATE_ID},
            {S.ServiceReviews.GENERATED_FROM_TEMPLATE_VERSION},
            {S.ServiceReviews.GENERATED_KEY},
            {S.ServiceReviews.TEMPLATE_NODE_KEY},
            {S.ServiceReviews.SORT_ORDER},
            {S.ServiceReviews.ORIGIN},
            {S.ServiceReviews.IS_TEMPLATE_MANAGED},
            {S.ServiceReviews.IS_USER_MODIFIED}
        )
        OUTPUT INSERTED.{S.ServiceReviews.REVIEW_ID} INTO @Inserted(id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        SELECT id FROM @Inserted;
        """,
        (
            project_id,
            service_id,
            payload["cycle_no"],
            payload["planned_date"],
            payload.get("due_date"),
            payload.get("disciplines"),
            payload.get("deliverables"),
            payload.get("status"),
            payload.get("weight_factor"),
            payload.get("evidence_links"),
            payload.get("invoice_reference"),
            payload.get("source_phase"),
            payload.get("billing_phase"),
            payload.get("billing_rate"),
            payload.get("billing_amount"),
            payload.get("is_billed"),
            template["template_id"],
            template["version"],
            generated_key,
            template_node_key,
            payload.get("sort_order"),
            "template_generated",
            1,
            0,
        ),
    )
    row = _fetch_first_row(cursor)
    if not row or row[0] is None:
        raise ValueError("Failed to create service review from template")
    return int(row[0])


def _insert_item(
    cursor,
    project_id: int,
    service_id: int,
    template: Dict[str, Any],
    generated_key: str,
    template_node_key: str,
    payload: Dict[str, Any],
) -> int:
    cursor.execute(
        f"""
        DECLARE @Inserted TABLE (id INT);
        INSERT INTO {S.ServiceItems.TABLE} (
            {S.ServiceItems.PROJECT_ID},
            {S.ServiceItems.SERVICE_ID},
            {S.ServiceItems.ITEM_TYPE},
            {S.ServiceItems.TITLE},
            {S.ServiceItems.DESCRIPTION},
            {S.ServiceItems.PLANNED_DATE},
            {S.ServiceItems.DUE_DATE},
            {S.ServiceItems.STATUS},
            {S.ServiceItems.PRIORITY},
            {S.ServiceItems.NOTES},
            {S.ServiceItems.GENERATED_FROM_TEMPLATE_ID},
            {S.ServiceItems.GENERATED_FROM_TEMPLATE_VERSION},
            {S.ServiceItems.GENERATED_KEY},
            {S.ServiceItems.SORT_ORDER},
            {S.ServiceItems.TEMPLATE_NODE_KEY},
            {S.ServiceItems.ORIGIN},
            {S.ServiceItems.IS_TEMPLATE_MANAGED},
            {S.ServiceItems.IS_USER_MODIFIED},
            {S.ServiceItems.CREATED_AT},
            {S.ServiceItems.UPDATED_AT}
        )
        OUTPUT INSERTED.{S.ServiceItems.ITEM_ID} INTO @Inserted(id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        SELECT id FROM @Inserted;
        """,
        (
            project_id,
            service_id,
            payload["item_type"],
            payload["title"],
            payload.get("description"),
            payload.get("planned_date"),
            payload.get("due_date"),
            payload.get("status"),
            payload.get("priority"),
            payload.get("notes"),
            template["template_id"],
            template["version"],
            generated_key,
            payload.get("sort_order"),
            template_node_key,
            "template_generated",
            1,
            0,
            datetime.utcnow(),
            datetime.utcnow(),
        ),
    )
    row = _fetch_first_row(cursor)
    if not row or row[0] is None:
        raise ValueError("Failed to create service item from template")
    return int(row[0])


def _fetch_existing_reviews(cursor, service_id: int) -> Dict[str, Dict[str, Any]]:
    cursor.execute(
        f"""
        SELECT {S.ServiceReviews.REVIEW_ID},
               {S.ServiceReviews.GENERATED_KEY},
               {S.ServiceReviews.TEMPLATE_NODE_KEY},
               {S.ServiceReviews.STATUS},
               {S.ServiceReviews.DELIVERABLES},
               {S.ServiceReviews.DISCIPLINES},
               {S.ServiceReviews.SORT_ORDER},
               {S.ServiceReviews.ORIGIN},
               {S.ServiceReviews.IS_TEMPLATE_MANAGED},
               {S.ServiceReviews.IS_USER_MODIFIED}
        FROM {S.ServiceReviews.TABLE}
        WHERE {S.ServiceReviews.SERVICE_ID} = ?
          AND ({S.ServiceReviews.GENERATED_KEY} IS NOT NULL
               OR {S.ServiceReviews.TEMPLATE_NODE_KEY} IS NOT NULL)
        """,
        (service_id,),
    )
    records = {}
    for row in cursor.fetchall():
        record = {
            "review_id": int(row[0]),
            "generated_key": row[1],
            "template_node_key": row[2],
            "status": row[3],
            "deliverables": row[4],
            "disciplines": row[5],
            "sort_order": row[6],
            "origin": row[7],
            "is_template_managed": row[8],
            "is_user_modified": row[9],
        }
        if row[2]:
            records[row[2]] = record
        if row[1]:
            records[row[1]] = record
    return records


def _fetch_existing_items(cursor, service_id: int) -> Dict[str, Dict[str, Any]]:
    cursor.execute(
        f"""
        SELECT {S.ServiceItems.ITEM_ID},
               {S.ServiceItems.GENERATED_KEY},
               {S.ServiceItems.TEMPLATE_NODE_KEY},
               {S.ServiceItems.TITLE},
               {S.ServiceItems.DESCRIPTION},
               {S.ServiceItems.STATUS},
               {S.ServiceItems.SORT_ORDER},
               {S.ServiceItems.ORIGIN},
               {S.ServiceItems.IS_TEMPLATE_MANAGED},
               {S.ServiceItems.IS_USER_MODIFIED}
        FROM {S.ServiceItems.TABLE}
        WHERE {S.ServiceItems.SERVICE_ID} = ?
          AND ({S.ServiceItems.GENERATED_KEY} IS NOT NULL
               OR {S.ServiceItems.TEMPLATE_NODE_KEY} IS NOT NULL)
        """,
        (service_id,),
    )
    records = {}
    for row in cursor.fetchall():
        record = {
            "item_id": int(row[0]),
            "generated_key": row[1],
            "template_node_key": row[2],
            "title": row[3],
            "description": row[4],
            "status": row[5],
            "sort_order": row[6],
            "origin": row[7],
            "is_template_managed": row[8],
            "is_user_modified": row[9],
        }
        if row[2]:
            records[row[2]] = record
        if row[1]:
            records[row[1]] = record
    return records


def _is_planned_status(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() == "planned"


def _update_review_fields(
    cursor,
    review_id: int,
    template: Dict[str, Any],
    updates: Dict[str, Any],
) -> None:
    if not updates:
        return
    updates[S.ServiceReviews.GENERATED_FROM_TEMPLATE_ID] = template["template_id"]
    updates[S.ServiceReviews.GENERATED_FROM_TEMPLATE_VERSION] = template["version"]
    updates[S.ServiceReviews.ORIGIN] = "template_generated"
    updates[S.ServiceReviews.IS_TEMPLATE_MANAGED] = 1

    set_clause = ", ".join(f"{column} = ?" for column in updates.keys())
    values = list(updates.values()) + [review_id]
    cursor.execute(
        f"UPDATE {S.ServiceReviews.TABLE} SET {set_clause} WHERE {S.ServiceReviews.REVIEW_ID} = ?",
        values,
    )


def _update_item_fields(
    cursor,
    item_id: int,
    template: Dict[str, Any],
    updates: Dict[str, Any],
) -> None:
    if not updates:
        return
    updates[S.ServiceItems.GENERATED_FROM_TEMPLATE_ID] = template["template_id"]
    updates[S.ServiceItems.GENERATED_FROM_TEMPLATE_VERSION] = template["version"]
    updates[S.ServiceItems.ORIGIN] = "template_generated"
    updates[S.ServiceItems.IS_TEMPLATE_MANAGED] = 1

    set_clause = ", ".join(f"{column} = ?" for column in updates.keys())
    values = list(updates.values()) + [item_id]
    cursor.execute(
        f"UPDATE {S.ServiceItems.TABLE} SET {set_clause} WHERE {S.ServiceItems.ITEM_ID} = ?",
        values,
    )


def _sync_reviews_and_items(
    cursor,
    project_id: int,
    service_id: int,
    template: Dict[str, Any],
    options_enabled: List[str],
    mode: str,
    dry_run: bool,
    base_date: date,
) -> Dict[str, List[Dict[str, Any]]]:
    existing_reviews = _fetch_existing_reviews(cursor, service_id)
    existing_items = _fetch_existing_items(cursor, service_id)

    added_reviews: List[Dict[str, Any]] = []
    updated_reviews: List[Dict[str, Any]] = []
    skipped_reviews: List[Dict[str, Any]] = []
    added_items: List[Dict[str, Any]] = []
    updated_items: List[Dict[str, Any]] = []
    skipped_items: List[Dict[str, Any]] = []

    review_entries = _iter_template_reviews(template, options_enabled)
    for review_index, (option_id, review) in enumerate(review_entries, start=1):
        review_template_id = review.get("review_template_id")
        if not review_template_id:
            continue
        count = int(review.get("count") or 1)
        interval_days = int(review.get("interval_days") or 7)
        start_offset = int(review.get("planned_offset_days") or 0)
        for index in range(1, count + 1):
            generated_key = _review_generated_key(option_id, review_template_id, index)
            template_node_key = _review_template_node_key(
                template["template_id"],
                template["version"],
                option_id,
                review_template_id,
                index,
            )
            planned_date = base_date + timedelta(days=start_offset + (index - 1) * interval_days)
            due_offset = review.get("due_offset_days")
            due_date = planned_date + timedelta(days=int(due_offset or 0)) if due_offset is not None else None
            payload = {
                "cycle_no": index,
                "planned_date": planned_date,
                "due_date": due_date,
                "disciplines": review.get("disciplines"),
                "deliverables": review.get("deliverables"),
                "status": review.get("status") or "planned",
                "weight_factor": _resolve_number(review.get("weight_factor")) or 1.0,
                "evidence_links": review.get("evidence_links"),
                "invoice_reference": review.get("invoice_reference"),
                "source_phase": review.get("source_phase"),
                "billing_phase": review.get("billing_phase"),
                "billing_rate": _resolve_number(review.get("billing_rate")),
                "billing_amount": _resolve_number(review.get("billing_amount")),
                "is_billed": 1 if str(review.get("status") or "").lower() == "completed" else 0,
                "sort_order": review_index,
            }

            existing = existing_reviews.get(template_node_key) or existing_reviews.get(generated_key)
            if not existing:
                if not dry_run:
                    review_id = _insert_review(
                        cursor,
                        project_id,
                        service_id,
                        template,
                        generated_key,
                        template_node_key,
                        payload,
                    )
                else:
                    review_id = None
                added_reviews.append({"template_node_key": template_node_key, "review_id": review_id})
                continue

            if mode == "sync_missing_only":
                skipped_reviews.append({"template_node_key": template_node_key, "review_id": existing["review_id"]})
                continue

            if (
                not existing.get("is_template_managed")
                or existing.get("is_user_modified")
                or not _is_planned_status(existing.get("status"))
            ):
                skipped_reviews.append({"template_node_key": template_node_key, "review_id": existing["review_id"]})
                continue

            updates: Dict[str, Any] = {}
            if template_node_key != existing.get("template_node_key"):
                updates[S.ServiceReviews.TEMPLATE_NODE_KEY] = template_node_key
            if payload.get("deliverables") is not None and payload.get("deliverables") != existing.get("deliverables"):
                updates[S.ServiceReviews.DELIVERABLES] = payload.get("deliverables")
            if payload.get("disciplines") is not None and payload.get("disciplines") != existing.get("disciplines"):
                updates[S.ServiceReviews.DISCIPLINES] = payload.get("disciplines")
            desired_status = payload.get("status")
            if desired_status and _is_planned_status(existing.get("status")) and desired_status != existing.get("status"):
                updates[S.ServiceReviews.STATUS] = desired_status
            if payload.get("sort_order") is not None and payload.get("sort_order") != existing.get("sort_order"):
                updates[S.ServiceReviews.SORT_ORDER] = payload.get("sort_order")

            if updates:
                if not dry_run:
                    _update_review_fields(cursor, existing["review_id"], template, updates)
                updated_reviews.append({"template_node_key": template_node_key, "review_id": existing["review_id"]})
            else:
                skipped_reviews.append({"template_node_key": template_node_key, "review_id": existing["review_id"]})

    item_entries = _iter_template_items(template, options_enabled)
    for item_index, (option_id, item) in enumerate(item_entries, start=1):
        item_template_id = item.get("item_template_id") or item.get("template_id")
        if not item_template_id:
            continue
        generated_key = _item_generated_key(option_id, item)
        template_node_key = _item_template_node_key(
            template["template_id"],
            template["version"],
            option_id,
            item,
        )
        planned_date = _resolve_date(base_date, item.get("planned_date"), item.get("planned_offset_days"))
        due_date = None
        if item.get("due_date") or item.get("due_offset_days") is not None:
            due_date = _resolve_date(planned_date, item.get("due_date"), item.get("due_offset_days"))
        payload = {
            "item_type": item.get("item_type") or "deliverable",
            "title": item.get("title") or item.get("name") or "Untitled",
            "description": item.get("description"),
            "planned_date": planned_date,
            "due_date": due_date,
            "status": item.get("status") or "planned",
            "priority": item.get("priority") or "medium",
            "notes": item.get("notes"),
            "sort_order": item.get("sort_order") if item.get("sort_order") is not None else item_index,
        }

        existing = existing_items.get(template_node_key) or existing_items.get(generated_key)
        if not existing:
            if not dry_run:
                item_id = _insert_item(cursor, project_id, service_id, template, generated_key, template_node_key, payload)
            else:
                item_id = None
            added_items.append({"template_node_key": template_node_key, "item_id": item_id})
            continue

        if mode == "sync_missing_only":
            skipped_items.append({"template_node_key": template_node_key, "item_id": existing["item_id"]})
            continue

        if (
            not existing.get("is_template_managed")
            or existing.get("is_user_modified")
            or not _is_planned_status(existing.get("status"))
        ):
            skipped_items.append({"template_node_key": template_node_key, "item_id": existing["item_id"]})
            continue

        updates = {}
        if template_node_key != existing.get("template_node_key"):
            updates[S.ServiceItems.TEMPLATE_NODE_KEY] = template_node_key
        if payload.get("title") and payload.get("title") != existing.get("title"):
            updates[S.ServiceItems.TITLE] = payload.get("title")
        if payload.get("description") is not None and payload.get("description") != existing.get("description"):
            updates[S.ServiceItems.DESCRIPTION] = payload.get("description")
        desired_status = payload.get("status")
        if desired_status and _is_planned_status(existing.get("status")) and desired_status != existing.get("status"):
            updates[S.ServiceItems.STATUS] = desired_status
        if payload.get("sort_order") is not None and payload.get("sort_order") != existing.get("sort_order"):
            updates[S.ServiceItems.SORT_ORDER] = payload.get("sort_order")

        if updates:
            if not dry_run:
                _update_item_fields(cursor, existing["item_id"], template, updates)
            updated_items.append({"template_node_key": template_node_key, "item_id": existing["item_id"]})
        else:
            skipped_items.append({"template_node_key": template_node_key, "item_id": existing["item_id"]})

    return {
        "added_reviews": added_reviews,
        "updated_reviews": updated_reviews,
        "skipped_reviews": skipped_reviews,
        "added_items": added_items,
        "updated_items": updated_items,
        "skipped_items": skipped_items,
    }

def _generate_reviews_and_items(
    cursor,
    project_id: int,
    service_id: int,
    template: Dict[str, Any],
    options_enabled: List[str],
    mode: str,
    dry_run: bool,
    base_date: date,
) -> Dict[str, List[Dict[str, Any]]]:
    return _sync_reviews_and_items(
        cursor=cursor,
        project_id=project_id,
        service_id=service_id,
        template=template,
        options_enabled=options_enabled,
        mode=mode,
        dry_run=dry_run,
        base_date=base_date,
    )


def create_service_from_template(
    project_id: int,
    template_id: str,
    options_enabled: List[str],
    overrides: Dict[str, Any],
    applied_by_user_id: Optional[int] = None,
) -> Dict[str, Any]:
    template = _get_template_by_id(template_id)
    payload = _resolve_service_payload(template, overrides or {})
    options_enabled = [str(option) for option in options_enabled or []]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        start_date = _coerce_date(overrides.get("start_date"))
        if not start_date:
            start_date = _fetch_project_start_date(cursor, project_id) or date.today()
        review_anchor_date = _coerce_date(overrides.get("review_anchor_date")) or start_date
        review_interval_days, review_count_planned = _derive_template_review_cadence(template, options_enabled)
        if overrides.get("review_interval_days") is not None:
            try:
                review_interval_days = int(overrides.get("review_interval_days"))
            except (TypeError, ValueError):
                review_interval_days = review_interval_days
        if overrides.get("review_count_planned") is not None:
            try:
                review_count_planned = int(overrides.get("review_count_planned"))
            except (TypeError, ValueError):
                review_count_planned = review_count_planned

        payload.update({
            "start_date": start_date,
            "review_anchor_date": review_anchor_date,
            "review_interval_days": review_interval_days,
            "review_count_planned": review_count_planned,
            "source_template_id": template.get("template_id"),
            "source_template_version": template.get("version"),
            "source_template_hash": template.get("template_hash"),
            "template_mode": overrides.get("template_mode") or "managed",
        })

        service_id = _insert_service(cursor, project_id, payload)
        _update_service_metadata(cursor, service_id, payload)
        _update_service_template_source(cursor, service_id, template, payload.get("template_mode"))
        binding = _upsert_template_binding(
            cursor,
            project_id=project_id,
            service_id=service_id,
            template=template,
            options_enabled=options_enabled,
            applied_by_user_id=applied_by_user_id,
        )
        generated = _generate_reviews_and_items(
            cursor,
            project_id,
            service_id,
            template,
            options_enabled,
            mode="sync_missing_only",
            dry_run=False,
            base_date=review_anchor_date,
        )
        conn.commit()

    return {
        "service_id": service_id,
        "project_id": project_id,
        "template": {
            "template_id": template["template_id"],
            "name": template.get("name"),
            "version": template.get("version"),
            "template_hash": template.get("template_hash"),
        },
        "binding": binding,
        "generated": {
            "review_ids": [entry["review_id"] for entry in generated["added_reviews"]],
            "item_ids": [entry["item_id"] for entry in generated["added_items"]],
            "review_count": len(generated["added_reviews"]),
            "item_count": len(generated["added_items"]),
        },
    }


def apply_template_to_service(
    project_id: int,
    service_id: int,
    template_id: str,
    options_enabled: List[str],
    overrides: Dict[str, Any],
    applied_by_user_id: Optional[int] = None,
    mode: str = "sync_and_update_managed",
    dry_run: bool = False,
) -> Dict[str, Any]:
    template = _get_template_by_id(template_id)
    payload = _resolve_service_payload(template, overrides or {})
    if mode not in {"sync_missing_only", "sync_and_update_managed"}:
        mode = "sync_and_update_managed"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.ProjectServices.SERVICE_ID}
            FROM {S.ProjectServices.TABLE}
            WHERE {S.ProjectServices.SERVICE_ID} = ?
              AND {S.ProjectServices.PROJECT_ID} = ?
            """,
            (service_id, project_id),
        )
        if not cursor.fetchone():
            raise ValueError("Service not found for this project")

        cursor.execute(
            f"""
            SELECT {S.ProjectServiceTemplateBindings.OPTIONS_ENABLED_JSON},
                   {S.ProjectServiceTemplateBindings.OPTIONS_ENABLED}
            FROM {S.ProjectServiceTemplateBindings.TABLE}
            WHERE {S.ProjectServiceTemplateBindings.SERVICE_ID} = ?
            """,
            (service_id,),
        )
        binding_options_row = cursor.fetchone()
        if options_enabled:
            resolved_options = [str(option) for option in options_enabled or []]
        elif binding_options_row:
            raw_options = binding_options_row[0] or binding_options_row[1]
            if raw_options:
                try:
                    resolved_options = json.loads(raw_options)
                except json.JSONDecodeError:
                    resolved_options = []
            else:
                resolved_options = []
        else:
            resolved_options = []

        schedule = _fetch_service_schedule(cursor, service_id)
        base_date = _coerce_date(overrides.get("review_anchor_date")) or schedule.get("review_anchor_date") or schedule.get("start_date")
        if not base_date:
            base_date = _fetch_project_start_date(cursor, project_id) or date.today()

        _update_service_metadata(cursor, service_id, payload)
        _update_service_template_source(cursor, service_id, template, overrides.get("template_mode") or "managed")
        binding = _upsert_template_binding(
            cursor,
            project_id=project_id,
            service_id=service_id,
            template=template,
            options_enabled=resolved_options,
            applied_by_user_id=applied_by_user_id,
        )
        generated = _generate_reviews_and_items(
            cursor,
            project_id,
            service_id,
            template,
            resolved_options,
            mode=mode,
            dry_run=dry_run,
            base_date=base_date,
        )
        if not dry_run:
            conn.commit()

    return {
        "service_id": service_id,
        "project_id": project_id,
        "template": {
            "template_id": template["template_id"],
            "name": template.get("name"),
            "version": template.get("version"),
            "template_hash": template.get("template_hash"),
        },
        "binding": binding,
        "generated": {
            "review_ids": [entry.get("review_id") for entry in generated["added_reviews"]],
            "item_ids": [entry.get("item_id") for entry in generated["added_items"]],
            "review_count": len(generated["added_reviews"]),
            "item_count": len(generated["added_items"]),
        },
        "added_reviews": generated["added_reviews"],
        "updated_reviews": generated["updated_reviews"],
        "skipped_reviews": generated["skipped_reviews"],
        "added_items": generated["added_items"],
        "updated_items": generated["updated_items"],
        "skipped_items": generated["skipped_items"],
        "dry_run": dry_run,
        "mode": mode,
    }


def get_generated_structure(project_id: int, service_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.ProjectServices.SERVICE_ID}, {S.ProjectServices.PROJECT_ID},
                   {S.ProjectServices.SERVICE_CODE}, {S.ProjectServices.SERVICE_NAME},
                   {S.ProjectServices.PHASE}, {S.ProjectServices.UNIT_TYPE},
                   {S.ProjectServices.UNIT_QTY}, {S.ProjectServices.UNIT_RATE},
                   {S.ProjectServices.LUMP_SUM_FEE}, {S.ProjectServices.AGREED_FEE},
                   {S.ProjectServices.BILL_RULE}, {S.ProjectServices.NOTES},
                   {S.ProjectServices.STATUS}, {S.ProjectServices.PROGRESS_PCT},
                   {S.ProjectServices.CLAIMED_TO_DATE}, {S.ProjectServices.ASSIGNED_USER_ID},
                   {S.ProjectServices.START_DATE}, {S.ProjectServices.END_DATE},
                   {S.ProjectServices.REVIEW_ANCHOR_DATE}, {S.ProjectServices.REVIEW_INTERVAL_DAYS},
                   {S.ProjectServices.REVIEW_COUNT_PLANNED},
                   {S.ProjectServices.SOURCE_TEMPLATE_ID},
                   {S.ProjectServices.SOURCE_TEMPLATE_VERSION},
                   {S.ProjectServices.SOURCE_TEMPLATE_HASH},
                   {S.ProjectServices.TEMPLATE_MODE}
            FROM {S.ProjectServices.TABLE}
            WHERE {S.ProjectServices.SERVICE_ID} = ?
              AND {S.ProjectServices.PROJECT_ID} = ?
            """,
            (service_id, project_id),
        )
        service_row = cursor.fetchone()
        if not service_row:
            return None

        service = {
            "service_id": service_row[0],
            "project_id": service_row[1],
            "service_code": service_row[2],
            "service_name": service_row[3],
            "phase": service_row[4],
            "unit_type": service_row[5],
            "unit_qty": service_row[6],
            "unit_rate": service_row[7],
            "lump_sum_fee": service_row[8],
            "agreed_fee": service_row[9],
            "bill_rule": service_row[10],
            "notes": service_row[11],
            "status": service_row[12],
            "progress_pct": service_row[13],
            "claimed_to_date": service_row[14],
            "assigned_user_id": service_row[15],
            "start_date": service_row[16],
            "end_date": service_row[17],
            "review_anchor_date": service_row[18],
            "review_interval_days": service_row[19],
            "review_count_planned": service_row[20],
            "source_template_id": service_row[21],
            "source_template_version": service_row[22],
            "source_template_hash": service_row[23],
            "template_mode": service_row[24],
        }

        cursor.execute(
            f"""
            SELECT {S.ProjectServiceTemplateBindings.BINDING_ID},
                   {S.ProjectServiceTemplateBindings.TEMPLATE_ID},
                   {S.ProjectServiceTemplateBindings.TEMPLATE_VERSION},
                   {S.ProjectServiceTemplateBindings.TEMPLATE_HASH},
                   {S.ProjectServiceTemplateBindings.OPTIONS_ENABLED_JSON},
                   {S.ProjectServiceTemplateBindings.OPTIONS_ENABLED},
                   {S.ProjectServiceTemplateBindings.APPLIED_AT},
                   {S.ProjectServiceTemplateBindings.APPLIED_BY_USER_ID}
            FROM {S.ProjectServiceTemplateBindings.TABLE}
            WHERE {S.ProjectServiceTemplateBindings.SERVICE_ID} = ?
            """,
            (service_id,),
        )
        binding_row = cursor.fetchone()
        binding = None
        template = None
        options_enabled: List[str] = []

        if binding_row:
            options_raw = binding_row[4] or binding_row[5]
            if options_raw:
                try:
                    options_enabled = json.loads(options_raw)
                except json.JSONDecodeError:
                    options_enabled = []
            binding = {
                "binding_id": binding_row[0],
                "template_id": binding_row[1],
                "template_version": binding_row[2],
                "template_hash": binding_row[3],
                "options_enabled": options_enabled,
                "applied_at": binding_row[6],
                "applied_by_user_id": binding_row[7],
            }
            try:
                template = _get_template_by_id(binding_row[1])
            except ValueError:
                template = None

        cursor.execute(
            f"""
            SELECT {S.ServiceReviews.REVIEW_ID}, {S.ServiceReviews.GENERATED_KEY},
                   {S.ServiceReviews.TEMPLATE_NODE_KEY},
                   {S.ServiceReviews.CYCLE_NO}, {S.ServiceReviews.PLANNED_DATE},
                   {S.ServiceReviews.STATUS}, {S.ServiceReviews.IS_TEMPLATE_MANAGED},
                   {S.ServiceReviews.IS_USER_MODIFIED}
            FROM {S.ServiceReviews.TABLE}
            WHERE {S.ServiceReviews.SERVICE_ID} = ?
              AND ({S.ServiceReviews.GENERATED_KEY} IS NOT NULL
                   OR {S.ServiceReviews.TEMPLATE_NODE_KEY} IS NOT NULL)
            ORDER BY {S.ServiceReviews.CYCLE_NO}
            """,
            (service_id,),
        )
        reviews = [
            {
                "review_id": row[0],
                "generated_key": row[1],
                "template_node_key": row[2],
                "cycle_no": row[3],
                "planned_date": row[4],
                "status": row[5],
                "is_template_managed": bool(row[6]) if row[6] is not None else None,
                "is_user_modified": bool(row[7]) if row[7] is not None else False,
            }
            for row in cursor.fetchall()
        ]

        cursor.execute(
            f"""
            SELECT {S.ServiceItems.ITEM_ID}, {S.ServiceItems.GENERATED_KEY},
                   {S.ServiceItems.TEMPLATE_NODE_KEY},
                   {S.ServiceItems.TITLE}, {S.ServiceItems.ITEM_TYPE},
                   {S.ServiceItems.STATUS}, {S.ServiceItems.IS_TEMPLATE_MANAGED},
                   {S.ServiceItems.IS_USER_MODIFIED}
            FROM {S.ServiceItems.TABLE}
            WHERE {S.ServiceItems.SERVICE_ID} = ?
              AND ({S.ServiceItems.GENERATED_KEY} IS NOT NULL
                   OR {S.ServiceItems.TEMPLATE_NODE_KEY} IS NOT NULL)
            ORDER BY {S.ServiceItems.CREATED_AT}
            """,
            (service_id,),
        )
        items = [
            {
                "item_id": row[0],
                "generated_key": row[1],
                "template_node_key": row[2],
                "title": row[3],
                "item_type": row[4],
                "status": row[5],
                "is_template_managed": bool(row[6]) if row[6] is not None else None,
                "is_user_modified": bool(row[7]) if row[7] is not None else False,
            }
            for row in cursor.fetchall()
        ]

    return {
        "service": service,
        "binding": binding,
        "template": template,
        "options_enabled": options_enabled,
        "generated_reviews": reviews,
        "generated_items": items,
    }
