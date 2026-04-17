# Tests

Date verified: `2026-04-17`

## Commands

```bash
python3 -m py_compile backend/platform_core.py backend/platform_api.py backend/postgres_store.py backend/db_schema.py backend/demo_seed.py backend/tests/test_ui_validation_modal.py
docker compose exec -T backend pytest tests -q
```

## Results

```text
29 passed, 1 skipped, 7 warnings in 152.37s (0:02:32)
```

## Coverage Added In This Change Set

- Diagnosis-link warning becomes resolvable and persisted.
- Patient claim-context returns the required claim-carry dataset.
- Structured payload endpoint returns stage completeness and remediation actions.
- EDI submission writes persisted artefacts and transport logs.
- PMB no-match returns evaluated ICD-10s, version/date context, and admin action metadata.

## Notes

- The single skipped test is the UI smoke test when frontend assets are not present inside the backend-only Docker test image.
- `node --check js/app.js` could not be executed in this workspace because `node` is not installed locally.
