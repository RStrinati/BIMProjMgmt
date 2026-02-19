# Documentation Cleanup Review (2026-02)

## Objective
Reduce active documentation noise, keep canonical implementation guides in place, and move low-signal status artifacts to archive without data loss.

## Folder-by-Folder Assessment

### `docs/archive`
- **Assessment:** Correct location for historical and superseded docs.
- **Action:** Added `2026-02-doc-cleanup/` bucket for this pass.

### `docs/cleanup`
- **Assessment:** Entire folder was historical process meta and no longer operational.
- **Action:** Moved all files to archive; folder now empty.

### `docs/core`
- **Assessment:** Contains essential onboarding and standards docs.
- **Action:** Kept core standards; archived roadmap-adjacent one-pagers and temporary orientation docs.

### `docs/features`
- **Assessment:** Mixed high-value specs with many delivery/status summaries.
- **Action:** Kept index/start-here/usage/spec docs; archived completion summaries, planning artifacts, and one-off delivery reports.

### `docs/integrations`
- **Assessment:** Strong architecture/docs set with some duplicated summary files.
- **Action:** Kept architecture/index/reference docs; archived enhancement/summary-only files.

### `docs/migration`
- **Assessment:** Core migration state docs are valuable; session-progress artifacts are not.
- **Action:** Kept migration + optimization + data flow docs; archived session-level logs/prompts.

### `docs/reference`
- **Assessment:** Highest concentration of audit/report duplication.
- **Action:** Kept reusable technical references; archived phase completion and process-heavy audit reports.

### `docs/security`
- **Assessment:** Needed simplification around overlapping audit documents.
- **Action:** Kept security audit + setup + fixes; archived duplicate report/complete summaries.

### `docs/testing`
- **Assessment:** Usable guide plus too many deep-dive planning artifacts.
- **Action:** Kept execution-focused guides/checklists; archived low-frequency analysis docs.

### `docs/troubleshooting`
- **Assessment:** Generally concise and useful.
- **Action:** Retained active fix docs; updated index to remove moved references.

### `docs/ui-audit`
- **Assessment:** Mixed curated docs with large generated raw artifacts.
- **Action:** Kept curated markdown/csv outputs; archived raw `_*.txt/.json/.md` extracts.

## Cleanup Outcome (File Count by Folder)
- `archive`: 124 → 216
- `cleanup`: 5 → 0
- `core`: 16 → 10
- `features`: 68 → 47
- `integrations`: 19 → 15
- `migration`: 9 → 6
- `reference`: 50 → 21
- `security`: 6 → 4
- `testing`: 11 → 6
- `troubleshooting`: 7 → 7
- `ui-audit`: 24 → 7

## Notes
- No documentation content was destroyed; removed files were moved into archive.
- Navigation docs were updated to point at active sources.