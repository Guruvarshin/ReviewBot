"""
LLM-as-judge: scores individual agent findings for quality.

Uses a separate Claude call so the judge is independent of the agents being evaluated.
Returns a JudgeVerdict per finding, aggregated into per-dimension precision metrics.
"""

import asyncio

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import config  # noqa: F401
from app.models import Finding


JUDGE_SYSTEM_PROMPT = """You are an expert code reviewer evaluating whether an AI-generated \
finding about a GitHub pull request is accurate, relevant, and useful.

You will be given:
1. The pull request diff (or a summary of it)
2. A finding produced by an AI reviewer

Score the finding on three axes:
- accuracy (0-3): Is the finding factually correct given the diff? 0=hallucinated, 3=clearly correct
- actionability (0-2): Does it tell the developer what to do? 0=vague, 2=specific and actionable
- severity_fit (0-2): Is the severity label (critical/high/medium/low/info) appropriate? \
  0=way off, 2=correct

Also set is_false_positive (true/false): would a senior engineer dismiss this finding as noise?

Be strict. A finding that references a line that doesn't exist in the diff, or describes a \
problem that isn't actually present, should score 0 for accuracy and be marked as false positive."""


class JudgeVerdict(BaseModel):
    finding_title: str
    accuracy: int        # 0-3
    actionability: int   # 0-2
    severity_fit: int    # 0-2
    is_false_positive: bool
    reasoning: str


class JudgeBatch(BaseModel):
    verdicts: list[JudgeVerdict]


_judge_llm = (
    ChatAnthropic(model="claude-sonnet-4-6", temperature=0, max_tokens=4096)
    .with_structured_output(JudgeBatch)
    .with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
)

_JUDGE_BATCH_SIZE = 5  # evaluate at most 5 findings per LLM call to stay within output token budget


def _format_findings_for_judge(findings: list[Finding]) -> str:
    lines = []
    for i, f in enumerate(findings, 1):
        lines.append(
            f"Finding {i}: [{f.severity.upper()}] {f.title}\n"
            f"  File: {f.file}" + (f", Line: {f.line}" if f.line else "") + "\n"
            f"  Category: {f.category}\n"
            f"  Description: {f.description}\n"
            f"  Suggestion: {f.suggestion or 'N/A'}"
        )
    return "\n\n".join(lines)


async def judge_findings(diff_summary: str, findings: list[Finding]) -> list[JudgeVerdict]:
    """Judge a list of findings in batches. Returns one verdict per finding."""
    if not findings:
        return []

    all_verdicts: list[JudgeVerdict] = []
    for i in range(0, len(findings), _JUDGE_BATCH_SIZE):
        batch = findings[i : i + _JUDGE_BATCH_SIZE]
        human_message = (
            f"PULL REQUEST DIFF SUMMARY:\n{diff_summary}\n\n"
            f"AI FINDINGS TO EVALUATE (batch {i // _JUDGE_BATCH_SIZE + 1}):\n"
            f"{_format_findings_for_judge(batch)}\n\n"
            f"Return one verdict per finding in the same order."
        )
        result: JudgeBatch = await _judge_llm.ainvoke(
            [("system", JUDGE_SYSTEM_PROMPT), ("human", human_message)]
        )
        all_verdicts.extend(result.verdicts)

    return all_verdicts


def compute_precision_metrics(verdicts: list[JudgeVerdict]) -> dict:
    if not verdicts:
        return {"total": 0, "false_positive_rate": 0.0, "mean_quality_score": 0.0, "precision": 1.0}

    total = len(verdicts)
    false_positives = sum(1 for v in verdicts if v.is_false_positive)
    quality_scores = [(v.accuracy / 3 + v.actionability / 2 + v.severity_fit / 2) / 3 * 100 for v in verdicts]

    return {
        "total": total,
        "false_positive_rate": round(false_positives / total, 3),
        "precision": round(1 - false_positives / total, 3),
        "mean_quality_score": round(sum(quality_scores) / total, 1),
        "mean_accuracy": round(sum(v.accuracy for v in verdicts) / total, 2),
        "mean_actionability": round(sum(v.actionability for v in verdicts) / total, 2),
    }
