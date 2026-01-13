"""
Warehouse ETL pipeline orchestrating staging, dimension, fact and mart loads.

The pipeline is designed to be idempotent and incremental:
    * Staging loads pull from operational databases using high-water marks.
    * Dimensions implement SCD Type-2 with hash-based change detection.
    * Facts derive metrics aligned with business logic requirements.
    * Control tables capture run metadata and data-quality findings.
"""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import pyodbc  # type: ignore

from config import Config
from database_pool import get_db_connection
from constants import schema as S

logger = logging.getLogger(__name__)


@dataclass
class DataQualityCheck:
    """Represents a configurable data-quality validation."""

    name: str
    severity: str
    query: str
    expected_result: Callable[[Sequence[pyodbc.Row]], bool]
    failure_message: Callable[[Sequence[pyodbc.Row]], str]
    params: Optional[Tuple[Any, ...]] = None
    details_on_pass: bool = False


class WarehousePipeline:
    """Coordinates extraction, transformation, and load activities."""

    def __init__(
        self,
        source_db: str = Config.PROJECT_MGMT_DB,
        warehouse_db: str = Config.WAREHOUSE_DB,
        pipeline_name: str = "warehouse_full_load",
    ) -> None:
        self.source_db = source_db
        self.warehouse_db = warehouse_db
        self.pipeline_name = pipeline_name
        self._current_run_id: Optional[int] = None
        self._issue_import_run_id: Optional[int] = None
        self._issue_source_watermark: Optional[datetime] = None
        self._issue_snapshot_date: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Control helpers
    # ------------------------------------------------------------------
    def _start_run(self) -> None:
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ctl.etl_run (pipeline_name, status)
                OUTPUT INSERTED.run_id
                VALUES (?, ?)
                """,
                (self.pipeline_name, "running"),
            )
            self._current_run_id = cursor.fetchone()[0]
            conn.commit()
        logger.info("Started ETL run id=%s", self._current_run_id)

    def _complete_run(self, status: str, message: Optional[str] = None) -> None:
        if self._current_run_id is None:
            return
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE ctl.etl_run
                SET status = ?, completed_at = SYSUTCDATETIME(), message = ?
                WHERE run_id = ?
                """,
                (status, message, self._current_run_id),
            )
            conn.commit()
        logger.info("Completed ETL run id=%s with status=%s", self._current_run_id, status)

    def _start_issue_import_run(self, run_type: str = "warehouse_full_load") -> None:
        """Start an issue import run for dashboard gating."""
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO dbo.{S.IssueImportRuns.TABLE} (
                    {S.IssueImportRuns.SOURCE_SYSTEM},
                    {S.IssueImportRuns.RUN_TYPE},
                    {S.IssueImportRuns.STATUS},
                    {S.IssueImportRuns.NOTES}
                )
                OUTPUT INSERTED.{S.IssueImportRuns.IMPORT_RUN_ID}
                VALUES (?, ?, ?, ?)
                """,
                ("combined", run_type, "running", self.pipeline_name),
            )
            self._issue_import_run_id = cursor.fetchone()[0]
            conn.commit()
        logger.info("Started issue import run id=%s", self._issue_import_run_id)

    def _complete_issue_import_run(
        self,
        status: str,
        message: Optional[str] = None,
        row_count: Optional[int] = None,
    ) -> None:
        if self._issue_import_run_id is None:
            return
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE dbo.{S.IssueImportRuns.TABLE}
                SET {S.IssueImportRuns.STATUS} = ?,
                    {S.IssueImportRuns.COMPLETED_AT} = SYSUTCDATETIME(),
                    {S.IssueImportRuns.SOURCE_WATERMARK} = ?,
                    {S.IssueImportRuns.ROW_COUNT} = ?,
                    {S.IssueImportRuns.NOTES} = ?
                WHERE {S.IssueImportRuns.IMPORT_RUN_ID} = ?
                """,
                (
                    status,
                    self._issue_source_watermark,
                    row_count,
                    message,
                    self._issue_import_run_id,
                ),
            )
            conn.commit()
        logger.info("Completed issue import run id=%s status=%s", self._issue_import_run_id, status)

    def _get_watermark(self, process_name: str, source_object: str) -> datetime:
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT watermark_value FROM ctl.watermark
                WHERE process_name = ? AND source_object = ?
                """,
                (process_name, source_object),
            )
            row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        return datetime(1900, 1, 1)

    def _set_watermark(
        self,
        process_name: str,
        source_object: str,
        watermark_value: datetime,
        row_count: int,
    ) -> None:
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                MERGE ctl.watermark AS target
                USING (SELECT ? AS process_name, ? AS source_object) AS src
                    ON target.process_name = src.process_name
                   AND target.source_object = src.source_object
                WHEN MATCHED THEN
                    UPDATE SET watermark_value = ?, row_count = ?, updated_at = SYSUTCDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (process_name, source_object, watermark_value, row_count)
                    VALUES (?, ?, ?, ?);
                """,
                (
                    process_name,
                    source_object,
                    watermark_value,
                    row_count,
                    process_name,
                    source_object,
                    watermark_value,
                    row_count,
                ),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Staging loaders
    # ------------------------------------------------------------------
    def load_staging_issues(self) -> int:
        """Incrementally load issues view into staging."""
        process = "stg_issues"
        source_object = "vw_ProjectManagement_AllIssues"
        watermark = self._get_watermark(process, source_object)
        logger.info("Loading staging issues (watermark=%s)", watermark.isoformat())

        select_query = """
            WITH source_issues AS (
                SELECT
                    pm.source,
                    CAST(pm.issue_id AS NVARCHAR(255)) AS issue_id,
                    CAST(pm.source_issue_id AS NVARCHAR(255)) AS source_issue_id,
                    pm.project_name,
                    CAST(pm.project_id AS NVARCHAR(255)) AS project_id_raw,
                    CAST(pm.source_project_id AS NVARCHAR(255)) AS source_project_id,
                    pm.status,
                    pm.status_normalized,
                    pm.priority,
                    pm.source_updated_at,
                    pm.phase,
                    pm.building_level,
                    pm.clash_level,
                    pm.custom_attributes_json,
                    pm.is_deleted,
                    pm.project_mapped,
                    ve.Priority AS acc_priority,
                    ve.Discipline AS acc_discipline,
                    ve.location_name AS acc_location_name,
                    ve.root_location,
                    ve.building_name,
                    ve.level_name,
                    rv.tags_json AS revizto_tags_json,
                    rv.position_properties_decoded AS revizto_position_properties,
                    prio_map.normalized_priority AS mapped_priority,
                    loc_map.location_root AS mapped_location_root,
                    loc_map.location_building AS mapped_location_building,
                    loc_map.location_level AS mapped_location_level,
                    pm.title,
                    pm.assignee,
                    pm.author,
                    pm.created_at,
                    pm.closed_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY pm.source, pm.issue_id
                        ORDER BY
                            CASE WHEN pm.created_at IS NOT NULL THEN pm.created_at ELSE '1900-01-01' END DESC,
                            CASE WHEN pm.closed_at IS NOT NULL THEN pm.closed_at ELSE '1900-01-01' END DESC
                    ) AS rn
                FROM vw_ProjectManagement_AllIssues pm
                LEFT JOIN acc_data_schema.dbo.vw_issues_expanded ve
                    ON CAST(ve.display_id AS NVARCHAR(255)) = pm.issue_id
                   AND CAST(ve.project_id AS NVARCHAR(255)) = pm.project_id
                   AND pm.source = 'ACC'
                LEFT JOIN ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed rv
                    ON CAST(rv.issue_number AS NVARCHAR(255)) = pm.issue_id
                   AND pm.source = 'Revizto'
                OUTER APPLY (
                    SELECT TOP (1) m.normalized_priority
                    FROM dbo.issue_priority_map m
                    WHERE m.source_system = pm.source
                      AND m.raw_priority = COALESCE(ve.Priority, pm.priority)
                      AND (m.project_id = CAST(pm.project_id AS NVARCHAR(100)) OR m.project_id IS NULL)
                    ORDER BY CASE WHEN m.project_id = CAST(pm.project_id AS NVARCHAR(100)) THEN 0 ELSE 1 END,
                             CASE WHEN m.is_default = 1 THEN 0 ELSE 1 END
                ) prio_map
                OUTER APPLY (
                    SELECT TOP (1) m.location_root, m.location_building, m.location_level
                    FROM dbo.issue_location_map m
                    WHERE m.source_system = pm.source
                      AND m.raw_location = COALESCE(
                          ve.location_name,
                          ve.root_location,
                          rv.position_properties_decoded,
                          JSON_VALUE(rv.tags_json, '$[0]')
                      )
                      AND (m.project_id = CAST(pm.project_id AS NVARCHAR(100)) OR m.project_id IS NULL)
                    ORDER BY CASE WHEN m.project_id = CAST(pm.project_id AS NVARCHAR(100)) THEN 0 ELSE 1 END,
                             CASE WHEN m.is_default = 1 THEN 0 ELSE 1 END
                ) loc_map
                WHERE
                    pm.source_updated_at IS NOT NULL
                    AND pm.source_updated_at > ?
            )
            SELECT
                source,
                issue_id,
                source_issue_id,
                project_name,
                project_id_raw,
                source_project_id,
                status,
                status_normalized,
                priority,
                source_updated_at,
                phase,
                building_level,
                clash_level,
                custom_attributes_json,
                is_deleted,
                project_mapped,
                acc_priority,
                acc_discipline,
                acc_location_name,
                root_location,
                building_name,
                level_name,
                revizto_tags_json,
                revizto_position_properties,
                mapped_priority,
                mapped_location_root,
                mapped_location_building,
                mapped_location_level,
                title,
                assignee,
                author,
                created_at,
                closed_at
            FROM source_issues
            WHERE rn = 1
        """

        rows = self._fetch_source_rows(select_query, watermark)
        if not rows:
            logger.info("No new issue rows to load.")
            return 0

        insert_sql = """
            INSERT INTO stg.issues (
                source_system, issue_id, source_issue_id, project_name, project_id_raw, source_project_id,
                status, status_normalized, priority,
                priority_normalized, title, description, assignee, author, created_at, closed_at,
                last_activity_date, due_date, discipline, category_primary,
                category_secondary, location_raw, location_root, location_building, location_level,
                phase, building_level, clash_level, custom_attributes_json,
                is_deleted, project_mapped,
                record_source, source_load_ts
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, SYSUTCDATETIME()
            )
        """
        record_source = "ProjectManagement"
        insert_rows = [
            (
                row.source,
                row.issue_id,
                row.source_issue_id,
                row.project_name,
                row.project_id_raw,
                row.source_project_id,
                row.status,
                row.status_normalized,
                row.priority,
                row.mapped_priority or self._normalize_priority(row.acc_priority or row.priority),
                row.title,
                getattr(row, "description", None),
                row.assignee,
                row.author,
                row.created_at,
                row.closed_at,
                None,
                getattr(row, "due_date", None),
                getattr(row, "acc_discipline", None)
                or (row.assignee if row.source == "Revizto" else None),
                getattr(row, "primary_category", None),
                getattr(row, "secondary_category", None),
                getattr(row, "acc_location_name", None)
                or getattr(row, "root_location", None)
                or getattr(row, "revizto_position_properties", None)
                or self._extract_revizto_tag(row.revizto_tags_json),
                getattr(row, "mapped_location_root", None)
                or getattr(row, "root_location", None)
                or self._extract_revizto_tag(row.revizto_tags_json),
                getattr(row, "mapped_location_building", None)
                or getattr(row, "building_name", None),
                getattr(row, "mapped_location_level", None)
                or getattr(row, "level_name", None),
                getattr(row, "phase", None),
                getattr(row, "building_level", None),
                getattr(row, "clash_level", None),
                getattr(row, "custom_attributes_json", None),
                getattr(row, "is_deleted", None),
                getattr(row, "project_mapped", None),
                record_source,
            )
            for row in rows
        ]

        self._bulk_insert(insert_sql, insert_rows)

        latest = max((row.source_updated_at for row in rows if row.source_updated_at is not None), default=watermark)
        self._set_watermark(process, source_object, latest, len(rows))
        self._issue_source_watermark = latest
        logger.info("Loaded %s issue rows into staging.", len(rows))
        return len(rows)

    def load_staging_processed_issues(self) -> int:
        process = "stg_processed_issues"
        source_object = "ProcessedIssues"
        watermark = self._get_watermark(process, source_object)
        logger.info("Loading processed issues (watermark=%s)", watermark.isoformat())

        select_query = """
            SELECT
                source,
                source_issue_id,
                project_id,
                urgency_score,
                complexity_score,
                sentiment_score,
                categorization_confidence,
                discipline_category_id,
                primary_category_id,
                secondary_category_id,
                resolution_days,
                is_recurring,
                recurring_cluster_id,
                comment_count,
                processed_at,
                processing_version,
                extracted_keywords
            FROM ProcessedIssues
            WHERE processed_at IS NOT NULL AND processed_at > ?
        """

        rows = self._fetch_source_rows(select_query, watermark)
        if not rows:
            logger.info("No new processed issue rows to stage.")
            return 0

        insert_sql = """
            INSERT INTO stg.processed_issues (
                source_system, issue_id, project_id, urgency_score, complexity_score,
                sentiment_score, categorization_confidence, discipline_category_id,
                primary_category_id, secondary_category_id, resolution_days,
                is_recurring, recurring_cluster_id, comment_count, processed_at,
                processing_version, extracted_keywords_json, record_source, source_load_ts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
        """
        record_source = "ProcessedIssues"
        insert_rows = [
            (
                row.source,
                row.source_issue_id,
                self._safe_str(row.project_id, 255),
                row.urgency_score,
                row.complexity_score,
                row.sentiment_score,
                row.categorization_confidence,
                row.discipline_category_id,
                row.primary_category_id,
                row.secondary_category_id,
                row.resolution_days,
                row.is_recurring,
                row.recurring_cluster_id,
                row.comment_count,
                row.processed_at,
                self._safe_str(row.processing_version, 100),
                row.extracted_keywords,
                record_source,
            )
            for row in rows
        ]

        self._bulk_insert(insert_sql, insert_rows)
        latest = max(row.processed_at for row in rows if row.processed_at is not None)
        self._set_watermark(process, source_object, latest, len(rows))
        logger.info("Loaded %s processed issues.", len(rows))
        return len(rows)

    def _load_attribute_map(self) -> Dict[Tuple[str, Optional[str], str], Tuple[str, int]]:
        """Load active attribute mappings keyed by (source_system, project_id, raw_name)."""
        query = """
            SELECT project_id, source_system, raw_attribute_name, mapped_field_name, priority
            FROM dbo.issue_attribute_map
            WHERE is_active = 1
        """
        mapping: Dict[Tuple[str, Optional[str], str], Tuple[str, int]] = {}
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                project_id = str(row[0]).strip() if row[0] is not None else None
                source = str(row[1]).strip()
                raw_name = str(row[2]).strip().lower()
                mapped_name = str(row[3]).strip()
                priority = int(row[4] or 100)
                key = (source, project_id, raw_name)
                existing = mapping.get(key)
                if existing is None or priority < existing[1]:
                    mapping[key] = (mapped_name, priority)
        return mapping

    @staticmethod
    def _parse_custom_attributes(value: Optional[object]) -> List[Dict[str, Optional[str]]]:
        if value is None:
            return []
        text = str(value).strip()
        if not text:
            return []
        try:
            payload = json.loads(text)
        except (TypeError, json.JSONDecodeError):
            return []
        if not isinstance(payload, list):
            return []
        parsed: List[Dict[str, Optional[str]]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            value = item.get("value")
            parsed.append(
                {
                    "name": str(name).strip() if name is not None else None,
                    "type": str(item.get("type")).strip() if item.get("type") is not None else None,
                    "value": str(value) if value is not None else None,
                    "created_at": item.get("created_at"),
                }
            )
        return [row for row in parsed if row.get("name")]

    def load_staging_issue_attributes(self) -> int:
        """Load custom issue attributes into staging with optional mapping."""
        process = "stg_issue_attributes"
        source_object = "vw_ProjectManagement_AllIssues"
        watermark = self._get_watermark(process, source_object)
        logger.info("Loading issue attributes (watermark=%s)", watermark.isoformat())

        select_query = """
            SELECT
                source,
                issue_id,
                project_id,
                custom_attributes_json,
                source_updated_at
            FROM vw_ProjectManagement_AllIssues
            WHERE source = 'ACC'
              AND custom_attributes_json IS NOT NULL
              AND source_updated_at > ?
        """

        rows = self._fetch_source_rows(select_query, watermark)
        if not rows:
            logger.info("No new issue attribute rows to stage.")
            return 0

        mapping = self._load_attribute_map()
        insert_sql = """
            INSERT INTO stg.issue_attributes (
                source_system, issue_id, project_id_raw, attribute_name, attribute_value,
                attribute_type, attribute_created_at, mapped_field_name, map_priority,
                record_source, source_load_ts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
        """
        record_source = "ProjectManagement"
        insert_rows = []
        latest = watermark
        deduped: Dict[Tuple[str, str, str], tuple] = {}

        for row in rows:
            source = row.source
            issue_id = self._safe_str(row.issue_id, 255)
            if not issue_id:
                continue
            project_id_raw = row.project_id
            source_updated_at = row.source_updated_at or watermark
            latest = max(latest, source_updated_at)
            attrs = self._parse_custom_attributes(row.custom_attributes_json)
            for attr in attrs:
                raw_name = self._safe_str(attr["name"], 255)
                if not raw_name:
                    continue
                key = (source, str(project_id_raw).strip() if project_id_raw is not None else None, raw_name.lower())
                mapped = mapping.get(key)
                if mapped is None:
                    mapped = mapping.get((source, None, raw_name.lower()))
                mapped_field_name = mapped[0] if mapped else None
                map_priority = mapped[1] if mapped else None
                attr_value = attr.get("value")
                if isinstance(attr_value, str) and attr_value.strip() == "":
                    attr_value = None
                attr_type = self._safe_str(attr.get("type"), 50)
                attr_created_at = self._safe_datetime(attr.get("created_at"))
                row_key = (source, issue_id, raw_name)
                payload = (
                    source,
                    issue_id,
                    project_id_raw,
                    raw_name,
                    attr_value,
                    attr_type,
                    attr_created_at,
                    self._safe_str(mapped_field_name, 100),
                    map_priority,
                    record_source,
                )
                existing = deduped.get(row_key)
                if existing is None:
                    deduped[row_key] = payload
                else:
                    existing_created = existing[6]
                    if attr_created_at and (existing_created is None or attr_created_at >= existing_created):
                        deduped[row_key] = payload

        insert_rows = list(deduped.values())
        if not insert_rows:
            logger.info("No parsed issue attributes to insert.")
            return 0

        self._bulk_insert(insert_sql, insert_rows)
        self._set_watermark(process, source_object, latest, len(insert_rows))
        logger.info("Loaded %s issue attribute rows into staging.", len(insert_rows))
        return len(insert_rows)

    def load_staging_projects(self) -> int:
        process = "stg_projects"
        source_object = "projects"
        watermark = self._get_watermark(process, source_object)

        select_query = """
            SELECT
                project_id,
                project_name,
                status,
                priority,
                start_date,
                end_date,
                created_at,
                updated_at
            FROM projects
            WHERE updated_at IS NOT NULL AND updated_at > ?
        """

        rows = self._fetch_source_rows(select_query, watermark)
        if not rows:
            logger.info("No project changes detected.")
            return 0

        insert_sql = """
            INSERT INTO stg.projects (
                project_id, project_name, client_id, project_type_id, status, priority,
                start_date, end_date, area_hectares, city, state, country,
                created_at, updated_at, record_source, source_load_ts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
        """
        record_source = "projects"
        insert_rows = [
            (
                row.project_id,
                row.project_name,
                None,  # client_id not available
                None,  # project_type_id not available
                getattr(row, "status", None),
                getattr(row, "priority", None),
                getattr(row, "start_date", None),
                getattr(row, "end_date", None),
                None,  # area_hectares placeholder
                None,  # city placeholder
                None,  # state placeholder
                None,  # country placeholder
                getattr(row, "created_at", None),
                getattr(row, "updated_at", None),
                record_source,
            )
            for row in rows
        ]
        self._bulk_insert(insert_sql, insert_rows)
        latest = max(row.updated_at for row in rows if row.updated_at is not None)
        self._set_watermark(process, source_object, latest, len(rows))
        logger.info("Loaded %s project rows.", len(rows))
        return len(rows)

    def load_staging_services(self) -> int:
        process = "stg_services"
        source_object = "ProjectServices"
        watermark = self._get_watermark(process, source_object)

        select_query = """
            SELECT
                service_id,
                project_id,
                service_code,
                service_name,
                phase,
                unit_type,
                unit_qty,
                unit_rate,
                lump_sum_fee,
                agreed_fee,
                progress_pct,
                claimed_to_date,
                status,
                created_at,
                updated_at
            FROM ProjectServices
            WHERE (updated_at IS NOT NULL AND updated_at > ?)
               OR (created_at IS NOT NULL AND created_at > ?)
        """

        rows = self._fetch_source_rows(select_query, watermark, watermark)
        if not rows:
            logger.info("No service updates detected.")
            return 0

        insert_sql = """
            INSERT INTO stg.project_services (
                service_id, project_id, service_code, service_name, phase, unit_type,
                unit_qty, unit_rate, lump_sum_fee, agreed_fee, progress_pct,
                claimed_to_date, status, created_at, updated_at, record_source, source_load_ts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
        """
        record_source = "ProjectServices"
        insert_rows = [
            (
                row.service_id,
                row.project_id,
                row.service_code,
                row.service_name,
                row.phase,
                row.unit_type,
                row.unit_qty,
                row.unit_rate,
                row.lump_sum_fee,
                row.agreed_fee,
                row.progress_pct,
                row.claimed_to_date,
                row.status,
                row.created_at,
                row.updated_at,
                record_source,
            )
            for row in rows
        ]
        self._bulk_insert(insert_sql, insert_rows)
        latest = max(
            [
                value
                for row in rows
                for value in (row.updated_at, row.created_at)
                if value is not None
            ],
            default=watermark,
        )
        self._set_watermark(process, source_object, latest, len(rows))
        logger.info("Loaded %s service rows.", len(rows))
        return len(rows)

    def load_staging_service_reviews(self) -> int:
        process = "stg_service_reviews"
        source_object = "ServiceReviews"
        watermark = self._get_watermark(process, source_object)
        select_query = """
            SELECT
                review_id,
                service_id,
                cycle_no,
                planned_date,
                due_date,
                actual_issued_at,
                status,
                disciplines,
                deliverables,
                weight_factor,
                evidence_links,
                last_updated_at
            FROM vw_ServiceReviews_WithAudit
            WHERE last_updated_at IS NOT NULL AND last_updated_at > ?
        """
        fallback_query = """
            SELECT
                review_id,
                service_id,
                cycle_no,
                planned_date,
                due_date,
                actual_issued_at,
                status,
                disciplines,
                deliverables,
                weight_factor,
                evidence_links,
                COALESCE(actual_issued_at, planned_date) AS last_updated_at
            FROM ServiceReviews
            WHERE COALESCE(actual_issued_at, planned_date) > ?
        """

        if self._source_object_exists("vw_ServiceReviews_WithAudit", "V"):
            rows = self._fetch_source_rows(select_query, watermark)
        else:
            rows = self._fetch_source_rows(fallback_query, watermark)

        if not rows:
            logger.info("No service review changes detected.")
            return 0

        insert_sql = """
            INSERT INTO stg.service_reviews (
                review_id, service_id, cycle_no, planned_date, due_date, actual_date,
                status, disciplines, deliverables, weight_factor, evidence_links,
                last_status_at, record_source, source_load_ts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
        """
        record_source = "ServiceReviews"
        insert_rows = [
            (
                row.review_id,
                row.service_id,
                row.cycle_no,
                self._safe_datetime(row.planned_date),
                self._safe_datetime(row.due_date),
                self._safe_datetime(row.actual_issued_at),
                row.status,
                row.disciplines,
                row.deliverables,
                row.weight_factor,
                row.evidence_links,
                self._safe_datetime(getattr(row, "last_updated_at", None))
                or self._safe_datetime(row.actual_issued_at)
                or self._safe_datetime(row.planned_date),
                record_source,
            )
            for row in rows
        ]

        self._bulk_insert(insert_sql, insert_rows)
        latest_candidates = [
            self._safe_datetime(getattr(row, "last_updated_at", None))
            or self._safe_datetime(row.actual_issued_at)
            or self._safe_datetime(row.planned_date)
            for row in rows
        ]
        latest = max(candidate for candidate in latest_candidates if candidate is not None)
        self._set_watermark(process, source_object, latest, len(rows))
        logger.info("Loaded %s service reviews.", len(rows))
        return len(rows)

    def load_staging_project_aliases(self) -> int:
        """Load project alias mappings to support dim.project resolution."""
        process = "stg_project_aliases"
        source_object = "dbo.project_aliases"
        watermark = self._get_watermark(process, source_object)
        logger.info("Loading project aliases (watermark=%s)", watermark.isoformat())

        table_name = "dbo.project_aliases"
        has_created_at = self._source_column_exists(table_name, "created_at")
        has_alias_type = self._source_column_exists(table_name, "alias_type")
        alias_type_select = "alias_type" if has_alias_type else "NULL AS alias_type"

        if has_created_at:
            select_query = f"""
                SELECT
                    pm_project_id,
                    alias_name,
                    {alias_type_select},
                    created_at
                FROM {table_name}
                WHERE created_at IS NOT NULL AND created_at > ?
            """
            rows = self._fetch_source_rows(select_query, watermark)
        else:
            select_query = f"""
                SELECT
                    pm_project_id,
                    alias_name,
                    {alias_type_select}
                FROM {table_name}
            """
            rows = self._fetch_source_rows(select_query)

        if not rows:
            logger.info("No alias changes detected.")
            return 0

        insert_sql = """
            INSERT INTO stg.project_aliases (
                pm_project_id,
                alias_name,
                alias_type,
                record_source,
                source_load_ts
            ) VALUES (?, ?, ?, ?, SYSUTCDATETIME())
        """
        record_source = "dbo.project_aliases"
        insert_rows = [
            (
                row.pm_project_id,
                row.alias_name,
                getattr(row, "alias_type", None),
                record_source,
            )
            for row in rows
        ]
        self._bulk_insert(insert_sql, insert_rows)

        if has_created_at:
            latest = max(row.created_at for row in rows if row.created_at is not None)
        else:
            latest = datetime.now(timezone.utc)
        self._set_watermark(process, source_object, latest, len(rows))
        logger.info("Loaded %s project aliases.", len(rows))
        return len(rows)

    # ------------------------------------------------------------------
    # Dimension and fact loaders (high level placeholders)
    # ------------------------------------------------------------------
    def load_dimensions(self) -> None:
        """
        Populate dimension tables from staging.

        The actual implementation relies on stored procedures or MERGE statements.
        Here we invoke database-side routines, allowing SQL scripts to evolve
        without modifying Python orchestrator.
        """
        tasks = [
            "EXEC warehouse.usp_load_dim_date",
            "EXEC warehouse.usp_load_dim_client",
            "EXEC warehouse.usp_load_dim_project_type",
            "EXEC warehouse.usp_load_dim_project",
            "EXEC warehouse.usp_load_dim_project_alias",
            "EXEC warehouse.usp_load_dim_issue_category",
            "EXEC warehouse.usp_load_dim_user",
            "EXEC warehouse.usp_load_dim_issue",
            "EXEC warehouse.usp_load_dim_service",
            "EXEC warehouse.usp_load_dim_review_stage",
            "EXEC warehouse.usp_load_dim_review_cycle",
        ]
        self._execute_warehouse_tasks(tasks, "dimension")

    def load_facts(self) -> None:
        tasks = [
            "EXEC warehouse.usp_load_fact_issue_snapshot",
            "EXEC warehouse.usp_load_fact_issue_activity",
            "EXEC warehouse.usp_load_fact_service_monthly",
            "EXEC warehouse.usp_load_fact_review_cycle",
            "EXEC warehouse.usp_load_fact_review_event",
            "EXEC warehouse.usp_load_fact_project_kpi_monthly",
            "EXEC warehouse.usp_load_bridges",
        ]
        self._execute_warehouse_tasks(tasks, "fact")

    def _execute_warehouse_tasks(self, statements: Iterable[str], label: str) -> None:
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            for statement in statements:
                logger.info("Executing %s task: %s", label, statement)
                cursor.execute(statement)
            conn.commit()

    # ------------------------------------------------------------------
    # Data quality checks
    # ------------------------------------------------------------------
    def run_data_quality_checks(self, checks: Optional[List[DataQualityCheck]] = None) -> None:
        if self._current_run_id is None:
            logger.warning("Cannot record data quality results without active run id.")
            return

        default_checks = [
            DataQualityCheck(
                name="issue_project_fk",
                severity="high",
                query="""
                    SELECT COUNT(*) AS orphan_count
                    FROM fact.issue_snapshot f
                    LEFT JOIN dim.project p ON f.project_sk = p.project_sk
                    WHERE f.project_sk IS NOT NULL AND p.project_sk IS NULL
                """,
                expected_result=lambda rows: rows[0][0] == 0,
                failure_message=lambda rows: f"{rows[0][0]} issue_snapshot rows missing project reference",
            ),
            DataQualityCheck(
                name="review_cycle_dates",
                severity="medium",
                query="""
                    SELECT COUNT(*) AS invalid_dates
                    FROM fact.review_cycle
                    WHERE planned_date_sk IS NOT NULL
                      AND actual_date_sk IS NOT NULL
                      AND planned_date_sk > actual_date_sk
                """,
                expected_result=lambda rows: rows[0][0] == 0,
                failure_message=lambda rows: f"{rows[0][0]} review cycles have actual date before planned date",
            ),
            DataQualityCheck(
                name="issues_unmapped_projects",
                severity="high",
                query="""
                    SELECT COUNT(*) AS unmapped_count
                    FROM dim.issue i
                    WHERE i.current_flag = 1
                      AND ISNULL(i.project_mapped, 0) = 0
                """,
                expected_result=lambda rows: rows[0][0] == 0,
                failure_message=lambda rows: f"{rows[0][0]} issues lack project mapping",
            ),
            DataQualityCheck(
                name="acc_priority_null_rate",
                severity="medium",
                query="""
                    SELECT
                        COUNT(*) AS total,
                        SUM(CASE WHEN i.priority_normalized IS NULL THEN 1 ELSE 0 END) AS nulls
                    FROM dim.issue i
                    WHERE i.current_flag = 1
                      AND i.source_system = 'ACC'
                """,
                expected_result=lambda rows: (rows[0][0] or 0) == 0 or (rows[0][1] / rows[0][0]) <= 0.2,
                failure_message=lambda rows: f"ACC priority null rate {(rows[0][1] / rows[0][0]) * 100:.1f}% exceeds 20%",
            ),
            DataQualityCheck(
                name="issue_snapshot_freshness",
                severity="high",
                query="""
                    SELECT MAX(d.[date]) AS latest_snapshot_date
                    FROM fact.issue_snapshot s
                    JOIN dim.date d ON s.snapshot_date_sk = d.date_sk
                """,
                expected_result=lambda rows: rows[0][0] is not None,
                failure_message=lambda rows: "No issue snapshots available",
            ),
        ]
        checks = checks or default_checks

        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            for check in checks:
                logger.info("Running data quality check: %s", check.name)
                if check.params:
                    cursor.execute(check.query, check.params)
                else:
                    cursor.execute(check.query)
                rows = cursor.fetchall()
                passed = check.expected_result(rows)
                if passed and check.details_on_pass:
                    details = check.failure_message(rows)
                else:
                    details = None if passed else check.failure_message(rows)
                cursor.execute(
                    """
                    INSERT INTO ctl.data_quality_result (run_id, check_name, severity, passed, details)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (self._current_run_id, check.name, check.severity, int(passed), details),
                )
                if not passed:
                    logger.warning("Data quality check failed (%s): %s", check.name, details)
            conn.commit()

    def _load_issue_snapshots(self) -> int:
        """Populate Issues_Snapshots from the latest warehouse snapshot."""
        if self._issue_import_run_id is None:
            logger.warning("No issue import run id available; skipping issue snapshots load.")
            return 0

        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT MAX(s.snapshot_date_sk)
                FROM fact.issue_snapshot s
                """
            )
            row = cursor.fetchone()
            snapshot_date_sk = row[0] if row else None
            if snapshot_date_sk is None:
                logger.warning("No issue snapshots found in fact.issue_snapshot.")
                return 0

            cursor.execute(
                """
                SELECT [date]
                FROM dim.date
                WHERE date_sk = ?
                """,
                (snapshot_date_sk,),
            )
            snapshot_row = cursor.fetchone()
            self._issue_snapshot_date = snapshot_row[0] if snapshot_row else None

            cursor.execute(
                f"""
                INSERT INTO dbo.{S.IssuesSnapshots.TABLE} (
                    {S.IssuesSnapshots.SNAPSHOT_DATE},
                    {S.IssuesSnapshots.IMPORT_RUN_ID},
                    {S.IssuesSnapshots.ISSUE_KEY},
                    {S.IssuesSnapshots.ISSUE_KEY_HASH},
                    {S.IssuesSnapshots.SOURCE_SYSTEM},
                    {S.IssuesSnapshots.SOURCE_ISSUE_ID},
                    {S.IssuesSnapshots.SOURCE_PROJECT_ID},
                    {S.IssuesSnapshots.PROJECT_ID},
                    {S.IssuesSnapshots.STATUS_NORMALIZED},
                    {S.IssuesSnapshots.PRIORITY_NORMALIZED},
                    {S.IssuesSnapshots.DISCIPLINE_NORMALIZED},
                    {S.IssuesSnapshots.LOCATION_ROOT},
                    {S.IssuesSnapshots.ASSIGNEE_USER_KEY},
                    {S.IssuesSnapshots.IS_OPEN},
                    {S.IssuesSnapshots.IS_CLOSED},
                    {S.IssuesSnapshots.BACKLOG_AGE_DAYS},
                    {S.IssuesSnapshots.RESOLUTION_DAYS},
                    {S.IssuesSnapshots.CREATED_AT},
                    {S.IssuesSnapshots.UPDATED_AT},
                    {S.IssuesSnapshots.CLOSED_AT}
                )
                SELECT
                    d.[date] AS snapshot_date,
                    ? AS import_run_id,
                    CONCAT(
                        i.source_system,
                        '|',
                        COALESCE(NULLIF(i.source_project_id, ''), CAST(p.project_bk AS NVARCHAR(255)), 'unknown'),
                        '|',
                        COALESCE(NULLIF(i.source_issue_id, ''), i.issue_bk)
                    ) AS issue_key,
                    HASHBYTES(
                        'SHA2_256',
                        CONCAT(
                            i.source_system,
                            '|',
                            COALESCE(NULLIF(i.source_project_id, ''), CAST(p.project_bk AS NVARCHAR(255)), 'unknown'),
                            '|',
                            COALESCE(NULLIF(i.source_issue_id, ''), i.issue_bk)
                        )
                    ) AS issue_key_hash,
                    i.source_system,
                    COALESCE(NULLIF(i.source_issue_id, ''), i.issue_bk) AS source_issue_id,
                    COALESCE(NULLIF(i.source_project_id, ''), CAST(p.project_bk AS NVARCHAR(255)), 'unknown') AS source_project_id,
                    CAST(p.project_bk AS NVARCHAR(100)) AS project_id,
                    COALESCE(i.status_normalized, sm.{S.IssueStatusMap.NORMALIZED_STATUS}) AS status_normalized,
                    i.priority_normalized,
                    dp.discipline,
                    i.location_root,
                    u.user_bk AS assignee_user_key,
                    s.is_open,
                    s.is_closed,
                    s.backlog_age_days,
                    s.resolution_days,
                    d_created.[date] AS created_at,
                    NULL AS updated_at,
                    d_closed.[date] AS closed_at
                FROM fact.issue_snapshot s
                JOIN dim.issue i ON s.issue_sk = i.issue_sk
                LEFT JOIN dim.project p ON s.project_sk = p.project_sk
                LEFT JOIN dbo.{S.IssueStatusMap.TABLE} sm
                    ON sm.{S.IssueStatusMap.SOURCE_SYSTEM} = i.source_system
                   AND sm.{S.IssueStatusMap.RAW_STATUS} = LOWER(LTRIM(RTRIM(i.status)))
                   AND sm.{S.IssueStatusMap.IS_ACTIVE} = 1
                LEFT JOIN dim.[user] u
                    ON i.assignee_sk = u.user_sk AND u.current_flag = 1
                LEFT JOIN (
                    SELECT bic.issue_sk, MAX(ic.level1_name) AS discipline
                    FROM brg.issue_category bic
                    JOIN dim.issue_category ic
                        ON bic.issue_category_sk = ic.issue_category_sk
                    WHERE bic.category_role = 'discipline'
                    GROUP BY bic.issue_sk
                ) dp ON i.issue_sk = dp.issue_sk
                JOIN dim.date d ON s.snapshot_date_sk = d.date_sk
                LEFT JOIN dim.date d_created ON i.created_date_sk = d_created.date_sk
                LEFT JOIN dim.date d_closed ON i.closed_date_sk = d_closed.date_sk
                WHERE s.snapshot_date_sk = ?
                  AND i.current_flag = 1
                """,
                (self._issue_import_run_id, snapshot_date_sk),
            )
            inserted = cursor.rowcount if cursor.rowcount is not None else 0
            conn.commit()
        logger.info("Inserted %s issue snapshot rows for run %s", inserted, self._issue_import_run_id)
        return inserted

    def _run_issue_quality_checks(self) -> bool:
        """Run issue reliability checks and store results."""
        if self._issue_import_run_id is None:
            logger.warning("Cannot run issue quality checks without issue import run id.")
            return False

        checks = [
            DataQualityCheck(
                name="issue_key_uniqueness",
                severity="high",
                query=f"""
                    SELECT COUNT(*) AS total_rows,
                           COUNT(DISTINCT {S.IssuesSnapshots.ISSUE_KEY}) AS distinct_keys
                    FROM dbo.{S.IssuesSnapshots.TABLE}
                    WHERE {S.IssuesSnapshots.IMPORT_RUN_ID} = ?
                """,
                params=(self._issue_import_run_id,),
                expected_result=lambda rows: rows[0][0] == rows[0][1],
                failure_message=lambda rows: f"{rows[0][0] - rows[0][1]} duplicate issue_key rows",
            ),
            DataQualityCheck(
                name="issue_join_explosion_project",
                severity="high",
                query=f"""
                    SELECT
                        (SELECT COUNT(*)
                         FROM dbo.{S.IssuesSnapshots.TABLE}
                         WHERE {S.IssuesSnapshots.IMPORT_RUN_ID} = ?) AS base_count,
                        (SELECT COUNT(*)
                         FROM dbo.{S.IssuesSnapshots.TABLE} s
                         LEFT JOIN dim.project p
                             ON TRY_CAST(s.{S.IssuesSnapshots.PROJECT_ID} AS INT) = p.project_bk
                         WHERE s.{S.IssuesSnapshots.IMPORT_RUN_ID} = ?) AS joined_count
                """,
                params=(self._issue_import_run_id, self._issue_import_run_id),
                expected_result=lambda rows: rows[0][0] == rows[0][1],
                failure_message=lambda rows: f"Join explosion detected (base={rows[0][0]}, joined={rows[0][1]})",
            ),
            DataQualityCheck(
                name="issue_project_orphans",
                severity="high",
                query=f"""
                    SELECT COUNT(*) AS orphan_count
                    FROM dbo.{S.IssuesSnapshots.TABLE} s
                    LEFT JOIN dim.project p
                        ON TRY_CAST(s.{S.IssuesSnapshots.PROJECT_ID} AS INT) = p.project_bk
                    WHERE s.{S.IssuesSnapshots.IMPORT_RUN_ID} = ?
                      AND s.{S.IssuesSnapshots.PROJECT_ID} IS NOT NULL
                      AND p.project_sk IS NULL
                """,
                params=(self._issue_import_run_id,),
                expected_result=lambda rows: rows[0][0] == 0,
                failure_message=lambda rows: f"{rows[0][0]} issue rows missing project mapping",
            ),
            DataQualityCheck(
                name="issue_status_normalized_coverage",
                severity="high",
                query=f"""
                    SELECT COUNT(*) AS missing_status
                    FROM dbo.{S.IssuesSnapshots.TABLE}
                    WHERE {S.IssuesSnapshots.IMPORT_RUN_ID} = ?
                      AND ( {S.IssuesSnapshots.STATUS_NORMALIZED} IS NULL
                            OR LTRIM(RTRIM({S.IssuesSnapshots.STATUS_NORMALIZED})) = '' )
                """,
                params=(self._issue_import_run_id,),
                expected_result=lambda rows: rows[0][0] == 0,
                failure_message=lambda rows: f"{rows[0][0]} issues missing normalized status",
            ),
            DataQualityCheck(
                name="issue_time_sanity",
                severity="medium",
                query=f"""
                    SELECT COUNT(*) AS invalid_dates
                    FROM dbo.{S.IssuesSnapshots.TABLE}
                    WHERE {S.IssuesSnapshots.IMPORT_RUN_ID} = ?
                      AND {S.IssuesSnapshots.CLOSED_AT} IS NOT NULL
                      AND {S.IssuesSnapshots.CREATED_AT} IS NOT NULL
                      AND {S.IssuesSnapshots.CLOSED_AT} < {S.IssuesSnapshots.CREATED_AT}
                """,
                params=(self._issue_import_run_id,),
                expected_result=lambda rows: rows[0][0] == 0,
                failure_message=lambda rows: f"{rows[0][0]} issues closed before created",
            ),
            DataQualityCheck(
                name="issue_current_vs_snapshot_count",
                severity="medium",
                query=f"""
                    SELECT
                        (SELECT COUNT(*)
                         FROM dbo.{S.IssuesCurrent.TABLE}) AS current_count,
                        (SELECT COUNT(*)
                         FROM dbo.{S.IssuesSnapshots.TABLE}
                         WHERE {S.IssuesSnapshots.IMPORT_RUN_ID} = ?) AS snapshot_count
                """,
                params=(self._issue_import_run_id,),
                expected_result=lambda rows: rows[0][0] == rows[0][1],
                failure_message=lambda rows: f"current={rows[0][0]} snapshot={rows[0][1]}",
                details_on_pass=True,
            ),
            DataQualityCheck(
                name="issue_status_changes",
                severity="info",
                query=f"""
                    WITH current_run AS (
                        SELECT ? AS run_id
                    ),
                    current_completed AS (
                        SELECT completed_at
                        FROM dbo.{S.IssueImportRuns.TABLE}
                        WHERE {S.IssueImportRuns.IMPORT_RUN_ID} = ?
                    ),
                    prev_run AS (
                        SELECT TOP 1 {S.IssueImportRuns.IMPORT_RUN_ID} AS run_id
                        FROM dbo.{S.IssueImportRuns.TABLE}
                        WHERE {S.IssueImportRuns.STATUS} = 'success'
                          AND completed_at < (SELECT completed_at FROM current_completed)
                        ORDER BY completed_at DESC
                    ),
                    current_snap AS (
                        SELECT issue_key_hash, status_normalized
                        FROM dbo.{S.IssuesSnapshots.TABLE}
                        WHERE import_run_id = (SELECT run_id FROM current_run)
                    ),
                    prev_snap AS (
                        SELECT issue_key_hash, status_normalized
                        FROM dbo.{S.IssuesSnapshots.TABLE}
                        WHERE import_run_id = (SELECT run_id FROM prev_run)
                    )
                    SELECT
                        COALESCE((SELECT COUNT(*) FROM current_snap), 0) AS current_count,
                        COALESCE((SELECT COUNT(*) FROM prev_snap), 0) AS prev_count,
                        COALESCE((SELECT COUNT(*) FROM current_snap c JOIN prev_snap p ON c.issue_key_hash = p.issue_key_hash), 0) AS compared_count,
                        COALESCE((
                            SELECT COUNT(*)
                            FROM current_snap c
                            JOIN prev_snap p ON c.issue_key_hash = p.issue_key_hash
                            WHERE ISNULL(c.status_normalized, '') <> ISNULL(p.status_normalized, '')
                        ), 0) AS changed_count
                """,
                params=(self._issue_import_run_id, self._issue_import_run_id),
                expected_result=lambda rows: True,
                failure_message=lambda rows: (
                    f"current={rows[0][0]} prev={rows[0][1]} compared={rows[0][2]} status_changed={rows[0][3]}"
                ),
                details_on_pass=True,
            ),
            DataQualityCheck(
                name="issue_assignee_changes",
                severity="info",
                query=f"""
                    WITH current_run AS (
                        SELECT ? AS run_id
                    ),
                    current_completed AS (
                        SELECT completed_at
                        FROM dbo.{S.IssueImportRuns.TABLE}
                        WHERE {S.IssueImportRuns.IMPORT_RUN_ID} = ?
                    ),
                    prev_run AS (
                        SELECT TOP 1 {S.IssueImportRuns.IMPORT_RUN_ID} AS run_id
                        FROM dbo.{S.IssueImportRuns.TABLE}
                        WHERE {S.IssueImportRuns.STATUS} = 'success'
                          AND completed_at < (SELECT completed_at FROM current_completed)
                        ORDER BY completed_at DESC
                    ),
                    current_snap AS (
                        SELECT issue_key_hash, assignee_user_key
                        FROM dbo.{S.IssuesSnapshots.TABLE}
                        WHERE import_run_id = (SELECT run_id FROM current_run)
                    ),
                    prev_snap AS (
                        SELECT issue_key_hash, assignee_user_key
                        FROM dbo.{S.IssuesSnapshots.TABLE}
                        WHERE import_run_id = (SELECT run_id FROM prev_run)
                    )
                    SELECT
                        COALESCE((SELECT COUNT(*) FROM current_snap), 0) AS current_count,
                        COALESCE((SELECT COUNT(*) FROM prev_snap), 0) AS prev_count,
                        COALESCE((SELECT COUNT(*) FROM current_snap c JOIN prev_snap p ON c.issue_key_hash = p.issue_key_hash), 0) AS compared_count,
                        COALESCE((
                            SELECT COUNT(*)
                            FROM current_snap c
                            JOIN prev_snap p ON c.issue_key_hash = p.issue_key_hash
                            WHERE ISNULL(c.assignee_user_key, '') <> ISNULL(p.assignee_user_key, '')
                        ), 0) AS changed_count
                """,
                params=(self._issue_import_run_id, self._issue_import_run_id),
                expected_result=lambda rows: True,
                failure_message=lambda rows: (
                    f"current={rows[0][0]} prev={rows[0][1]} compared={rows[0][2]} assignee_changed={rows[0][3]}"
                ),
                details_on_pass=True,
            ),
        ]

        all_passed = True
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            for check in checks:
                logger.info("Running issue quality check: %s", check.name)
                if check.params:
                    cursor.execute(check.query, check.params)
                else:
                    cursor.execute(check.query)
                rows = cursor.fetchall()
                passed = check.expected_result(rows)
                if passed and check.details_on_pass:
                    details = check.failure_message(rows)
                else:
                    details = None if passed else check.failure_message(rows)
                cursor.execute(
                    f"""
                    INSERT INTO dbo.{S.IssueDataQualityResults.TABLE} (
                        {S.IssueDataQualityResults.IMPORT_RUN_ID},
                        {S.IssueDataQualityResults.CHECK_NAME},
                        {S.IssueDataQualityResults.SEVERITY},
                        {S.IssueDataQualityResults.PASSED},
                        {S.IssueDataQualityResults.DETAILS}
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        self._issue_import_run_id,
                        check.name,
                        check.severity,
                        int(passed),
                        details,
                    ),
                )
                if not passed:
                    all_passed = False
                    logger.warning("Issue quality check failed: %s (%s)", check.name, details)
            conn.commit()
        return all_passed

    def _refresh_issues_current(self) -> int:
        """Replace Issues_Current using the latest snapshot for the current run."""
        if self._issue_import_run_id is None:
            logger.warning("Cannot refresh Issues_Current without issue import run id.")
            return 0

        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT MAX({S.IssuesSnapshots.SNAPSHOT_DATE})
                FROM dbo.{S.IssuesSnapshots.TABLE}
                WHERE {S.IssuesSnapshots.IMPORT_RUN_ID} = ?
                """,
                (self._issue_import_run_id,),
            )
            row = cursor.fetchone()
            snapshot_date = row[0] if row else None
            if snapshot_date is None:
                logger.warning("No issue snapshots found for current run.")
                return 0

            cursor.execute(f"DELETE FROM dbo.{S.IssuesCurrent.TABLE}")

            cursor.execute(
                f"""
                WITH snapshot_rows AS (
                    SELECT
                        s.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY s.{S.IssuesSnapshots.ISSUE_KEY_HASH}
                            ORDER BY s.{S.IssuesSnapshots.SNAPSHOT_ID} DESC
                        ) AS rn
                    FROM dbo.{S.IssuesSnapshots.TABLE} s
                    WHERE s.{S.IssuesSnapshots.IMPORT_RUN_ID} = ?
                      AND s.{S.IssuesSnapshots.SNAPSHOT_DATE} = ?
                ),
                enriched AS (
                    SELECT
                        s.{S.IssuesSnapshots.ISSUE_KEY},
                        s.{S.IssuesSnapshots.ISSUE_KEY_HASH},
                        s.{S.IssuesSnapshots.SOURCE_SYSTEM},
                        s.{S.IssuesSnapshots.SOURCE_ISSUE_ID},
                        s.{S.IssuesSnapshots.SOURCE_PROJECT_ID},
                        s.{S.IssuesSnapshots.PROJECT_ID},
                        i.status AS status_raw,
                        COALESCE(i.status_normalized, sm.{S.IssueStatusMap.NORMALIZED_STATUS}) AS status_normalized,
                        i.priority AS priority_raw,
                        i.priority_normalized,
                        dp.discipline AS discipline_raw,
                        dp.discipline AS discipline_normalized,
                        u.user_bk AS assignee_user_key,
                        s.{S.IssuesSnapshots.CREATED_AT} AS created_at,
                        s.{S.IssuesSnapshots.UPDATED_AT} AS updated_at,
                        s.{S.IssuesSnapshots.CLOSED_AT} AS closed_at,
                        i.location_root,
                        i.location_building,
                        i.location_level,
                        i.is_deleted,
                        i.project_mapped,
                        s.{S.IssuesSnapshots.IMPORT_RUN_ID} AS import_run_id,
                        s.{S.IssuesSnapshots.SNAPSHOT_ID} AS snapshot_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY s.{S.IssuesSnapshots.ISSUE_KEY_HASH}
                            ORDER BY i.issue_sk DESC
                        ) AS issue_rn
                    FROM snapshot_rows s
                    JOIN dim.issue i
                        ON i.source_system = s.{S.IssuesSnapshots.SOURCE_SYSTEM}
                       AND COALESCE(NULLIF(i.source_issue_id, ''), i.issue_bk) = s.{S.IssuesSnapshots.SOURCE_ISSUE_ID}
                       AND COALESCE(NULLIF(i.source_project_id, ''), s.{S.IssuesSnapshots.SOURCE_PROJECT_ID})
                           = s.{S.IssuesSnapshots.SOURCE_PROJECT_ID}
                    LEFT JOIN dbo.{S.IssueStatusMap.TABLE} sm
                        ON sm.{S.IssueStatusMap.SOURCE_SYSTEM} = i.source_system
                       AND sm.{S.IssueStatusMap.RAW_STATUS} = LOWER(LTRIM(RTRIM(i.status)))
                       AND sm.{S.IssueStatusMap.IS_ACTIVE} = 1
                    LEFT JOIN dim.[user] u
                        ON i.assignee_sk = u.user_sk AND u.current_flag = 1
                    LEFT JOIN (
                        SELECT bic.issue_sk, MAX(ic.level1_name) AS discipline
                        FROM brg.issue_category bic
                        JOIN dim.issue_category ic
                            ON bic.issue_category_sk = ic.issue_category_sk
                        WHERE bic.category_role = 'discipline'
                        GROUP BY bic.issue_sk
                    ) dp ON i.issue_sk = dp.issue_sk
                    WHERE s.rn = 1
                      AND i.current_flag = 1
                )
                INSERT INTO dbo.{S.IssuesCurrent.TABLE} (
                    {S.IssuesCurrent.ISSUE_KEY},
                    {S.IssuesCurrent.ISSUE_KEY_HASH},
                    {S.IssuesCurrent.SOURCE_SYSTEM},
                    {S.IssuesCurrent.SOURCE_ISSUE_ID},
                    {S.IssuesCurrent.SOURCE_PROJECT_ID},
                    {S.IssuesCurrent.PROJECT_ID},
                    {S.IssuesCurrent.STATUS_RAW},
                    {S.IssuesCurrent.STATUS_NORMALIZED},
                    {S.IssuesCurrent.PRIORITY_RAW},
                    {S.IssuesCurrent.PRIORITY_NORMALIZED},
                    {S.IssuesCurrent.DISCIPLINE_RAW},
                    {S.IssuesCurrent.DISCIPLINE_NORMALIZED},
                    {S.IssuesCurrent.ASSIGNEE_USER_KEY},
                    {S.IssuesCurrent.CREATED_AT},
                    {S.IssuesCurrent.UPDATED_AT},
                    {S.IssuesCurrent.CLOSED_AT},
                    {S.IssuesCurrent.LOCATION_ROOT},
                    {S.IssuesCurrent.LOCATION_BUILDING},
                    {S.IssuesCurrent.LOCATION_LEVEL},
                    {S.IssuesCurrent.IS_DELETED},
                    {S.IssuesCurrent.PROJECT_MAPPED},
                    {S.IssuesCurrent.IMPORT_RUN_ID},
                    {S.IssuesCurrent.SNAPSHOT_ID}
                )
                SELECT
                    issue_key,
                    issue_key_hash,
                    source_system,
                    source_issue_id,
                    source_project_id,
                    project_id,
                    status_raw,
                    status_normalized,
                    priority_raw,
                    priority_normalized,
                    discipline_raw,
                    discipline_normalized,
                    assignee_user_key,
                    created_at,
                    updated_at,
                    closed_at,
                    location_root,
                    location_building,
                    location_level,
                    is_deleted,
                    project_mapped,
                    import_run_id,
                    snapshot_id
                FROM enriched
                WHERE issue_rn = 1
                """,
                (self._issue_import_run_id, snapshot_date),
            )
            inserted = cursor.rowcount if cursor.rowcount is not None else 0
            conn.commit()
        logger.info("Refreshed Issues_Current with %s rows", inserted)
        return inserted

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _fetch_source_rows(self, query: str, *params) -> List[pyodbc.Row]:
        with get_db_connection(self.source_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    @staticmethod
    def _safe_datetime(value: Optional[object]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.year >= 1900 else None
        from datetime import date

        if isinstance(value, date):
            try:
                candidate = datetime.combine(value, datetime.min.time())
                return candidate if candidate.year >= 1900 else None
            except ValueError:
                return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.year < 1900:
                return None
            return parsed
        except (ValueError, TypeError):
            return None

    def _source_object_exists(self, object_name: str, object_type: Optional[str] = None) -> bool:
        query = """
            SELECT 1
            FROM sys.objects
            WHERE object_id = OBJECT_ID(?)
        """
        params: List[object] = [object_name]
        if object_type:
            query += " AND type = ?"
            params.append(object_type)
        with get_db_connection(self.source_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone() is not None

    def _source_column_exists(self, table_name: str, column_name: str) -> bool:
        if "." in table_name:
            schema_name, base_table = table_name.split(".", 1)
        else:
            schema_name, base_table = "dbo", table_name
        query = """
            SELECT 1
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ?
              AND TABLE_NAME = ?
              AND COLUMN_NAME = ?
        """
        with get_db_connection(self.source_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (schema_name, base_table, column_name))
            return cursor.fetchone() is not None

    def _bulk_insert(self, insert_sql: str, rows: Iterable[tuple]) -> None:
        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            batch = list(rows)
            if not batch:
                return
            try:
                cursor.fast_executemany = True
                cursor.executemany(insert_sql, batch)
            except (pyodbc.ProgrammingError, pyodbc.DataError, pyodbc.Error) as exc:
                logger.warning("Bulk insert fallback due to %s: %s", type(exc).__name__, exc)
                cursor.fast_executemany = False
                for idx, row in enumerate(batch):
                    try:
                        cursor.execute(insert_sql, row)
                    except (pyodbc.ProgrammingError, pyodbc.DataError, pyodbc.Error) as row_exc:
                        logger.error(
                            "Failed to insert row %s into staging: %s | values=%s",
                            idx,
                            row_exc,
                            row,
                        )
                        raise
            conn.commit()

    @staticmethod
    def _safe_str(value: Optional[object], max_length: Optional[int] = None) -> Optional[str]:
        if value is None:
            return None
        text = str(value)
        if max_length is not None and len(text) > max_length:
            return text[:max_length]
        return text

    @staticmethod
    def _normalize_priority(value: Optional[object]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        key = text.upper()
        if key in ("NONE", "N/A", "NA", "NULL", "UNKNOWN"):
            return None
        if key in ("BLOCKER", "CRITICAL", "L1 - CRITICAL"):
            return "Critical"
        if key in ("MAJOR", "L2 - IMPORTANT"):
            return "High"
        if key in ("MINOR", "L3 - SIGNIFICANT"):
            return "Medium"
        if key in ("TRIVIAL", "L4 - MINOR"):
            return "Low"
        return text.title()

    @staticmethod
    def _extract_revizto_tag(value: Optional[object]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            import json

            parsed = json.loads(text)
        except (TypeError, json.JSONDecodeError):
            return text
        if isinstance(parsed, list) and parsed:
            return str(parsed[0])
        return None

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def run(self) -> None:
        self._start_run()
        self._start_issue_import_run(run_type=self.pipeline_name)
        try:
            staged_counts = {
                "issues": self.load_staging_issues(),
                "processed_issues": self.load_staging_processed_issues(),
                "issue_attributes": self.load_staging_issue_attributes(),
                "projects": self.load_staging_projects(),
                "services": self.load_staging_services(),
                "service_reviews": self.load_staging_service_reviews(),
                "project_aliases": self.load_staging_project_aliases(),
            }
            logger.info("Staging summary: %s", staged_counts)

            self.load_dimensions()
            self.load_facts()
            issue_snapshot_count = self._load_issue_snapshots()
            issue_checks_passed = self._run_issue_quality_checks()
            if issue_checks_passed:
                self._refresh_issues_current()
                self._complete_issue_import_run(
                    status="success",
                    row_count=issue_snapshot_count,
                )
            else:
                self._complete_issue_import_run(
                    status="failed",
                    message="Issue quality checks failed",
                    row_count=issue_snapshot_count,
                )

            self.run_data_quality_checks()

            self._complete_run(status="success")
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Warehouse pipeline failed: %s", exc)
            self._complete_run(status="failed", message=str(exc))
            self._complete_issue_import_run(status="failed", message=str(exc))
            raise


def configure_logging(level: str = Config.LOG_LEVEL) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def main() -> None:
    configure_logging()
    pipeline = WarehousePipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
