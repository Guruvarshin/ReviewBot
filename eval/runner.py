"""
ReviewBot Evaluation Runner

Usage:
    cd backend
    python ../eval/runner.py                     # full eval (golden set + consistency)
    python ../eval/runner.py --consistency-only  # just consistency tests (faster)
    python ../eval/runner.py --case hardcoded_secret  # single case by id

Outputs:
    eval/results/report_<timestamp>.json   raw results
    eval/results/report_<timestamp>.md     human-readable summary
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import config  # noqa: F401
from app.graph import graph
from app.models import ReviewResult

from judge import compute_precision_metrics, judge_findings

RESULTS_DIR = Path(__file__).parent / "results"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _diff_summary(review: ReviewResult) -> str:
    """Build a compact diff summary to pass to the judge (avoids re-fetching GitHub)."""
    pr = review
    lines = [
        f"PR: {pr.pr_title}",
        f"Repo: {pr.repo_owner}/{pr.repo_name}  PR #{pr.pr_number}",
        f"Overall score: {pr.overall_score}",
    ]
    for ar in pr.agent_results:
        lines.append(f"\n[{ar.dimension.upper()} agent, score={ar.score}]")
        lines.append(ar.summary)
    return "\n".join(lines)


def _check_recall(review: ReviewResult, expected_findings: list[dict]) -> dict:
    """
    For each expected finding, check if any actual finding contains at least one
    of the expected keywords in its title/description, in the right dimension.
    """
    results = []
    for exp in expected_findings:
        dimension = exp["dimension"]
        keywords = [k.lower() for k in exp["keywords"]]
        agent_result = next((ar for ar in review.agent_results if ar.dimension == dimension), None)
        if agent_result is None:
            results.append({"expected": exp, "found": False, "reason": "dimension not in results"})
            continue

        matched = any(
            any(kw in (f.title + " " + f.description).lower() for kw in keywords)
            for f in agent_result.findings
        )
        results.append({"expected": exp, "found": matched})
    return {
        "recall": round(sum(r["found"] for r in results) / len(results), 3) if results else 1.0,
        "details": results,
    }


def _check_score_bounds(review: ReviewResult, score_bounds: dict) -> dict:
    results = {}
    dim_scores = {**review.dimension_scores, "overall": review.overall_score}
    for dim, bounds in score_bounds.items():
        actual = dim_scores.get(dim)
        passed = True
        if actual is None:
            passed = False
        else:
            if "min" in bounds and actual < bounds["min"]:
                passed = False
            if "max" in bounds and actual > bounds["max"]:
                passed = False
        results[dim] = {"actual": actual, "bounds": bounds, "passed": passed}
    return results


async def run_review(pr_url: str) -> tuple[ReviewResult, float]:
    start = time.monotonic()
    state = await graph.ainvoke({"pr_url": pr_url, "started_at": start})
    elapsed = time.monotonic() - start
    return state["final_review"], elapsed


# ---------------------------------------------------------------------------
# Eval types
# ---------------------------------------------------------------------------

async def run_golden_case(case: dict) -> dict:
    print(f"\n  Running case: {case['id']} ...")
    pr_url = case["pr_url"]

    if pr_url == "FILL_IN":
        print(f"  SKIP — pr_url not filled in for case '{case['id']}'")
        return {"case_id": case["id"], "skipped": True}

    try:
        review, elapsed = await run_review(pr_url)
    except Exception as exc:
        print(f"  ERROR: {exc}")
        return {"case_id": case["id"], "error": str(exc)}

    # 1. Recall
    recall_result = _check_recall(review, case["expected_findings"])

    # 2. Score calibration
    calibration_result = _check_score_bounds(review, case["score_bounds"])

    # 3. LLM-as-judge precision (run for each dimension that has findings)
    judge_results = {}
    diff_summary = _diff_summary(review)
    for ar in review.agent_results:
        if ar.findings:
            verdicts = await judge_findings(diff_summary, ar.findings)
            judge_results[ar.dimension] = compute_precision_metrics(verdicts)

    calibration_passed = all(v["passed"] for v in calibration_result.values())
    overall_precision = (
        round(
            sum(j["precision"] for j in judge_results.values()) / len(judge_results), 3
        )
        if judge_results
        else 1.0
    )

    result = {
        "case_id": case["id"],
        "description": case["description"],
        "pr_url": pr_url,
        "latency_seconds": round(elapsed, 2),
        "scores": {**review.dimension_scores, "overall": review.overall_score},
        "recall": recall_result["recall"],
        "recall_details": recall_result["details"],
        "calibration_passed": calibration_passed,
        "calibration": calibration_result,
        "precision_by_dimension": judge_results,
        "overall_precision": overall_precision,
        "passed": recall_result["recall"] == 1.0 and calibration_passed,
    }

    status = "PASS" if result["passed"] else "FAIL"
    print(f"  {status} | recall={recall_result['recall']} | precision={overall_precision} | latency={elapsed:.1f}s")
    return result


async def run_consistency_test(pr_url: str, run_index: int) -> dict:
    if pr_url == "FILL_IN":
        return {"pr_url": pr_url, "skipped": True}

    print(f"\n  Consistency test {run_index + 1}: {pr_url[:60]}...")
    try:
        r1, _ = await run_review(pr_url)
        r2, _ = await run_review(pr_url)
    except Exception as exc:
        return {"pr_url": pr_url, "error": str(exc)}

    dims = ["security", "performance", "quality", "testing", "overall"]
    scores_1 = {**r1.dimension_scores, "overall": r1.overall_score}
    scores_2 = {**r2.dimension_scores, "overall": r2.overall_score}

    variance = {d: abs(scores_1[d] - scores_2[d]) for d in dims}
    max_variance = max(variance.values())
    passed = max_variance <= 10

    status = "PASS" if passed else "FAIL"
    print(f"  {status} | max score variance: {max_variance} pts")
    return {
        "pr_url": pr_url,
        "run1_scores": scores_1,
        "run2_scores": scores_2,
        "variance": variance,
        "max_variance": max_variance,
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _write_report(golden_results: list[dict], consistency_results: list[dict], output_dir: Path):
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"report_{ts}.json"
    json_path.write_text(
        json.dumps({"golden": golden_results, "consistency": consistency_results}, indent=2, default=str),
        encoding="utf-8",
    )

    # Markdown report
    md_lines = [
        f"# ReviewBot Eval Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Golden Set Results",
        "",
        "| Case | Recall | Precision | Calibration | Latency | Result |",
        "|------|--------|-----------|-------------|---------|--------|",
    ]

    valid = [r for r in golden_results if not r.get("skipped") and not r.get("error")]
    for r in golden_results:
        if r.get("skipped"):
            md_lines.append(f"| {r['case_id']} | — | — | — | — | SKIPPED |")
        elif r.get("error"):
            md_lines.append(f"| {r['case_id']} | — | — | — | — | ERROR |")
        else:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            md_lines.append(
                f"| {r['case_id']} | {r['recall']:.0%} | {r['overall_precision']:.0%} "
                f"| {'✅' if r['calibration_passed'] else '❌'} "
                f"| {r['latency_seconds']}s | {status} |"
            )

    if valid:
        avg_recall = sum(r["recall"] for r in valid) / len(valid)
        avg_precision = sum(r["overall_precision"] for r in valid) / len(valid)
        avg_latency = sum(r["latency_seconds"] for r in valid) / len(valid)
        pass_rate = sum(1 for r in valid if r["passed"]) / len(valid)

        md_lines += [
            "",
            f"**Summary**: {len(valid)} cases evaluated | "
            f"Pass rate: {pass_rate:.0%} | "
            f"Avg recall: {avg_recall:.0%} | "
            f"Avg precision: {avg_precision:.0%} | "
            f"Avg latency: {avg_latency:.1f}s",
        ]

    md_lines += ["", "## Consistency Tests", ""]
    valid_c = [r for r in consistency_results if not r.get("skipped") and not r.get("error")]
    for r in consistency_results:
        if r.get("skipped"):
            md_lines.append("- SKIPPED (pr_url not filled in)")
        elif r.get("error"):
            md_lines.append(f"- ERROR: {r['error']}")
        else:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            md_lines.append(
                f"- {r['pr_url'][:60]}... | max variance: {r['max_variance']}pts | {status}"
            )
            for dim, v in r["variance"].items():
                md_lines.append(f"  - {dim}: {r['run1_scores'][dim]} vs {r['run2_scores'][dim]} (Δ{v})")

    if valid_c:
        avg_var = sum(r["max_variance"] for r in valid_c) / len(valid_c)
        md_lines.append(f"\n**Avg max variance**: {avg_var:.1f} pts (target: ≤10)")

    md_path = output_dir / f"report_{ts}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return json_path, md_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="ReviewBot evaluation runner")
    parser.add_argument("--consistency-only", action="store_true")
    parser.add_argument("--golden-only", action="store_true")
    parser.add_argument("--case", help="Run a single golden case by id")
    args = parser.parse_args()

    from cases import CONSISTENCY_TEST_PRS, TEST_CASES

    golden_results = []
    consistency_results = []

    if not args.consistency_only:
        cases_to_run = TEST_CASES
        if args.case:
            cases_to_run = [c for c in TEST_CASES if c["id"] == args.case]
            if not cases_to_run:
                print(f"No case found with id '{args.case}'")
                sys.exit(1)

        print(f"\n=== Golden Set Evaluation ({len(cases_to_run)} cases) ===")
        for case in cases_to_run:
            result = await run_golden_case(case)
            golden_results.append(result)

    if not args.golden_only:
        print(f"\n=== Consistency Tests ({len(CONSISTENCY_TEST_PRS)} PRs × 2 runs) ===")
        for i, pr_url in enumerate(CONSISTENCY_TEST_PRS):
            result = await run_consistency_test(pr_url, i)
            consistency_results.append(result)

    json_path, md_path = _write_report(golden_results, consistency_results, RESULTS_DIR)
    print(f"\n=== Report written ===")
    print(f"  JSON : {json_path}")
    print(f"  MD   : {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
