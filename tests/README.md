# Test Suite Organization

This repo keeps automated tests under `tests/` and manual test scripts under
`scripts/testing/`.

Structure:
- `tests/unit/`: fast tests with fakes/mocks
- `tests/integration/`: tests that call services or multiple modules together
- `tests/performance/`: timing-sensitive checks
- `tests/fixtures/`: shared fixtures and data

Manual scripts (not collected by pytest):
- `scripts/testing/`: one-off or interactive validation helpers

Frontend:
- Playwright tests live under `e2e/`

Common commands:
```bash
pytest
pytest tests/unit
pytest tests/integration -m "not slow"
pytest tests/performance
```
