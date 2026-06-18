# ReviewBot Evaluation Framework

Measures finding quality, score calibration, and consistency of the multi-agent review pipeline.

## What it measures

| Metric | How | Target |
|---|---|---|
| **Finding recall** | Does each golden case catch the expected issue? | 100% on critical/high cases |
| **Finding precision** | LLM-as-judge: are findings accurate, not hallucinated? | >75% |
| **Score calibration** | Do known-bad PRs score below the defined ceiling? | All bounds pass |
| **Score consistency** | Same PR reviewed twice — how much do scores drift? | Max variance ≤10 pts |
| **Latency** | p50/p95 review_duration_seconds across cases | Logged for tracking |

## Setup

```bash
cd backend
pip install -r requirements.txt  # already done if backend is running
```

Populate `eval/cases.py` with real public PR URLs:
- `hardcoded_secret` — any PR that adds a literal API key or password in code
- `sql_injection` — a PR using f-string/format SQL queries without parameterization
- `n_plus_one_query` — a loop calling a DB query per iteration
- `no_tests_for_new_logic` — new source files with no corresponding test files
- `clean_pr` — a docs update or minor rename with no real issues
- `CONSISTENCY_TEST_PRS` — any 2 PRs you've already reviewed manually

## Running

```bash
# from the backend/ directory (needs .env loaded)
python ../eval/runner.py                      # full eval
python ../eval/runner.py --consistency-only   # fast — just score drift check
python ../eval/runner.py --golden-only        # just the golden set
python ../eval/runner.py --case hardcoded_secret  # one case
```

Results are written to `eval/results/report_<timestamp>.json` and `.md`.

## Interpreting results

**Recall = 1.0** on a case means the agent found what it was supposed to find.
**Precision** is the judge's estimate of what fraction of findings are real (not noise).
**Calibration passed** means the score fell within the expected bounds (e.g. security ≤ 45 for a known-vulnerable PR).
**Max variance ≤ 10** on consistency means the agents are stable across runs (temperature=0 helps).

A sample report looks like:

```
| Case               | Recall | Precision | Calibration | Latency | Result  |
|--------------------|--------|-----------|-------------|---------|---------|
| hardcoded_secret   |  100%  |    82%    |      ✅     |  18.4s  | ✅ PASS |
| sql_injection      |  100%  |    79%    |      ✅     |  21.1s  | ✅ PASS |
| clean_pr           |  100%  |    91%    |      ✅     |  14.2s  | ✅ PASS |

Summary: 5 cases | Pass rate: 100% | Avg recall: 100% | Avg precision: 82% | Avg latency: 17.8s
```
