from langchain_anthropic import ChatAnthropic

from app import config  # noqa: F401 - ensures .env is loaded before ChatAnthropic reads env vars
from app.agents.context import build_pr_context
from app.models import AgentFindings, AgentResult

SYSTEM_PROMPT = """You are a senior software engineer reviewing a GitHub pull request for \
PERFORMANCE.

Focus only on: inefficient algorithms or data structures (e.g. O(n^2) where O(n) is \
possible), N+1 query patterns, unnecessary work inside loops, redundant I/O or network \
calls, blocking calls in async code, and unbounded memory growth.

Use the cyclomatic complexity numbers from static analysis as a hint for where logic may \
have grown complex enough to hide inefficiencies, but reason primarily from the diff itself.

Do NOT comment on code style, security, or test coverage - other specialists handle those.

IMPORTANT RULES FOR FINDINGS:
- Only raise a finding for code that was ADDED or CHANGED (+ lines in the diff). \
Do not flag pre-existing performance issues in unchanged context lines.
- A finding must identify a clear, demonstrable inefficiency — not a hypothetical one. \
If you are speculating about performance without concrete evidence in the diff, do not raise it.
- Only raise findings of medium severity or higher. Minor micro-optimisations are not worth raising.

For each finding, reference the exact file and, where possible, the line number shown \
in the diff. Give a score from 0 (severe performance problems) to 100 (no performance \
concerns) reflecting the changed code only."""

llm = (
    ChatAnthropic(model="claude-sonnet-4-6", temperature=0, max_tokens=4096)
    .with_structured_output(AgentFindings)
    .with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
)


async def performance_agent_node(state: dict) -> dict:
    context = build_pr_context(state["pr"], state["static_analysis"])

    result: AgentFindings = await llm.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", context),
        ]
    )

    agent_result = AgentResult(
        agent_name="performance_agent",
        dimension="performance",
        summary=result.summary,
        score=result.score,
        findings=result.findings,
    )
    return {"agent_results": [agent_result]}
