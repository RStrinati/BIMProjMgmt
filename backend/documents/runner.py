from typing import List, Dict, Optional
from datetime import datetime

import pyodbc


def run_assignments(conn: pyodbc.Connection, project_document_id: int, scope: str = 'all', ids: Optional[List[int]] = None) -> Dict:
    """Run checks for assignments linked to a project document.
    Supports check_type='SQL_VIEW' where check_ref is a view or table.
    Params JSON may include: {"expect": ">=1"} or {"threshold": 1}
    """
    cur = conn.cursor()
    # Fetch assignments joined via ProjectClauses -> ProjectSections -> ProjectDocuments
    query = (
        """
        SELECT a.assignment_id, a.check_type, a.check_ref, a.params_json
        FROM dbo.ClauseAssignments a
        JOIN dbo.ProjectClauses pc ON pc.project_clause_id = a.project_clause_id
        JOIN dbo.ProjectSections ps ON ps.project_section_id = pc.project_section_id
        WHERE ps.project_document_id = ?
        """
    )
    params = [project_document_id]
    if scope == 'ids' and ids:
        query += " AND a.assignment_id IN (" + ",".join([str(int(i)) for i in ids]) + ")"
    cur.execute(query, params)
    rows = cur.fetchall()

    results = {"total": 0, "passed": 0, "failed": 0}
    for assignment_id, check_type, check_ref, params_json in rows:
        results["total"] += 1
        status = "Pending"
        last_result = None
        try:
            if check_type == 'SQL_VIEW':
                # Default: expect at least 1 row
                threshold = 1
                if params_json:
                    try:
                        import json
                        p = json.loads(params_json)
                        threshold = int(p.get('threshold', 1))
                    except Exception:
                        pass
                # Execute count
                cur2 = conn.cursor()
                cur2.execute(f"SELECT COUNT(1) FROM {check_ref}")
                count = int(cur2.fetchone()[0])
                status = 'Pass' if count >= threshold else 'Fail'
                last_result = f"{count} rows in {check_ref} (threshold {threshold})"
            else:
                status = 'N/A'
                last_result = 'Unsupported check type'
        except Exception as e:
            status = 'Fail'
            last_result = f"Error: {e}"

        # Update assignment status
        cur3 = conn.cursor()
        cur3.execute(
            "UPDATE dbo.ClauseAssignments SET status=?, last_run=SYSDATETIME(), last_result=? WHERE assignment_id=?",
            (status, last_result, int(assignment_id))
        )
        if status == 'Pass':
            results["passed"] += 1
        elif status == 'Fail':
            results["failed"] += 1

    conn.commit()
    return results

