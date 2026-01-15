"""
Database functions for IssueAnchorLinks integration.

Provides query/mutation operations for bidirectional issue ↔ anchor linking.
Uses database_pool.py for connection management with proper timeout and cleanup.
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from database_pool import get_db_connection

logger = logging.getLogger(__name__)


def get_anchor_linked_issues(
    project_id: int,
    anchor_type: str,
    anchor_id: int,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "updated_at",
    sort_dir: str = "DESC",
    link_role_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Query linked issues for an anchor (review, service item, etc).
    
    Args:
        project_id: Project context
        anchor_type: 'review' | 'service' | 'item'
        anchor_id: ID of the anchor
        page: Pagination page (1-based)
        page_size: Records per page
        sort_by: Column to sort by (updated_at, priority_normalized, status_normalized)
        sort_dir: ASC or DESC
        link_role_filter: Optional filter for 'blocks', 'evidence', 'relates'
    
    Returns:
        Dict with pagination metadata and list of issue dicts
    """
    try:
        # Validate inputs
        if anchor_type not in ('review', 'service', 'item'):
            return {"error": f"Invalid anchor_type: {anchor_type}", "issues": []}
        
        if sort_by not in ('updated_at', 'priority_normalized', 'status_normalized'):
            sort_by = 'updated_at'
        
        sort_dir = 'DESC' if sort_dir.upper() == 'DESC' else 'ASC'
        
        # Build anchor filter
        anchor_col_map = {
            'review': 'ial.review_id',
            'service': 'ial.service_id',
            'item': 'ial.item_id'
        }
        anchor_col = anchor_col_map[anchor_type]
        anchor_filter = f"AND {anchor_col} = {anchor_id}"
        
        # Build link_role filter
        role_filter = ""
        if link_role_filter and link_role_filter in ('blocks', 'evidence', 'relates'):
            role_filter = f"AND ial.link_role = '{link_role_filter}'"
        
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            cursor.timeout = 30  # 30 second query timeout
            
            # Count total (without pagination)
            count_query = f"""
                SELECT COUNT(*)
                FROM dbo.vw_IssueAnchorLinks_Expanded ial
                WHERE ial.project_id = ?
                  AND ial.anchor_type = ?
                  {anchor_filter}
                  AND ial.link_deleted_at IS NULL
                  {role_filter}
            """
            cursor.execute(count_query, (project_id, anchor_type))
            total_count = cursor.fetchone()[0] or 0
            
            # Fetch paginated data
            offset = (page - 1) * page_size
            data_query = f"""
                SELECT
                    ial.link_id,
                    ial.issue_key,
                    ial.display_id,
                    ial.title,
                    ial.status_normalized,
                    ial.priority_normalized,
                    ial.discipline_normalized,
                    ial.assignee_user_key,
                    ial.issue_updated_at,
                    ial.link_role,
                    ial.note,
                    ial.link_created_at,
                    ial.link_created_by,
                    ial.source_system
                FROM dbo.vw_IssueAnchorLinks_Expanded ial
                WHERE ial.project_id = ?
                  AND ial.anchor_type = ?
                  {anchor_filter}
                  AND ial.link_deleted_at IS NULL
                  {role_filter}
                ORDER BY ial.{sort_by} {sort_dir}
                OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
            """
            
            cursor.execute(data_query, (project_id, anchor_type))
            rows = cursor.fetchall()
            
            issues = []
            for row in rows:
                issues.append({
                    'link_id': row[0],
                    'issue_key': row[1],
                    'display_id': row[2],
                    'title': row[3],
                    'status_normalized': row[4],
                    'priority_normalized': row[5],
                    'discipline_normalized': row[6],
                    'assignee_user_key': row[7],
                    'issue_updated_at': row[8].isoformat() if row[8] else None,
                    'link_role': row[9],
                    'note': row[10],
                    'link_created_at': row[11].isoformat() if row[11] else None,
                    'link_created_by': row[12],
                    'source_system': row[13],
                })
            
            return {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "issues": issues,
            }
    
    except Exception as e:
        logger.exception(f"Error fetching anchor linked issues: {e}")
        return {
            "error": str(e),
            "page": page,
            "page_size": page_size,
            "total_count": 0,
            "issues": [],
        }


def get_anchor_blocker_counts(
    project_id: int,
    anchor_type: str,
    anchor_id: int,
) -> Dict[str, Any]:
    """
    Get blocker badge counts for an anchor.
    
    Args:
        project_id: Project context
        anchor_type: 'review' | 'service' | 'item'
        anchor_id: ID of the anchor
    
    Returns:
        Dict with badge counts (total_linked, open_count, critical_count, etc.)
    """
    try:
        if anchor_type not in ('review', 'service', 'item'):
            return {"error": f"Invalid anchor_type: {anchor_type}"}
        
        # Map anchor type to column
        anchor_col_map = {
            'review': 'review_id',
            'service': 'service_id',
            'item': 'item_id'
        }
        anchor_col = anchor_col_map[anchor_type]
        
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            cursor.timeout = 10  # 10 second timeout for counts query
            
            query = f"""
                SELECT
                    COALESCE(total_linked, 0) as total_linked,
                    COALESCE(open_count, 0) as open_count,
                    COALESCE(closed_count, 0) as closed_count,
                    COALESCE(critical_count, 0) as critical_count,
                    COALESCE(high_count, 0) as high_count,
                    COALESCE(medium_count, 0) as medium_count
                FROM dbo.vw_AnchorBlockerCounts
                WHERE anchor_type = ?
                  AND {anchor_col} = ?
            """
            
            cursor.execute(query, (anchor_type, anchor_id))
            row = cursor.fetchone()
            
            if row:
                return {
                    'total_linked': row[0],
                    'open_count': row[1],
                    'closed_count': row[2],
                    'critical_count': row[3],
                    'high_count': row[4],
                    'medium_count': row[5],
                }
            else:
                # No links yet
                return {
                    'total_linked': 0,
                    'open_count': 0,
                    'closed_count': 0,
                    'critical_count': 0,
                    'high_count': 0,
                    'medium_count': 0,
                }
    
    except Exception as e:
        logger.exception(f"Error fetching anchor blocker counts: {e}")
        return {"error": str(e)}


def create_issue_anchor_link(
    project_id: int,
    issue_key_hash: bytes,
    anchor_type: str,
    anchor_id: int,
    link_role: str = 'blocks',
    note: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new issue-anchor link.
    
    Args:
        project_id: Project context
        issue_key_hash: Binary hash from Issues_Current.issue_key_hash
        anchor_type: 'review' | 'service' | 'item'
        anchor_id: ID of the anchor
        link_role: 'blocks' | 'evidence' | 'relates'
        note: Optional explanation
        created_by: User who created the link
    
    Returns:
        Dict with created link_id or error
    """
    try:
        if anchor_type not in ('review', 'service', 'item'):
            return {"error": f"Invalid anchor_type: {anchor_type}"}
        
        if link_role not in ('blocks', 'evidence', 'relates'):
            return {"error": f"Invalid link_role: {link_role}"}
        
        if not isinstance(issue_key_hash, bytes):
            return {"error": "issue_key_hash must be bytes"}
        
        # Map anchor type to column
        service_id = anchor_id if anchor_type == 'service' else None
        review_id = anchor_id if anchor_type == 'review' else None
        item_id = anchor_id if anchor_type == 'item' else None
        
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            cursor.timeout = 10
            
            insert_query = """
                INSERT INTO dbo.IssueAnchorLinks (
                    project_id, issue_key_hash, anchor_type, service_id, review_id, item_id,
                    link_role, note, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(
                insert_query,
                (project_id, issue_key_hash, anchor_type, service_id, review_id, item_id,
                 link_role, note, created_by)
            )
            conn.commit()
            
            # Get inserted link_id
            link_id = cursor.lastrowid
            
            return {
                'link_id': link_id,
                'anchor_type': anchor_type,
                'anchor_id': anchor_id,
                'link_role': link_role,
            }
    
    except Exception as e:
        logger.exception(f"Error creating issue anchor link: {e}")
        return {"error": str(e)}


def delete_issue_anchor_link(link_id: int) -> Dict[str, Any]:
    """
    Soft-delete an issue-anchor link.
    
    Args:
        link_id: ID of the link to delete
    
    Returns:
        Dict with success status or error
    """
    try:
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            cursor.timeout = 10
            
            update_query = """
                UPDATE dbo.IssueAnchorLinks
                SET deleted_at = SYSUTCDATETIME()
                WHERE link_id = ? AND deleted_at IS NULL
            """
            
            cursor.execute(update_query, (link_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                return {'success': True, 'link_id': link_id}
            else:
                return {'error': f'Link {link_id} not found or already deleted'}
    
    except Exception as e:
        logger.exception(f"Error deleting issue anchor link: {e}")
        return {"error": str(e)}


def get_issue_linked_anchors(
    project_id: int,
    issue_key_hash: bytes,
) -> Dict[str, Any]:
    """
    Get all anchors linked to a specific issue.
    
    Args:
        project_id: Project context
        issue_key_hash: Binary hash from Issues_Current.issue_key_hash
    
    Returns:
        Dict with list of anchors linked to the issue
    """
    try:
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            cursor.timeout = 10
            
            query = """
                SELECT
                    link_id,
                    anchor_type,
                    service_id,
                    review_id,
                    item_id,
                    link_role,
                    note,
                    created_at,
                    created_by
                FROM dbo.IssueAnchorLinks
                WHERE project_id = ?
                  AND issue_key_hash = ?
                  AND deleted_at IS NULL
                ORDER BY created_at DESC
            """
            
            cursor.execute(query, (project_id, issue_key_hash))
            rows = cursor.fetchall()
            
            anchors = []
            for row in rows:
                anchors.append({
                    'link_id': row[0],
                    'anchor_type': row[1],
                    'service_id': row[2],
                    'review_id': row[3],
                    'item_id': row[4],
                    'link_role': row[5],
                    'note': row[6],
                    'created_at': row[7].isoformat() if row[7] else None,
                    'created_by': row[8],
                })
            
            return {"anchors": anchors}
    
    except Exception as e:
        logger.exception(f"Error fetching issue linked anchors: {e}")
        return {"error": str(e), "anchors": []}
