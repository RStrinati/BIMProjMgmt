# Migration & Schema Documentation

Historical migration and data-flow records for backend/database evolution.

## Active Documents
- `DB_MIGRATION_PHASE4_COMPLETE.md` — final connection pooling migration state
- `DATABASE_OPTIMIZATION_REPORT.md` — performance and optimization findings
- `SCHEMA_FIX_COMPLETE.md` — schema correction notes
- `DATA_FLOW_EXECUTIVE_SUMMARY.md` and `DATA_FLOW_INDEX.md` — data-flow orientation
- `MASTER_USERS_SCHEMA_REFERENCE.md` — Master user identity consolidation (Feb 2026)

## Recent Schema Changes (Feb 2026)

### Master Users & Identity Normalization
New tables added to consolidate ACC/Revizto users by email:
- **`master_users`** — Normalized user record (one per email)
- **`master_user_identities`** — Source-specific identities (ACC vs Revizto users)
- **`master_user_flags`** — User project settings (invitations, watcher status, assignee eligibility)
- **Related migrations**: `20260213_add_master_user_identities.sql`, `20260206_add_issue_link_anchors.sql`

See `../features/MASTER_USERS_FEATURE.md` for feature overview and data flow.

## Archived During 2026-02 Cleanup
- `DATABASE_OPTIMIZATION_AGENT_PROMPT.md`
- `DB_MIGRATION_PROGRESS.md`
- `DB_MIGRATION_SESSION3_TOOLS.md`

Archived copies are in `../archive/2026-02-doc-cleanup/migration/`.

For implementation standards, use `../core/DATABASE_CONNECTION_GUIDE.md`.