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
from typing import Callable, Dict, Iterable, List, Optional, Sequence

import pyodbc  # type: ignore

from config import Config
from database_pool import get_db_connection

logger = logging.getLogger(__name__)


@dataclass
class DataQualityCheck:
    """Represents a configurable data-quality validation."""

    name: str
    severity: str
    query: str
    expected_result: Callable[[Sequence[pyodbc.Row]], bool]
    failure_message: Callable[[Sequence[pyodbc.Row]], str]


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
                    source,
                    CAST(issue_id AS NVARCHAR(255)) AS issue_id,
                    project_name,
                    CAST(project_id AS NVARCHAR(255)) AS project_id_raw,
                    status,
                    priority,
                    title,
                    assignee,
                    author,
                    created_at,
                    closed_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY source, issue_id
                        ORDER BY
                            CASE WHEN created_at IS NOT NULL THEN created_at ELSE '1900-01-01' END DESC,
                            CASE WHEN closed_at IS NOT NULL THEN closed_at ELSE '1900-01-01' END DESC
                    ) AS rn
                FROM vw_ProjectManagement_AllIssues
                WHERE
                    (created_at IS NOT NULL AND created_at > ?)
                    OR (closed_at IS NOT NULL AND closed_at > ?)
                    OR (last_activity_date IS NOT NULL AND last_activity_date > ?)
            )
            SELECT
                source,
                issue_id,
                project_name,
                project_id_raw,
                status,
                priority,
                title,
                assignee,
                author,
                created_at,
                closed_at,
                last_activity_date
            FROM source_issues
            WHERE rn = 1
        """

        rows = self._fetch_source_rows(select_query, watermark, watermark, watermark)
        if not rows:
            logger.info("No new issue rows to load.")
            return 0

        insert_sql = """
            INSERT INTO stg.issues (
                source_system, issue_id, project_name, project_id_raw, status, priority,
                title, description, assignee, author, created_at, closed_at,
                last_activity_date, due_date, discipline, category_primary,
                category_secondary, record_source, source_load_ts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
        """
        record_source = "ProjectManagement"
        insert_rows = [
            (
                row.source,
                row.issue_id,
                row.project_name,
                row.project_id_raw,
                row.status,
                row.priority,
                row.title,
                getattr(row, "description", None),
                row.assignee,
                row.author,
                row.created_at,
                row.closed_at,
                getattr(row, "last_activity_date", None),
                getattr(row, "due_date", None),
                getattr(row, "discipline", None),
                getattr(row, "primary_category", None),
                getattr(row, "secondary_category", None),
                record_source,
            )
            for row in rows
        ]

        self._bulk_insert(insert_sql, insert_rows)

        latest = max(
            [
                value
                for row in rows
                for value in (row.created_at, row.closed_at, getattr(row, "last_activity_date", None))
                if value is not None
            ],
            default=watermark,
        )
        self._set_watermark(process, source_object, latest, len(rows))
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
        ]
        checks = checks or default_checks

        with get_db_connection(self.warehouse_db) as conn:
            cursor = conn.cursor()
            for check in checks:
                logger.info("Running data quality check: %s", check.name)
                cursor.execute(check.query)
                rows = cursor.fetchall()
                passed = check.expected_result(rows)
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
            except (pyodbc.ProgrammingError, pyodbc.DataError) as exc:
                logger.warning("Bulk insert fallback due to %s: %s", type(exc).__name__, exc)
                cursor.fast_executemany = False
                for idx, row in enumerate(batch):
                    try:
                        cursor.execute(insert_sql, row)
                    except (pyodbc.ProgrammingError, pyodbc.DataError) as row_exc:
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

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def run(self) -> None:
        self._start_run()
        try:
            staged_counts = {
                "issues": self.load_staging_issues(),
                "processed_issues": self.load_staging_processed_issues(),
                "projects": self.load_staging_projects(),
                "services": self.load_staging_services(),
                "service_reviews": self.load_staging_service_reviews(),
                "project_aliases": self.load_staging_project_aliases(),
            }
            logger.info("Staging summary: %s", staged_counts)

            self.load_dimensions()
            self.load_facts()
            self.run_data_quality_checks()

            self._complete_run(status="success")
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Warehouse pipeline failed: %s", exc)
            self._complete_run(status="failed", message=str(exc))
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
