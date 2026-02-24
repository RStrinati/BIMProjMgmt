from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from constants import schema as S
from database import get_db_connection


@dataclass(frozen=True)
class OverviewSummaryResult:
    summary_text: str
    summary_json: str
    summary_month: str


def _parse_month(value: Optional[str]) -> Tuple[date, date, str]:
    if value:
        parsed = datetime.strptime(value, "%Y-%m")
        month_start = date(parsed.year, parsed.month, 1)
    else:
        today = date.today()
        month_start = date(today.year, today.month, 1)

    if month_start.month == 12:
        next_month = date(month_start.year + 1, 1, 1)
    else:
        next_month = date(month_start.year, month_start.month + 1, 1)
    return month_start, next_month, month_start.strftime("%Y-%m")


def _format_month_label(month_value: str) -> str:
    parsed = datetime.strptime(month_value, "%Y-%m")
    return parsed.strftime("%B %Y")


def _format_currency(amount: float) -> str:
    return f"${amount:,.2f}"


def _fetch_review_labels_for_month(cursor, project_id: int, month_value: str) -> Dict[str, int]:
    cursor.execute(
        f"""
        SELECT
            COALESCE(NULLIF(LTRIM(RTRIM(sr.{S.ServiceReviews.DELIVERABLES})), ''), ps.{S.ProjectServices.SERVICE_NAME} + ' Review') AS label,
            COUNT(*) AS item_count
        FROM {S.ServiceReviews.TABLE} sr
        INNER JOIN {S.ProjectServices.TABLE} ps
            ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
        WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
          AND COALESCE(
              sr.{S.ServiceReviews.INVOICE_MONTH_FINAL},
              sr.{S.ServiceReviews.INVOICE_MONTH_OVERRIDE},
              sr.{S.ServiceReviews.INVOICE_MONTH_AUTO},
              CONVERT(char(7), sr.{S.ServiceReviews.DUE_DATE}, 126),
              CONVERT(char(7), sr.{S.ServiceReviews.PLANNED_DATE}, 126)
          ) = ?
          AND LOWER(ISNULL(sr.{S.ServiceReviews.STATUS}, '')) <> 'cancelled'
        GROUP BY
            COALESCE(NULLIF(LTRIM(RTRIM(sr.{S.ServiceReviews.DELIVERABLES})), ''), ps.{S.ProjectServices.SERVICE_NAME} + ' Review')
        """,
        (project_id, month_value),
    )
    return {row[0]: int(row[1]) for row in cursor.fetchall() if row[0]}


def _fetch_item_labels_for_month(
    cursor,
    project_id: int,
    month_start: date,
    month_end: date,
) -> Dict[str, int]:
    cursor.execute(
        f"""
        SELECT
            si.{S.ServiceItems.TITLE} AS label,
            COUNT(*) AS item_count
        FROM {S.ServiceItems.TABLE} si
        INNER JOIN {S.ProjectServices.TABLE} ps
            ON si.{S.ServiceItems.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
        WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
          AND COALESCE(si.{S.ServiceItems.DUE_DATE}, si.{S.ServiceItems.PLANNED_DATE}) >= ?
          AND COALESCE(si.{S.ServiceItems.DUE_DATE}, si.{S.ServiceItems.PLANNED_DATE}) < ?
          AND LOWER(ISNULL(si.{S.ServiceItems.STATUS}, '')) <> 'cancelled'
        GROUP BY si.{S.ServiceItems.TITLE}
        """,
        (project_id, month_start, month_end),
    )
    return {row[0]: int(row[1]) for row in cursor.fetchall() if row[0]}


def _fetch_scope_remaining(cursor, project_id: int) -> Dict[str, int]:
    remaining: Dict[str, int] = {}

    cursor.execute(
        f"""
        SELECT
            COALESCE(NULLIF(LTRIM(RTRIM(sr.{S.ServiceReviews.DELIVERABLES})), ''), ps.{S.ProjectServices.SERVICE_NAME} + ' Review') AS label,
            COUNT(*) AS item_count
        FROM {S.ServiceReviews.TABLE} sr
        INNER JOIN {S.ProjectServices.TABLE} ps
            ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
        WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
          AND LOWER(ISNULL(sr.{S.ServiceReviews.STATUS}, '')) NOT IN ('completed', 'closed', 'report_issued', 'ready', 'cancelled')
        GROUP BY
            COALESCE(NULLIF(LTRIM(RTRIM(sr.{S.ServiceReviews.DELIVERABLES})), ''), ps.{S.ProjectServices.SERVICE_NAME} + ' Review')
        """,
        (project_id,),
    )
    for row in cursor.fetchall():
        if row[0]:
            remaining[row[0]] = remaining.get(row[0], 0) + int(row[1])

    cursor.execute(
        f"""
        SELECT
            si.{S.ServiceItems.TITLE} AS label,
            COUNT(*) AS item_count
        FROM {S.ServiceItems.TABLE} si
        INNER JOIN {S.ProjectServices.TABLE} ps
            ON si.{S.ServiceItems.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
        WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
          AND LOWER(ISNULL(si.{S.ServiceItems.STATUS}, '')) NOT IN ('completed', 'cancelled')
        GROUP BY si.{S.ServiceItems.TITLE}
        """,
        (project_id,),
    )
    for row in cursor.fetchall():
        if row[0]:
            remaining[row[0]] = remaining.get(row[0], 0) + int(row[1])

    return remaining


def _fetch_ready_to_bill_amount(
    cursor,
    project_id: int,
    month_value: str,
    month_start: date,
    month_end: date,
) -> float:
    ready_amount = 0.0

    cursor.execute(
        """
        SELECT ready_amount
        FROM vw_invoice_pipeline_by_project_month
        WHERE project_id = ? AND invoice_month = ?
        """,
        (project_id, month_value),
    )
    row = cursor.fetchone()
    if row and row[0] is not None:
        ready_amount += float(row[0])

    cursor.execute(
        f"""
        SELECT
            SUM(COALESCE({S.ServiceItems.FEE_AMOUNT}, {S.ServiceItems.BILLED_AMOUNT}, 0))
        FROM {S.ServiceItems.TABLE} si
        INNER JOIN {S.ProjectServices.TABLE} ps
            ON si.{S.ServiceItems.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
        WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
          AND COALESCE(si.{S.ServiceItems.DUE_DATE}, si.{S.ServiceItems.PLANNED_DATE}) >= ?
          AND COALESCE(si.{S.ServiceItems.DUE_DATE}, si.{S.ServiceItems.PLANNED_DATE}) < ?
          AND LOWER(ISNULL(si.{S.ServiceItems.STATUS}, '')) IN ('completed', 'ready')
          AND ISNULL(si.{S.ServiceItems.IS_BILLED}, 0) = 0
        """,
        (project_id, month_start, month_end),
    )
    row = cursor.fetchone()
    if row and row[0] is not None:
        ready_amount += float(row[0])

    return ready_amount


def _fetch_completion_dates(cursor, project_id: int) -> Dict[str, Optional[str]]:
    cursor.execute(
        f"""
        SELECT TOP 1 ps.{S.ProjectServices.PHASE}, ps.{S.ProjectServices.END_DATE}
        FROM {S.ProjectServices.TABLE} ps
        WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
          AND ps.{S.ProjectServices.END_DATE} IS NOT NULL
        ORDER BY ps.{S.ProjectServices.END_DATE} DESC
        """,
        (project_id,),
    )
    phase_row = cursor.fetchone()
    phase_label = phase_row[0] if phase_row else None
    phase_end = phase_row[1] if phase_row else None

    cursor.execute(
        f"""
        SELECT p.{S.Projects.END_DATE}
        FROM {S.Projects.TABLE} p
        WHERE p.{S.Projects.ID} = ?
        """,
        (project_id,),
    )
    project_row = cursor.fetchone()
    project_end = project_row[0] if project_row else None

    def _fmt(value: Optional[date]) -> Optional[str]:
        if not value:
            return None
        if isinstance(value, datetime):
            value = value.date()
        return value.strftime("%B %Y")

    return {
        "phase_label": phase_label,
        "phase_end": _fmt(phase_end),
        "project_end": _fmt(project_end),
    }


def generate_project_overview_summary(
    project_id: int,
    target_month: Optional[str] = None,
) -> OverviewSummaryResult:
    month_start, month_end, month_value = _parse_month(target_month)
    month_label = _format_month_label(month_value)

    with get_db_connection("ProjectManagement") as conn:
        cursor = conn.cursor()

        review_labels = _fetch_review_labels_for_month(cursor, project_id, month_value)
        item_labels = _fetch_item_labels_for_month(cursor, project_id, month_start, month_end)

        current_activities: Dict[str, int] = {}
        for label, count in {**review_labels, **item_labels}.items():
            current_activities[label] = current_activities.get(label, 0) + count

        ready_amount = _fetch_ready_to_bill_amount(cursor, project_id, month_value, month_start, month_end)
        scope_remaining = _fetch_scope_remaining(cursor, project_id)
        completion = _fetch_completion_dates(cursor, project_id)

    def _sorted_entries(entries: Dict[str, int]) -> List[Dict[str, Any]]:
        return [
            {"label": label, "count": count}
            for label, count in sorted(entries.items(), key=lambda item: (-item[1], item[0].lower()))
        ]

    summary_payload = {
        "month": month_value,
        "current_activities": _sorted_entries(current_activities),
        "billing": {
            "ready_amount": round(ready_amount, 2),
            "ready_month": month_value,
        },
        "scope_remaining": _sorted_entries(scope_remaining),
        "estimated_completion": completion,
    }

    summary_lines: List[str] = []
    summary_lines.append(f"Current activities for month ({month_label}):")
    if summary_payload["current_activities"]:
        for entry in summary_payload["current_activities"]:
            summary_lines.append(f"- {entry['count']} x {entry['label']}")
    else:
        summary_lines.append("- None")

    summary_lines.append("")
    summary_lines.append("Billing:")
    if ready_amount > 0:
        summary_lines.append(f"- {_format_currency(ready_amount)} to bill for {month_label}")
    else:
        summary_lines.append(f"- No billable items ready for {month_label}")

    summary_lines.append("")
    summary_lines.append("Scope remaining:")
    if summary_payload["scope_remaining"]:
        for entry in summary_payload["scope_remaining"]:
            summary_lines.append(f"- {entry['count']} x {entry['label']}")
    else:
        summary_lines.append("- None")

    summary_lines.append("")
    summary_lines.append("Est. project completion:")
    if completion.get("phase_label") and completion.get("phase_end"):
        summary_lines.append(f"- {completion['phase_label']}: {completion['phase_end']}")
    if completion.get("project_end"):
        summary_lines.append(f"- Project completion: {completion['project_end']}")
    if not completion.get("phase_label") and not completion.get("project_end"):
        summary_lines.append("- Not scheduled")

    summary_text = "\n".join(summary_lines)
    summary_json = json.dumps(summary_payload, default=str)

    return OverviewSummaryResult(
        summary_text=summary_text,
        summary_json=summary_json,
        summary_month=month_value,
    )
