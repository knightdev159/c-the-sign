# QUALITY_REPORT.md

This report captures objective metrics from `backend/scripts/run_eval.py`.

## How to Generate

1. Run backend locally on `http://localhost:8000`.
2. Execute:

```bash
python backend/scripts/run_eval.py --base-url http://localhost:8000
```

3. Review `backend/eval_report.json`.

## Metrics Tracked

- `pass_rate`
- `citation_presence_rate`
- `avg_groundedness_score`
- `abstain_rate`

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
