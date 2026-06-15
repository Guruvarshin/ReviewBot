from langchain_openai import ChatOpenAI

from app import config  # noqa: F401 - ensures .env is loaded before ChatOpenAI reads env vars
from app.agents.context import build_pr_context, build_test_coverage_summary
from app.models import AgentFindings, AgentResult

SYSTEM_PROMPT = """You are a senior software engineer reviewing a GitHub pull request for \
TEST COVERAGE AND QUALITY.

Focus only on: whether new or changed logic in the source files is covered by new or \
updated tests, whether the new/updated tests cover meaningful edge cases (not just the \
happy path), and whether test code itself is clear and maintainable.

A "Test files changed" summary is provided below the diff - use it to judge whether tests \
were added or updated alongside the source changes. Do not assume tests exist for code \
you cannot see being tested.

Do NOT comment on code style, security, or performance of non-test code - other \
specialists handle those.

For each finding, reference the exact file and, where possible, the line number shown \
in the diff. Give a score from 0 (no test coverage for significant new logic) to 100 \
(thorough, well-written tests) reflecting the changed code only."""

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(AgentFindings)


async def testing_agent_node(state: dict) -> dict:
    pr = state["pr"]
    context = build_pr_context(pr, state["static_analysis"])
    context += "\n\n--- TEST COVERAGE SUMMARY ---\n" + build_test_coverage_summary(pr)

    result: AgentFindings = await llm.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", context),
        ]
    )

    agent_result = AgentResult(
        agent_name="testing_agent",
        dimension="testing",
        summary=result.summary,
        score=result.score,
        findings=result.findings,
    )
    return {"agent_results": [agent_result]}
