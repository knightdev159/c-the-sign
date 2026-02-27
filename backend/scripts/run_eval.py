#!/usr/bin/env python3
"""Run evaluation scenarios against local API endpoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NG12 API evaluation cases")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--cases", type=Path, default=Path("backend/eval_cases.json"))
    parser.add_argument("--output", type=Path, default=Path("backend/eval_report.json"))
    return parser.parse_args()


def call_json(method: str, url: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    request = Request(
        url,
        method=method,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request) as response:  # noqa: S310 - local evaluation utility
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except HTTPError as err:
        body = err.read().decode("utf-8") if err.fp else "{}"
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"detail": body}
        return err.code, parsed


def run_case(base_url: str, case: dict[str, object]) -> dict[str, object]:
    mode = case["mode"]
    payload = case["payload"]
    endpoint = "/assess" if mode == "assess" else "/chat"

    status, body = call_json("POST", f"{base_url}{endpoint}", payload)
    expected_status = int(case.get("expected_status", 200))
    expected_action = case.get("expected_action")

    action = None
    citations = 0
    groundedness = 0.0
    if status == 200 and isinstance(body, dict):
        safety = body.get("safety") or {}
        action = safety.get("action")
        groundedness = float(safety.get("groundedness_score", 0.0))
        citations = len(body.get("citations", []))

    pass_status = status == expected_status
    pass_action = True if expected_action is None else action == expected_action

    return {
        "id": case["id"],
        "status": status,
        "expected_status": expected_status,
        "action": action,
        "expected_action": expected_action,
        "citations": citations,
        "groundedness_score": groundedness,
        "pass_status": pass_status,
        "pass_action": pass_action,
        "passed": pass_status and pass_action,
        "response": body,
    }


def summarize(results: list[dict[str, object]]) -> dict[str, object]:
    if not results:
        return {}

    total = len(results)
    passed = sum(1 for result in results if result["passed"])
    with_citations = sum(1 for result in results if int(result.get("citations", 0)) > 0)
    avg_groundedness = sum(float(result.get("groundedness_score", 0.0)) for result in results) / total
    abstains = sum(1 for result in results if result.get("action") == "abstain")

    return {
        "total_cases": total,
        "passed_cases": passed,
        "pass_rate": passed / total,
        "citation_presence_rate": with_citations / total,
        "avg_groundedness_score": avg_groundedness,
        "abstain_rate": abstains / total,
    }


def main() -> None:
    args = parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))

    results = [run_case(args.base_url, case) for case in cases]
    summary = summarize(results)

    report = {
        "base_url": args.base_url,
        "summary": summary,
        "results": results,
    }

    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Saved evaluation report to {args.output}")


if __name__ == "__main__":
    main()
