# Quality Report

This report captures objective metrics from `backend/scripts/run_eval.py` using `backend/eval_cases.json`.

## How to Generate

1. Start the backend locally from the repo root:

```bash
source backend/.venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

2. Execute:

```bash
source backend/.venv/bin/activate
python backend/scripts/run_eval.py --base-url http://localhost:8000
```

3. Review `backend/eval_report.json`.

## Metrics Tracked

- `total_cases`
- `passed_cases`
- `pass_rate`
- `citation_presence_rate`
- `avg_groundedness_score`
- `abstain_rate`

The generated report also includes per-case status, safety action, citation count, groundedness score, and raw response payloads.

## Failure Analysis Template

### Case: `<case_id>`
- Expected:
- Actual:
- Root cause:
- Fix applied / planned:

### Case: `<case_id>`
- Expected:
- Actual:
- Root cause:
- Fix applied / planned:

### Case: `<case_id>`
- Expected:
- Actual:
- Root cause:
- Fix applied / planned:
