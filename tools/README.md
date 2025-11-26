# Tools Overview

This directory holds operational/maintenance scripts. Legacy tests/debug scripts live in `tests/legacy_tools/`.

- **Configuration**: `appsettings.template.json`, `appsettings.json` (local only, ignored), `config_loader.py`. Keep `appsettings.json` out of git.
- **db/**: DB checks and schema helpers (`check_*`, `verify_custom_attributes.py`, SQL diagnostics such as `sql_inventory.sql`).
- **imports/**: Data migrations/import utilities (`migrate_*`, `apply_*`, `run_batch_processing.py`, `fix_sql_syntax.py`, `diagnose_acc_project_mapping.sql`, etc.).
- **analytics/**: Analysis and debugging helpers (`analyze_*`, `debug_*`, `setup_issue_analytics.py`, `seed_keywords.py`, `generate_analytics_report.py`, etc.).
- **Docs maintenance**: `check_docs_links.py` (root) used in CI to validate markdown links.
- **archive/legacy-binaries/**: Revizto artifacts; do not commit new binaries without review.

When adding new scripts:
- Place operational/data-maintenance scripts in the appropriate subfolder.
- Put automated tests under `tests/`.
- Archive one-off/obsolete scripts instead of leaving them at the top level.
