# Master Users Schema Reference

**Date**: February 2026  
**Migration File**: `sql/migrations/20260213_add_master_user_identities.sql`  
**Feature**: User identity consolidation and project assignment

---

## Table Structure

### 📌 `dbo.master_users`
**Purpose**: Single record per email address, consolidating users across ACC and Revizto.

```sql
CREATE TABLE dbo.master_users (
    master_user_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    email_normalized NVARCHAR(255) NOT NULL,
    display_name NVARCHAR(255) NULL,
    company NVARCHAR(255) NULL,
    status NVARCHAR(64) NULL,
    last_active_at DATETIME2 NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT UQ_master_users_email UNIQUE (email_normalized)
);

CREATE INDEX IX_master_users_last_active ON dbo.master_users(last_active_at);
```

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| `master_user_id` | INT | PK, IDENTITY | Surrogate key for user record |
| `email_normalized` | NVARCHAR(255) | UNIQUE NOT NULL | Normalized email (lowercase); used for deduplication |
| `display_name` | NVARCHAR(255) | NULL | Combined display name (sourced from most recent update) |
| `company` | NVARCHAR(255) | NULL | Consolidated company (sourced from identities) |
| `status` | NVARCHAR(64) | NULL | Aggregated status (e.g., 'active', 'inactive', 'archived') |
| `last_active_at` | DATETIME2 | NULL | Most recent activity timestamp across all sources |
| `created_at` | DATETIME2 | DEFAULT SYSUTCDATETIME() | Record creation time |
| `updated_at` | DATETIME2 | DEFAULT SYSUTCDATETIME() | Last update time |

**Indexes**:
- `IX_master_users_last_active` — Enables sorting by activity; identifies inactive users

**Notes**:
- Email is normalized (lowercased, whitespace trimmed) to ensure uniqueness across sources
- Fields like `display_name` and `company` are sourced from the most recent `master_user_identities` update
- `status` can be NULL if no identities exist yet

---

### 📌 `dbo.master_user_identities`
**Purpose**: Store each user's identity in each source system (ACC, Revizto, etc.).

```sql
CREATE TABLE dbo.master_user_identities (
    master_user_id INT NOT NULL,
    source_system NVARCHAR(32) NOT NULL,
    source_user_id NVARCHAR(100) NOT NULL,
    email_normalized NVARCHAR(255) NULL,
    name NVARCHAR(255) NULL,
    company NVARCHAR(255) NULL,
    role NVARCHAR(255) NULL,
    status NVARCHAR(64) NULL,
    last_active_at DATETIME2 NULL,
    user_key NVARCHAR(160) NULL,
    synced_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_master_user_identities PRIMARY KEY (source_system, source_user_id),
    CONSTRAINT FK_master_user_identities_master_users 
        FOREIGN KEY (master_user_id) REFERENCES dbo.master_users(master_user_id)
);

CREATE INDEX IX_master_user_identities_email ON dbo.master_user_identities(email_normalized);
CREATE INDEX IX_master_user_identities_master_user_id ON dbo.master_user_identities(master_user_id);
```

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| `master_user_id` | INT | FK, NOT NULL | Link to consolidated `master_users` record |
| `source_system` | NVARCHAR(32) | PK, NOT NULL | Source platform code ('ACC', 'Revizto') |
| `source_user_id` | NVARCHAR(100) | PK, NOT NULL | Platform-native user ID (e.g., ACC user ID or Revizto user ID) |
| `email_normalized` | NVARCHAR(255) | NULL | Email in this source (used for matching during sync) |
| `name` | NVARCHAR(255) | NULL | User's full name as stored in this source |
| `company` | NVARCHAR(255) | NULL | User's company from this source |
| `role` | NVARCHAR(255) | NULL | Role/title from this source |
| `status` | NVARCHAR(64) | NULL | User status in this source (e.g., 'active', 'deactivated') |
| `last_active_at` | DATETIME2 | NULL | Last activity timestamp in this source |
| `user_key` | NVARCHAR(160) | NULL | Composite key for tracking (usually `email:source`) |
| `synced_at` | DATETIME2 | DEFAULT SYSUTCDATETIME() | When this identity was last synced/updated |

**Primary Key**: `(source_system, source_user_id)` — Ensures one identity record per user per source  
**Indexes**:
- `IX_master_user_identities_email` — Fast lookups by email during sync
- `IX_master_user_identities_master_user_id` — Retrieve all identities for a master user

**Notes**:
- Multiple identities can point to the same `master_user_id` (same email across sources)
- Email matching is case-insensitive and normalized
- `synced_at` tracks when the foreign system was last queried for this user

---

### 📌 `dbo.master_user_flags`
**Purpose**: Store project-level or system-level user properties (optional, for flags set at application level).

```sql
-- Optional table (created separately from migration)
CREATE TABLE dbo.master_user_flags (
    master_user_id INT NOT NULL,
    invited_to_bim_meetings BIT NOT NULL DEFAULT 0,
    is_watcher BIT NOT NULL DEFAULT 0,
    is_assignee BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_master_user_flags PRIMARY KEY (master_user_id),
    CONSTRAINT FK_master_user_flags_master_users 
        FOREIGN KEY (master_user_id) REFERENCES dbo.master_users(master_user_id)
);
```

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| `master_user_id` | INT | PK, FK, NOT NULL | Link to master user record |
| `invited_to_bim_meetings` | BIT | NOT NULL, DEFAULT 0 | User is invited to project BIM meetings |
| `is_watcher` | BIT | NOT NULL, DEFAULT 0 | User watches issues/deliverables |
| `is_assignee` | BIT | NOT NULL, DEFAULT 0 | User is eligible for assignment |
| `created_at` | DATETIME2 | DEFAULT SYSUTCDATETIME() | Flag creation time |
| `updated_at` | DATETIME2 | DEFAULT SYSUTCDATETIME() | Last flag update time |

**Notes**:
- One-to-one with `master_users`
- Flags are application-level (set by PM or system logic), not imported from ACC/Revizto
- Default is 0 (false) for all flags

---

## Data Flow & Sync Process

### Sync Workflow (via `sync_master_users_from_sources()`)

```
1. Fetch ACC users (from importer cache or API)
2. Fetch Revizto users (from license member API)
3. For each ACC user:
     a. Normalize email
     b. Check if master_users record exists
     c. If not, INSERT into master_users
     d. Upsert into master_user_identities (source='ACC', source_user_id=...)
4. For each Revizto user:
     a. Normalize email
     b. Check if master_users record exists
     c. If not, INSERT into master_users
     d. Upsert into master_user_identities (source='Revizto', source_user_id=...)
5. Update master_users.updated_at, last_active_at from consolidated identities
6. Return sync summary (new count, updated count)
```

### Example: Single User Across Both Systems

**ACC User:**
```
name: John Architect
email: john@acme.example
company_id: ACC-123
role: Architect
```

**Revizto License Member:**
```
name: John A.
email: john@acme.example
license_type: Professional
role: Senior Architect
```

**Result in Database:**

`master_users` (1 row):
```
master_user_id: 1
email_normalized: john@acme.example
display_name: John Architect  (from most recent update)
company: NULL  (no company in Revizto identity)
status: active
last_active_at: 2026-02-13 14:30:00  (latest from identities)
```

`master_user_identities` (2 rows):
```
Row 1:
  master_user_id: 1
  source_system: ACC
  source_user_id: ACC-123
  email_normalized: john@acme.example
  name: John Architect
  role: Architect
  synced_at: 2026-02-13 10:00:00

Row 2:
  master_user_id: 1
  source_system: Revizto
  source_user_id: REV-456
  email_normalized: john@acme.example
  name: John A.
  role: Senior Architect
  synced_at: 2026-02-13 14:30:00
```

---

## Relationships & Dependencies

```
master_users (1) ──┬── (N) master_user_identities
                   └── (1) master_user_flags
```

### Foreign Key Relationships

1. **master_user_identities** → **master_users**
   - `master_user_identities.master_user_id` references `master_users.master_user_id`
   - ON DELETE: CASCADE (remove identities when master user deleted)

2. **master_user_flags** → **master_users**
   - `master_user_flags.master_user_id` references `master_users.master_user_id`
   - ON DELETE: CASCADE (remove flags when master user deleted)

### Related Tables (Import Data)

- **`acc_data_schema.dbo.vw_issues_expanded_pm`** — Source of ACC user data
- **`dbo.RevitLicenseMembers`** → **`dbo.revizto_license_members`** — Source of Revizto user data

---

## Query Examples

### Find All Users Created After Feb 1, 2026

```sql
SELECT m.master_user_id, m.email_normalized, m.display_name, COUNT(i.source_system) AS source_count
FROM master_users m
LEFT JOIN master_user_identities i ON m.master_user_id = i.master_user_id
WHERE m.created_at >= '2026-02-01'
GROUP BY m.master_user_id, m.email_normalized, m.display_name
ORDER BY m.created_at DESC;
```

### Get Users with Identities in Both ACC and Revizto

```sql
SELECT m.master_user_id, m.email_normalized, m.display_name
FROM master_users m
WHERE m.master_user_id IN (
    SELECT master_user_id
    FROM master_user_identities
    GROUP BY master_user_id
    HAVING COUNT(DISTINCT source_system) > 1
)
ORDER BY m.email_normalized;
```

### Find Inactive Users (No Activity in Past 30 Days)

```sql
SELECT m.master_user_id, m.email_normalized, m.display_name, m.last_active_at
FROM master_users m
WHERE m.last_active_at < DATEADD(DAY, -30, SYSUTCDATETIME())
ORDER BY m.last_active_at ASC;
```

### Get All Revizto-Only Users (Not in ACC)

```sql
SELECT m.master_user_id, m.email_normalized, m.display_name
FROM master_users m
WHERE NOT EXISTS (
    SELECT 1
    FROM master_user_identities i
    WHERE i.master_user_id = m.master_user_id
    AND i.source_system = 'ACC'
)
AND EXISTS (
    SELECT 1
    FROM master_user_identities i
    WHERE i.master_user_id = m.master_user_id
    AND i.source_system = 'Revizto'
);
```

---

## Constraints & Integrity Rules

| Rule | SQL Constraint | Enforcement |
|------|---|---|
| Email is unique | `UNIQUE(email_normalized)` | Database constraint |
| Identity per source | `PK (source_system, source_user_id)` | Database constraint |
| Identity links to master user | `FK master_user_id` | Database constraint |
| No orphaned identities | FK with NO ACTION | Database constraint |
| Email normalization | NVARCHAR uppercase logic in application | Application logic |

---

## Performance Tuning

### Index Usage

**Common Query Patterns**:
1. **Filter by email** → `IX_master_user_identities_email` is used
2. **Find identities for a master user** → `IX_master_user_identities_master_user_id` is used
3. **Sort by last activity** → `IX_master_users_last_active` is used

**Expected Performance**:
- Lookup by email: O(log n) via index
- Full list with sort: O(n log n) with page limit
- Sync operation (upsert 100-1000 records): < 5 seconds

### Recommended Statistics

```sql
-- Update stats before large reports
UPDATE STATISTICS master_users;
UPDATE STATISTICS master_user_identities;
UPDATE STATISTICS master_user_flags;
```

---

## Related Documentation

- [Master Users Feature Guide](../features/MASTER_USERS_FEATURE.md)
- [Database Connection Guide](../core/DATABASE_CONNECTION_GUIDE.md)
- [Data Imports Architecture](../integrations/DATA_IMPORTS_ARCHITECTURE.md)

---

## Migration History

- **2026-02-13**: Initial creation of `master_users`, `master_user_identities` tables
- **Future**: `master_user_flags` table (created on-demand or as separate migration)

