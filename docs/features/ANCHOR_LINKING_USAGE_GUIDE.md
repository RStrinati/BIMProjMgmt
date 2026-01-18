# Anchor Linking - Usage Patterns & Examples

**Guide**: How to use IssueAnchorLinks for service/review/item blocking

---

## Quick Reference

### Database Schema

```sql
-- Create a link: Issue blocks Service
INSERT INTO dbo.IssueAnchorLinks (
    project_id,
    issue_key_hash,
    anchor_type,
    service_id,
    link_role,
    note
) VALUES (
    @project_id,
    @issue_key_hash,  -- from vw_Issues_Reconciled
    'service',
    @service_id,
    'blocks',
    'Blocking deployment due to critical crash'
);

-- Query: Get all blockers for a service
SELECT ir.display_id, ir.title, ir.priority_normalized, ir.status_normalized
FROM dbo.IssueAnchorLinks ial
JOIN dbo.vw_Issues_Reconciled ir ON ial.issue_key_hash = ir.issue_key_hash
WHERE ial.anchor_type = 'service'
  AND ial.service_id = @service_id
  AND ial.link_role = 'blocks'
  AND ial.deleted_at IS NULL;
```

---

## Use Cases

### 1. Service Blocking

**Scenario**: A critical issue blocks service deployment

```sql
-- Find issue by display_id
DECLARE @issue_hash VARBINARY(32)
SELECT @issue_hash = issue_key_hash 
FROM dbo.vw_Issues_Reconciled 
WHERE display_id = 'ACC-924';

-- Link to service
INSERT INTO dbo.IssueAnchorLinks (
    project_id, issue_key_hash, anchor_type, service_id, link_role
) VALUES (
    1, @issue_hash, 'service', 42, 'blocks'
);

-- UI: Display badge on service details
-- "🔴 1 Blocker - ACC-924: Fix crash in HVAC zone calculation"
```

### 2. Review Evidence

**Scenario**: Issues provide evidence of work done in a review cycle

```sql
-- Link multiple issues as evidence
INSERT INTO dbo.IssueAnchorLinks (
    project_id, issue_key_hash, anchor_type, review_id, link_role, note
) VALUES
    (1, @hash1, 'review', 5, 'evidence', 'Resolved clash'),
    (1, @hash2, 'review', 5, 'evidence', 'Fixed MEP coordination'),
    (1, @hash3, 'review', 5, 'evidence', 'Updated model');

-- UI: Show "3 items closed in this review cycle"
```

### 3. Item Related Issues

**Scenario**: Issues relate to a specific scope item

```sql
-- Link issue to item
INSERT INTO dbo.IssueAnchorLinks (
    project_id, issue_key_hash, anchor_type, item_id, link_role
) VALUES (
    1, @hash, 'item', 99, 'relates'
);

-- Query: All related issues for scope item
SELECT ir.display_id, ir.title, ir.status_normalized
FROM dbo.vw_IssueAnchorLinks_Expanded ial
WHERE ial.anchor_type = 'item'
  AND ial.item_id = 99
  AND link_role = 'relates'
  AND link_deleted_at IS NULL;
```

---

## Common Queries

### Get blocker badge count

```sql
SELECT 
    total_linked,
    open_count,
    critical_count
FROM dbo.vw_AnchorBlockerCounts
WHERE anchor_type = 'service' AND service_id = 42;
```

### Get all open blockers for anchor

```sql
SELECT 
    display_id,
    title,
    priority_normalized,
    status_normalized,
    assignee_user_key
FROM dbo.vw_IssueAnchorLinks_Expanded
WHERE anchor_type = 'service'
  AND service_id = 42
  AND link_role = 'blocks'
  AND link_deleted_at IS NULL
  AND status_normalized IN ('Open', 'In Progress', 'In Review')
ORDER BY priority_normalized DESC, issue_updated_at DESC;
```

### Get issues by role type

```sql
-- All "blocks" relationships
SELECT * FROM dbo.IssueAnchorLinks
WHERE link_role = 'blocks' AND deleted_at IS NULL;

-- All "evidence" relationships  
SELECT * FROM dbo.IssueAnchorLinks
WHERE link_role = 'evidence' AND deleted_at IS NULL;

-- All "relates" relationships
SELECT * FROM dbo.IssueAnchorLinks
WHERE link_role = 'relates' AND deleted_at IS NULL;
```

### Search issues that block a specific service

```sql
DECLARE @service_id INT = 42;

SELECT 
    ial.link_id,
    ir.display_id,
    ir.title,
    ir.priority_normalized,
    ir.status_normalized,
    ir.updated_at,
    ial.note
FROM dbo.vw_IssueAnchorLinks_Expanded ial
WHERE ial.anchor_type = 'service'
  AND ial.service_id = @service_id
  AND ial.link_role = 'blocks'
  AND ial.link_deleted_at IS NULL
ORDER BY ir.priority_normalized DESC;
```

---

## Data Modification Examples

### Add Link

```sql
DECLARE @issue_key_hash VARBINARY(32)
DECLARE @project_id INT

-- Get issue hash by display_id
SELECT @issue_key_hash = issue_key_hash, @project_id = CAST(project_id AS INT)
FROM dbo.vw_Issues_Reconciled
WHERE display_id = 'ACC-924'

IF @issue_key_hash IS NOT NULL
BEGIN
    INSERT INTO dbo.IssueAnchorLinks (
        project_id, issue_key_hash, anchor_type, service_id, link_role, note, created_by
    ) VALUES (
        @project_id, @issue_key_hash, 'service', 42, 'blocks',
        'Critical crash preventing deployment', 'user@company.com'
    )
END
```

### Update Link Note

```sql
UPDATE dbo.IssueAnchorLinks
SET note = 'Fixed in build 2.5.1 - pending release'
WHERE link_id = 123;
```

### Soft Delete Link

```sql
UPDATE dbo.IssueAnchorLinks
SET deleted_at = SYSUTCDATETIME()
WHERE link_id = 123;
```

### Restore (Undelete) Link

```sql
UPDATE dbo.IssueAnchorLinks
SET deleted_at = NULL
WHERE link_id = 123;
```

### Hard Delete (Use Sparingly)

```sql
DELETE FROM dbo.IssueAnchorLinks
WHERE link_id = 123;
```

---

## Python Backend Implementation

### Database Helper Functions

```python
# Add to database.py
from typing import Optional, List, Dict
from datetime import datetime

def add_issue_anchor_link(
    project_id: int,
    issue_display_id: str,
    anchor_type: str,  # 'service', 'review', 'item'
    anchor_id: int,
    link_role: str = 'blocks',  # 'blocks', 'evidence', 'relates'
    note: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Dict[str, any]:
    """Add a link between an issue and an anchor."""
    
    try:
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            
            # Get issue hash by display_id
            cursor.execute("""
                SELECT issue_key_hash FROM dbo.vw_Issues_Reconciled
                WHERE display_id = ? AND project_id = ?
            """, (issue_display_id, str(project_id)))
            
            result = cursor.fetchone()
            if not result:
                return {"error": "Issue not found", "display_id": issue_display_id}
            
            issue_key_hash = result[0]
            
            # Map anchor_type to ID column
            id_col = {
                'service': 'service_id',
                'review': 'review_id',
                'item': 'item_id'
            }.get(anchor_type)
            
            if not id_col:
                return {"error": f"Invalid anchor_type: {anchor_type}"}
            
            # Insert link
            cursor.execute(f"""
                INSERT INTO dbo.IssueAnchorLinks (
                    project_id, issue_key_hash, anchor_type, {id_col},
                    link_role, note, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (project_id, issue_key_hash, anchor_type, anchor_id,
                  link_role, note, created_by))
            
            conn.commit()
            
            return {
                "status": "success",
                "link_id": cursor.lastrowid,
                "issue": issue_display_id,
                "anchor": f"{anchor_type}:{anchor_id}"
            }
    
    except Exception as e:
        logger.exception(f"Error adding anchor link: {e}")
        return {"error": str(e)}


def get_anchor_blockers(anchor_type: str, anchor_id: int) -> Dict[str, any]:
    """Get all blocker issues for an anchor with badge counts."""
    
    try:
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            
            # Get counts
            cursor.execute("""
                SELECT total_linked, open_count, closed_count, critical_count, high_count
                FROM dbo.vw_AnchorBlockerCounts
                WHERE anchor_type = ? AND (
                    (anchor_type = 'service' AND service_id = ?)
                    OR (anchor_type = 'review' AND review_id = ?)
                    OR (anchor_type = 'item' AND item_id = ?)
                )
            """, (anchor_type, anchor_id, anchor_id, anchor_id))
            
            counts_row = cursor.fetchone()
            counts = {
                'total': counts_row[0] or 0,
                'open': counts_row[1] or 0,
                'closed': counts_row[2] or 0,
                'critical': counts_row[3] or 0,
                'high': counts_row[4] or 0,
            } if counts_row else {'total': 0, 'open': 0, 'closed': 0, 'critical': 0, 'high': 0}
            
            # Get issue details
            cursor.execute("""
                SELECT 
                    display_id, title, priority_normalized, status_normalized,
                    assignee_user_key, updated_at, note
                FROM dbo.vw_IssueAnchorLinks_Expanded
                WHERE anchor_type = ? AND (
                    (anchor_type = 'service' AND service_id = ?)
                    OR (anchor_type = 'review' AND review_id = ?)
                    OR (anchor_type = 'item' AND item_id = ?)
                )
                AND link_role = 'blocks'
                AND link_deleted_at IS NULL
                ORDER BY priority_normalized DESC, issue_updated_at DESC
            """, (anchor_type, anchor_id, anchor_id, anchor_id))
            
            columns = ['display_id', 'title', 'priority', 'status', 'assignee', 'updated_at', 'note']
            issues = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return {
                "anchor_type": anchor_type,
                "anchor_id": anchor_id,
                "badges": counts,
                "issues": issues
            }
    
    except Exception as e:
        logger.exception(f"Error getting anchor blockers: {e}")
        return {"error": str(e)}


def soft_delete_link(link_id: int) -> Dict[str, any]:
    """Soft delete a link (sets deleted_at)."""
    
    try:
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE dbo.IssueAnchorLinks
                SET deleted_at = SYSUTCDATETIME()
                WHERE link_id = ? AND deleted_at IS NULL
            """, (link_id,))
            
            conn.commit()
            return {"status": "success", "link_id": link_id}
    
    except Exception as e:
        logger.exception(f"Error deleting link: {e}")
        return {"error": str(e)}
```

### Flask API Routes

```python
# Add to backend/app.py
from database import add_issue_anchor_link, get_anchor_blockers, soft_delete_link

@app.route('/api/anchors/<anchor_type>/<int:anchor_id>/blockers', methods=['GET'])
def get_anchor_blockers_endpoint(anchor_type, anchor_id):
    """GET /api/anchors/service/42/blockers"""
    result = get_anchor_blockers(anchor_type, anchor_id)
    return jsonify(result)

@app.route('/api/anchor-links', methods=['POST'])
def create_anchor_link():
    """POST /api/anchor-links
    Body: {
        "project_id": 1,
        "issue_display_id": "ACC-924",
        "anchor_type": "service",
        "anchor_id": 42,
        "link_role": "blocks",
        "note": "Blocking deployment"
    }
    """
    data = request.get_json()
    result = add_issue_anchor_link(
        project_id=data['project_id'],
        issue_display_id=data['issue_display_id'],
        anchor_type=data['anchor_type'],
        anchor_id=data['anchor_id'],
        link_role=data.get('link_role', 'blocks'),
        note=data.get('note'),
        created_by=get_current_user()  # Implement as needed
    )
    return jsonify(result), 201 if 'status' in result else 400

@app.route('/api/anchor-links/<int:link_id>', methods=['DELETE'])
def delete_anchor_link(link_id):
    """DELETE /api/anchor-links/123"""
    result = soft_delete_link(link_id)
    return jsonify(result)
```

---

## React Component Example

```jsx
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

export function AnchorBlockerBadge({ anchorType, anchorId }) {
  const { data, isLoading } = useQuery({
    queryKey: ['anchor-blockers', anchorType, anchorId],
    queryFn: () =>
      fetch(`/api/anchors/${anchorType}/${anchorId}/blockers`)
        .then(r => r.json())
  });

  if (isLoading) return <span>Loading...</span>;
  if (!data) return null;

  const { badges, issues } = data;
  const isBlocked = badges.open > 0;

  return (
    <div className="blocker-badge">
      <span className={isBlocked ? 'badge-critical' : 'badge-clear'}>
        {isBlocked ? '🔴' : '✅'} 
        {badges.open} Open / {badges.total} Total Blockers
      </span>
      
      {isBlocked && (
        <details>
          <summary>Show {badges.open} Blockers</summary>
          <ul className="issue-list">
            {issues.map(issue => (
              <li key={issue.display_id} className={`priority-${issue.priority}`}>
                <strong>{issue.display_id}</strong>: {issue.title}
                <span className="status">{issue.status}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
```

---

## Constraint Validation

All insertions are validated by database constraints:

```sql
-- Valid: issue blocks service
INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, service_id, link_role)
VALUES (1, 0x..., 'service', 42, 'blocks');  ✅

-- Invalid: service AND review IDs both set
INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, service_id, review_id, link_role)
VALUES (1, 0x..., 'service', 42, 5, 'blocks');  ❌ CONSTRAINT VIOLATION

-- Invalid: anchor_type='service' but service_id is NULL
INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, review_id, link_role)
VALUES (1, 0x..., 'service', 5, 'blocks');  ❌ CONSTRAINT VIOLATION

-- Valid: multiple link roles allowed (not unique by itself)
INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, service_id, link_role)
VALUES (1, 0x..., 'service', 42, 'blocks');  ✅

INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, service_id, link_role)
VALUES (1, 0x..., 'service', 42, 'evidence');  ✅
```

---

**Version**: 1.0  
**Status**: Ready for Integration  
**Last Updated**: January 2026
