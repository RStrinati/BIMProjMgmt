# Bid Management DBA Migration Pack

Run order:
1) `sql/migrations/013_bid_management.sql`
2) (Optional rollback) `sql/migrations/013_rollback_bid_management.sql`

Notes:
- Scripts are idempotent and safe to re-run.
- Rollback drops only Bid Management tables and does not touch existing objects.
