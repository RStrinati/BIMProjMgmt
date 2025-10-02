import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import pyodbc

try:
    # Reuse central DB connection settings
    from database import connect_to_db
except Exception:
    connect_to_db = None


def get_connection(db_name: Optional[str] = "ProjectManagement") -> Optional[pyodbc.Connection]:
    if connect_to_db is None:
        return None
    return connect_to_db(db_name)


def ensure_schema(conn: pyodbc.Connection) -> None:
    """Create required tables if they do not exist. Idempotent for SQL Server."""
    cursor = conn.cursor()

    # Helper to check table existence
    def table_exists(name: str) -> bool:
        cursor.execute(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=?",
            (name,)
        )
        return cursor.fetchone()[0] > 0

    # Libraries
    if not table_exists("DocLibrary"):
        cursor.execute(
            """
            CREATE TABLE dbo.DocLibrary(
                library_id     INT IDENTITY PRIMARY KEY,
                document_type  NVARCHAR(10) NOT NULL,
                jurisdiction   NVARCHAR(50) NULL,
                template_name  NVARCHAR(100) NOT NULL,
                version        NVARCHAR(50) NULL,
                created_at     DATETIME2 DEFAULT SYSDATETIME()
            );
            """
        )

    if not table_exists("DocLibrarySections"):
        cursor.execute(
            """
            CREATE TABLE dbo.DocLibrarySections(
                section_id    INT IDENTITY PRIMARY KEY,
                library_id    INT NOT NULL REFERENCES dbo.DocLibrary(library_id) ON DELETE CASCADE,
                code          NVARCHAR(50) NULL,
                title         NVARCHAR(400) NOT NULL,
                body_md       NVARCHAR(MAX) NULL,
                parent_code   NVARCHAR(50) NULL,
                ord           INT NOT NULL DEFAULT 0
            );
            """
        )

    if not table_exists("DocLibraryClauses"):
        cursor.execute(
            """
            CREATE TABLE dbo.DocLibraryClauses(
                clause_id     INT IDENTITY PRIMARY KEY,
                section_id    INT NOT NULL REFERENCES dbo.DocLibrarySections(section_id) ON DELETE CASCADE,
                code          NVARCHAR(50) NULL,
                title         NVARCHAR(400) NULL,
                body_md       NVARCHAR(MAX) NULL,
                optional      BIT NOT NULL DEFAULT 0,
                ord           INT NOT NULL DEFAULT 0
            );
            """
        )

    # Project documents
    if not table_exists("ProjectDocuments"):
        cursor.execute(
            """
            CREATE TABLE dbo.ProjectDocuments(
                project_document_id INT IDENTITY PRIMARY KEY,
                project_id          INT NOT NULL,
                library_id          INT NULL REFERENCES dbo.DocLibrary(library_id),
                title               NVARCHAR(300) NOT NULL,
                version             NVARCHAR(50) NULL,
                document_type       NVARCHAR(10) NOT NULL,
                status              NVARCHAR(30) NOT NULL DEFAULT 'draft',
                created_at          DATETIME2 DEFAULT SYSDATETIME()
            );
            """
        )

    if not table_exists("ProjectSections"):
        cursor.execute(
            """
            CREATE TABLE dbo.ProjectSections(
                project_section_id  INT IDENTITY PRIMARY KEY,
                project_document_id INT NOT NULL REFERENCES dbo.ProjectDocuments(project_document_id) ON DELETE CASCADE,
                original_section_id INT NULL REFERENCES dbo.DocLibrarySections(section_id),
                code                NVARCHAR(50) NULL,
                title               NVARCHAR(400) NOT NULL,
                body_md             NVARCHAR(MAX) NULL,
                ord                 INT NOT NULL DEFAULT 0
            );
            """
        )

    if not table_exists("ProjectClauses"):
        cursor.execute(
            """
            CREATE TABLE dbo.ProjectClauses(
                project_clause_id   INT IDENTITY PRIMARY KEY,
                project_section_id  INT NOT NULL REFERENCES dbo.ProjectSections(project_section_id) ON DELETE CASCADE,
                original_clause_id  INT NULL REFERENCES dbo.DocLibraryClauses(clause_id),
                code                NVARCHAR(50) NULL,
                title               NVARCHAR(400) NULL,
                body_md             NVARCHAR(MAX) NULL,
                optional            BIT NOT NULL DEFAULT 0,
                selected            BIT NOT NULL DEFAULT 1,
                ord                 INT NOT NULL DEFAULT 0
            );
            """
        )

    # Assignments
    if not table_exists("ClauseAssignments"):
        cursor.execute(
            """
            CREATE TABLE dbo.ClauseAssignments(
                assignment_id       INT IDENTITY PRIMARY KEY,
                project_clause_id   INT NOT NULL REFERENCES dbo.ProjectClauses(project_clause_id) ON DELETE CASCADE,
                discipline          NVARCHAR(50) NULL,
                owner               NVARCHAR(200) NULL,
                owner_email         NVARCHAR(200) NULL,
                due_date            DATE NULL,
                evidence_type       NVARCHAR(50) NULL,
                check_type          NVARCHAR(50) NULL,
                check_ref           NVARCHAR(200) NULL,
                params_json         NVARCHAR(MAX) NULL,
                status              NVARCHAR(20) NOT NULL DEFAULT 'Pending',
                last_run            DATETIME2 NULL,
                last_result         NVARCHAR(200) NULL
            );
            """
        )

    # Revisions + files
    if not table_exists("DocumentRevisions"):
        cursor.execute(
            """
            CREATE TABLE dbo.DocumentRevisions(
                revision_id         INT IDENTITY PRIMARY KEY,
                project_document_id INT NOT NULL REFERENCES dbo.ProjectDocuments(project_document_id) ON DELETE CASCADE,
                revision_no         INT NOT NULL,
                change_note         NVARCHAR(MAX) NULL,
                created_at          DATETIME2 DEFAULT SYSDATETIME(),
                created_by          NVARCHAR(200) NULL,
                status              NVARCHAR(30) NOT NULL DEFAULT 'Published'
            );
            """
        )

    if not table_exists("PublishedFiles"):
        cursor.execute(
            """
            CREATE TABLE dbo.PublishedFiles(
                file_id     INT IDENTITY PRIMARY KEY,
                revision_id INT NOT NULL REFERENCES dbo.DocumentRevisions(revision_id) ON DELETE CASCADE,
                path        NVARCHAR(500) NOT NULL,
                format      NVARCHAR(10) NOT NULL,
                created_at  DATETIME2 DEFAULT SYSDATETIME()
            );
            """
        )

    conn.commit()


def get_or_create_library(conn: pyodbc.Connection, document_type: str, template_name: str,
                          version: str = "1.0", jurisdiction: Optional[str] = None) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT TOP 1 library_id FROM dbo.DocLibrary
        WHERE document_type = ? AND template_name = ? AND ISNULL(version,'') = ISNULL(?, '') AND ISNULL(jurisdiction,'') = ISNULL(?, '')
        ORDER BY library_id DESC
        """,
        (document_type, template_name, version, jurisdiction)
    )
    row = cursor.fetchone()
    if row:
        return int(row[0])
    cursor.execute(
        "INSERT INTO dbo.DocLibrary(document_type, jurisdiction, template_name, version) VALUES (?, ?, ?, ?);",
        (document_type, jurisdiction, template_name, version)
    )
    conn.commit()
    cursor.execute("SELECT SCOPE_IDENTITY();")
    return int(cursor.fetchone()[0])


def seed_library_from_json(conn: pyodbc.Connection, library_id: int, seed: Dict) -> None:
    """Insert sections/clauses preserving order; idempotent per (library, code)."""
    cursor = conn.cursor()
    # Insert sections
    for sidx, sec in enumerate(seed.get("sections", []), start=1):
        code = sec.get("code")
        title = sec.get("title") or "Untitled"
        body = sec.get("body_md") or ""
        parent_code = sec.get("parent_code")

        # Check if exists
        cursor.execute(
            "SELECT section_id FROM dbo.DocLibrarySections WHERE library_id=? AND ISNULL(code,'')=ISNULL(?, '')",
            (library_id, code)
        )
        row = cursor.fetchone()
        if row:
            section_id = int(row[0])
        else:
            cursor.execute(
                "INSERT INTO dbo.DocLibrarySections(library_id, code, title, body_md, parent_code, ord) VALUES (?,?,?,?,?,?);",
                (library_id, code, title, body, parent_code, sidx)
            )
            cursor.execute("SELECT SCOPE_IDENTITY();")
            section_id = int(cursor.fetchone()[0])

        # Clauses
        for cidx, cl in enumerate(sec.get("clauses", []), start=1):
            ccode = cl.get("code")
            ctitle = cl.get("title")
            cbody = cl.get("body_md") or ""
            optional = 1 if cl.get("optional", False) else 0
            cursor.execute(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM dbo.DocLibraryClauses WHERE section_id=? AND ISNULL(code,'')=ISNULL(?, '')
                )
                INSERT INTO dbo.DocLibraryClauses(section_id, code, title, body_md, optional, ord)
                VALUES (?,?,?,?,?,?);
                """,
                (section_id, ccode, ctitle, cbody, optional, cidx)
            )
    conn.commit()


def fetch_library_sections(conn: pyodbc.Connection, document_type: str,
                           filters: Optional[Dict] = None) -> List[Dict]:
    cursor = conn.cursor()
    q = [
        "SELECT s.section_id, l.library_id, l.template_name, l.version, s.code, s.title, s.body_md, s.parent_code, s.ord",
        "FROM dbo.DocLibrarySections s",
        "JOIN dbo.DocLibrary l ON l.library_id = s.library_id",
        "WHERE l.document_type = ?"
    ]
    params = [document_type]
    if filters:
        if filters.get("jurisdiction"):
            q.append("AND ISNULL(l.jurisdiction,'')= ?")
            params.append(filters["jurisdiction"]) 
        if filters.get("template"):
            q.append("AND l.template_name = ?")
            params.append(filters["template"]) 
        if filters.get("version"):
            q.append("AND ISNULL(l.version,'') = ISNULL(?, '')")
            params.append(filters["version"]) 
    q.append("ORDER BY l.library_id DESC, s.ord ASC")
    cursor.execute(" ".join(q), params)
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]


def instantiate_document(conn: pyodbc.Connection, project_id: int, library_id: int,
                         title: str, version: str, document_type: str,
                         include_optional: bool = True,
                         selected_section_ids: Optional[List[int]] = None) -> int:
    cursor = conn.cursor()
    # Create document header
    cursor.execute(
        "INSERT INTO dbo.ProjectDocuments(project_id, library_id, title, version, document_type) VALUES (?,?,?,?,?);",
        (project_id, library_id, title, version, document_type)
    )
    cursor.execute("SELECT SCOPE_IDENTITY();")
    project_document_id = int(cursor.fetchone()[0])

    # Pull sections to include
    if selected_section_ids and len(selected_section_ids) > 0:
        cursor.execute(
            "SELECT section_id, code, title, body_md, ord FROM dbo.DocLibrarySections WHERE section_id IN (" + ",".join([str(int(i)) for i in selected_section_ids]) + ") ORDER BY ord"
        )
    else:
        cursor.execute(
            "SELECT section_id, code, title, body_md, ord FROM dbo.DocLibrarySections WHERE library_id=? ORDER BY ord",
            (library_id,)
        )
    sections = cursor.fetchall()

    # Copy sections
    sec_map: Dict[int, int] = {}
    for s in sections:
        section_id, code, title, body_md, ordval = s
        cursor.execute(
            "INSERT INTO dbo.ProjectSections(project_document_id, original_section_id, code, title, body_md, ord) VALUES (?,?,?,?,?,?);",
            (project_document_id, int(section_id), code, title, body_md, int(ordval or 0))
        )
        cursor.execute("SELECT SCOPE_IDENTITY();")
        sec_map[int(section_id)] = int(cursor.fetchone()[0])

    # Copy clauses for each section
    for lib_section_id, proj_section_id in sec_map.items():
        cursor.execute(
            "SELECT clause_id, code, title, body_md, optional, ord FROM dbo.DocLibraryClauses WHERE section_id=? ORDER BY ord",
            (lib_section_id,)
        )
        for clause_id, ccode, ctitle, cbody, optional, cord in cursor.fetchall():
            if not include_optional and optional:
                continue
            cursor.execute(
                """
                INSERT INTO dbo.ProjectClauses(project_section_id, original_clause_id, code, title, body_md, optional, selected, ord)
                VALUES (?,?,?,?,?,?,1,?);
                """,
                (proj_section_id, int(clause_id), ccode, ctitle, cbody, int(optional or 0), int(cord or 0))
            )

    conn.commit()
    return project_document_id


def list_project_document_sections(conn: pyodbc.Connection, project_document_id: int) -> List[Dict]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT project_section_id, code, title, ord FROM dbo.ProjectSections WHERE project_document_id=? ORDER BY ord",
        (project_document_id,)
    )
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]


def list_project_clauses(conn: pyodbc.Connection, project_document_id: int) -> List[Dict]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT pc.project_clause_id, ps.code AS section_code, pc.code, pc.title, pc.optional, pc.selected
        FROM dbo.ProjectClauses pc
        JOIN dbo.ProjectSections ps ON ps.project_section_id = pc.project_section_id
        WHERE ps.project_document_id=?
        ORDER BY ps.ord, pc.ord
        """,
        (project_document_id,)
    )
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]


def insert_assignment(conn: pyodbc.Connection, project_clause_id: int, discipline: str, owner: str,
                      due_date: Optional[str], evidence_type: str, check_type: str,
                      check_ref: Optional[str], params_json: Optional[str]) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO dbo.ClauseAssignments(project_clause_id, discipline, owner, due_date, evidence_type, check_type, check_ref, params_json)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (project_clause_id, discipline, owner, due_date, evidence_type, check_type, check_ref, params_json)
    )
    cursor.execute("SELECT SCOPE_IDENTITY();")
    conn.commit()
    return int(cursor.fetchone()[0])


def create_revision(conn: pyodbc.Connection, project_document_id: int, change_note: str, created_by: Optional[str] = None) -> int:
    cursor = conn.cursor()
    # Next revision number
    cursor.execute(
        "SELECT ISNULL(MAX(revision_no),0)+1 FROM dbo.DocumentRevisions WHERE project_document_id=?",
        (project_document_id,)
    )
    rev_no = int(cursor.fetchone()[0])
    cursor.execute(
        "INSERT INTO dbo.DocumentRevisions(project_document_id, revision_no, change_note, created_by) VALUES (?,?,?,?);",
        (project_document_id, rev_no, change_note, created_by)
    )
    cursor.execute("SELECT SCOPE_IDENTITY();")
    conn.commit()
    return int(cursor.fetchone()[0])


def add_published_file(conn: pyodbc.Connection, revision_id: int, path: str, fmt: str) -> int:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO dbo.PublishedFiles(revision_id, path, format) VALUES (?,?,?);",
        (revision_id, path, fmt)
    )
    cursor.execute("SELECT SCOPE_IDENTITY();")
    conn.commit()
    return int(cursor.fetchone()[0])


def approve_revision(conn: pyodbc.Connection, project_document_id: int, approved_by: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE dbo.DocumentRevisions
        SET status='Approved'
        WHERE project_document_id=? AND revision_id=(SELECT TOP 1 revision_id FROM dbo.DocumentRevisions WHERE project_document_id=? ORDER BY created_at DESC)
        """,
        (project_document_id, project_document_id)
    )
    conn.commit()
    return cursor.rowcount >= 1

