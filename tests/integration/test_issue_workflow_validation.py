import pytest

from config import Config
from database_pool import get_db_connection


pytestmark = pytest.mark.integration


def _db():
    try:
        return get_db_connection(Config.WAREHOUSE_DB)
    except Exception as exc:
        pytest.skip(f"Database not reachable: {exc}")


def _latest_staging_ts(cursor, table_name):
    cursor.execute(f"SELECT MAX(source_load_ts) FROM {table_name}")
    row = cursor.fetchone()
    return row[0] if row else None


def _latest_issue_import_run(cursor):
    cursor.execute(
        """
        SELECT TOP 1 import_run_id
        FROM dbo.IssueImportRuns
        WHERE status = 'success'
        ORDER BY completed_at DESC, import_run_id DESC
        """
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _latest_issue_snapshot_date(cursor, import_run_id):
    cursor.execute(
        """
        SELECT MAX(snapshot_date)
        FROM dbo.Issues_Snapshots
        WHERE import_run_id = ?
        """,
        (import_run_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def test_staging_issues_latest_load_has_no_duplicates():
    with _db() as conn:
        cursor = conn.cursor()
        latest_ts = _latest_staging_ts(cursor, "stg.issues")
        if latest_ts is None:
            pytest.skip("No stg.issues data available")

        cursor.execute(
            """
            SELECT source_system,
                   COUNT(*) AS total_rows,
                   COUNT(DISTINCT issue_id) AS distinct_issue_ids
            FROM stg.issues
            WHERE source_load_ts = ?
              AND ISNULL(is_deleted, 0) = 0
            GROUP BY source_system
            """,
            (latest_ts,),
        )
        rows = cursor.fetchall()
        if not rows:
            pytest.skip("No staging rows found for latest load")

        duplicates = []
        for source_system, total_rows, distinct_issue_ids in rows:
            if total_rows != distinct_issue_ids:
                duplicates.append((source_system, total_rows, distinct_issue_ids))

        assert not duplicates, f"Duplicate staging issues detected: {duplicates}"


def test_staging_to_dim_issue_coverage():
    with _db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stg.issues")
        if cursor.fetchone()[0] == 0:
            pytest.skip("No staging issues available")

        cursor.execute(
            """
            WITH latest AS (
                SELECT source_system, MAX(source_load_ts) AS max_ts
                FROM stg.issues
                GROUP BY source_system
            ),
            latest_rows AS (
                SELECT s.*
                FROM stg.issues s
                JOIN latest l
                  ON s.source_system = l.source_system
                 AND s.source_load_ts = l.max_ts
                WHERE ISNULL(s.is_deleted, 0) = 0
            )
            SELECT lr.source_system, COUNT(*) AS missing_count
            FROM latest_rows lr
            LEFT JOIN dim.issue i
              ON i.source_system = lr.source_system
             AND COALESCE(NULLIF(i.source_issue_id, ''), i.issue_bk) = lr.issue_id
             AND i.current_flag = 1
            WHERE i.issue_sk IS NULL
            GROUP BY lr.source_system
            """
        )
        missing = cursor.fetchall()
        missing = [(row[0], row[1]) for row in missing if row[1] > 0]

        samples = {}
        for source_system, _count in missing:
            cursor.execute(
                """
                WITH latest AS (
                    SELECT source_system, MAX(source_load_ts) AS max_ts
                    FROM stg.issues
                    GROUP BY source_system
                )
                SELECT TOP 5 s.issue_id
                FROM stg.issues s
                JOIN latest l
                  ON s.source_system = l.source_system
                 AND s.source_load_ts = l.max_ts
                LEFT JOIN dim.issue i
                  ON i.source_system = s.source_system
                 AND COALESCE(NULLIF(i.source_issue_id, ''), i.issue_bk) = s.issue_id
                 AND i.current_flag = 1
                WHERE s.source_system = ?
                  AND ISNULL(s.is_deleted, 0) = 0
                  AND i.issue_sk IS NULL
                ORDER BY s.issue_id
                """,
                (source_system,),
            )
            samples[source_system] = [row[0] for row in cursor.fetchall()]

        assert not missing, f"Staging issues missing in dim.issue: {missing}, samples={samples}"


def test_issues_current_matches_latest_snapshot():
    with _db() as conn:
        cursor = conn.cursor()
        import_run_id = _latest_issue_import_run(cursor)
        if import_run_id is None:
            pytest.skip("No successful issue import runs found")

        snapshot_date = _latest_issue_snapshot_date(cursor, import_run_id)
        if snapshot_date is None:
            pytest.skip("No Issues_Snapshots found for latest import run")

        cursor.execute(
            """
            SELECT source_system, COUNT(DISTINCT issue_key_hash) AS snapshot_count
            FROM dbo.Issues_Snapshots
            WHERE import_run_id = ?
              AND snapshot_date = ?
            GROUP BY source_system
            """,
            (import_run_id, snapshot_date),
        )
        snapshot_counts = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT source_system, COUNT(*) AS current_count
            FROM dbo.Issues_Current
            WHERE import_run_id = ?
            GROUP BY source_system
            """,
            (import_run_id,),
        )
        current_counts = {row[0]: row[1] for row in cursor.fetchall()}

        mismatches = []
        for source_system, snapshot_count in snapshot_counts.items():
            current_count = current_counts.get(source_system, 0)
            if current_count != snapshot_count:
                mismatches.append((source_system, snapshot_count, current_count))

        assert not mismatches, f"Issues_Current counts differ from snapshots: {mismatches}"


def test_issue_snapshots_match_fact_snapshot_counts():
    with _db() as conn:
        cursor = conn.cursor()
        import_run_id = _latest_issue_import_run(cursor)
        if import_run_id is None:
            pytest.skip("No successful issue import runs found")

        snapshot_date = _latest_issue_snapshot_date(cursor, import_run_id)
        if snapshot_date is None:
            pytest.skip("No Issues_Snapshots found for latest import run")

        cursor.execute("SELECT date_sk FROM dim.date WHERE [date] = ?", (snapshot_date,))
        row = cursor.fetchone()
        if not row:
            pytest.skip("No dim.date row for latest snapshot date")
        snapshot_date_sk = row[0]

        cursor.execute(
            """
            SELECT COUNT(*) FROM dbo.Issues_Snapshots
            WHERE import_run_id = ? AND snapshot_date = ?
            """,
            (import_run_id, snapshot_date),
        )
        snapshots_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM fact.issue_snapshot WHERE snapshot_date_sk = ?",
            (snapshot_date_sk,),
        )
        fact_count = cursor.fetchone()[0]

        assert snapshots_count == fact_count, (
            f"Issues_Snapshots ({snapshots_count}) do not match fact.issue_snapshot "
            f"({fact_count}) for {snapshot_date}"
        )


def test_issue_trends_mart_matches_fact_snapshot():
    with _db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(snapshot_date_sk) FROM fact.issue_snapshot")
        row = cursor.fetchone()
        snapshot_date_sk = row[0] if row else None
        if snapshot_date_sk is None:
            pytest.skip("No fact.issue_snapshot data available")

        cursor.execute(
            """
            SELECT SUM(open_issues + closed_issues)
            FROM mart.v_issue_trends
            WHERE snapshot_date_sk = ?
            """,
            (snapshot_date_sk,),
        )
        mart_total = cursor.fetchone()[0] or 0

        cursor.execute(
            "SELECT COUNT(*) FROM fact.issue_snapshot WHERE snapshot_date_sk = ?",
            (snapshot_date_sk,),
        )
        fact_total = cursor.fetchone()[0]

        assert mart_total == fact_total, (
            f"mart.v_issue_trends total ({mart_total}) does not match fact.issue_snapshot "
            f"({fact_total}) for snapshot_date_sk={snapshot_date_sk}"
        )
