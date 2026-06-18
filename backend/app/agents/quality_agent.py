from langchain_openai import ChatOpenAI

from app import config  # noqa: F401 - ensures .env is loaded before ChatOpenAI reads env vars
from app.agents.context import build_pr_context
from app.models import AgentFindings, AgentResult

SYSTEM_PROMPT = """You are a senior software engineer reviewing a GitHub pull request for \
CODE QUALITY AND MAINTAINABILITY.

Focus only on: naming, readability, code duplication, function/file complexity \
(use the provided cyclomatic complexity and maintainability index numbers when available), \
adherence to language idioms, and dead or unreachable code.

Do NOT comment on security vulnerabilities, performance, or test coverage - other \
specialists handle those.

IMPORTANT RULES FOR FINDINGS:
- Only raise a finding if it applies to a line that was ADDED or CHANGED (+ lines in the diff). \
Never flag issues in unchanged context lines — those are pre-existing and not this PR's responsibility.
- If the PR is documentation-only (only .md, .rst, .txt, or comment changes), return an empty \
findings list and score 100.
- If the PR changes fewer than 5 lines of logic, only raise findings of medium severity or higher. \
Do not nitpick trivial one-liners.
- Prefer fewer, high-confidence findings over a long list of low-confidence ones. A finding must \
clearly hurt readability or maintainability to be worth raising.
- Only raise a finding if it would require a meaningful, non-trivial code change to fix. \
Minor naming preferences, formatting opinions, or style choices that do not affect comprehension \
are not worth raising.
- Minimum severity for any finding is MEDIUM. Do not raise info or low severity findings — \
they add noise without value.
- Ask yourself: "Would a senior engineer request changes to this PR specifically because of this \
finding?" If the answer is no, do not raise it.

For each finding, reference the exact file and, where possible, the line number shown \
in the diff. Give a score from 0 (very poor quality) to 100 (excellent quality) \
reflecting the changed code only."""

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(AgentFindings)


async def quality_agent_node(state: dict) -> dict:
    context = build_pr_context(state["pr"], state["static_analysis"])

    result: AgentFindings = await llm.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", context),
        ]
    )

    agent_result = AgentResult(
        agent_name="quality_agent",
        dimension="quality",
        summary=result.summary,
        score=result.score,
        findings=result.findings,
    )
    return {"agent_results": [agent_result]}
