import time
from datetime import datetime, timezone

from langchain_anthropic import ChatAnthropic

from app import config  # noqa: F401 - ensures .env is loaded before ChatAnthropic reads env vars
from app.agents.context import build_synthesis_context
from app.models import ReviewResult, SynthesisOutput

SYSTEM_PROMPT = """You are a principal engineer producing the final consolidated review for \
a GitHub pull request, based on the results of four specialist reviewers: security, \
performance, code quality, and testing.

Write a concise consolidated summary (2-4 sentences) that gives the PR author the most \
important takeaways across all dimensions, prioritizing critical/high severity findings.

Then give an overall score from 0 to 100. This should NOT simply be the average of the \
four dimension scores - weight it toward the lowest scores and toward critical/high \
severity security findings, since a severe security issue should dominate an otherwise \
clean PR."""

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0).with_structured_output(
    SynthesisOutput
)


async def synthesize_node(state: dict) -> dict:
    pr = state["pr"]
    agent_results = state["agent_results"]
    context = build_synthesis_context(pr, agent_results)

    result: SynthesisOutput = await llm.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", context),
        ]
    )

    final_review = ReviewResult(
        pr_url=state["pr_url"],
        repo_owner=pr.owner,
        repo_name=pr.repo,
        pr_number=pr.number,
        pr_title=pr.title,
        overall_score=result.overall_score,
        dimension_scores={ar.dimension: ar.score for ar in agent_results},
        consolidated_summary=result.consolidated_summary,
        agent_results=agent_results,
        created_at=datetime.now(timezone.utc),
        review_duration_seconds=time.monotonic() - state["started_at"],
    )
    return {"final_review": final_review}
