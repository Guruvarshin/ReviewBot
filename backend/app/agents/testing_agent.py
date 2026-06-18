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

SCORING RUBRIC:
- 85-100: new logic is accompanied by adequate tests, OR the PR contains no testable logic \
(documentation, configuration, CI/CD files, dependency updates, comments, or formatting-only changes).
- 60-84: partial test coverage — some new logic is tested but meaningful paths are missing.
- 30-59: new logic added with no tests at all.
- 0-29: existing tests deleted or clearly broken by the change.

IMPORTANT: A PR that only changes documentation, config files, CI/CD workflows, or \
non-executable content has no testable logic — score it 85 or higher and return an empty \
findings list. Do not penalise a PR for lacking tests when there is nothing to test.

IMPORTANT RULES FOR FINDINGS:
- Only raise findings when test files WERE changed in this PR but the tests are insufficient \
(e.g. missing edge cases, missing error paths, testing only the happy path). \
If NO test files were modified at all, do not raise any findings — express that entirely \
through the score and the summary. A finding requires something testable to critique.
- When you do raise a finding, name the specific function AND describe a concrete missing \
test scenario (e.g. "test that export_to_csv raises ValueError when the date range is empty"). \
Generic statements like "no tests added" or "tests are missing" are not findings.
- Prefer 1-3 specific, actionable findings over a long list of generic ones.

For each finding, reference the exact file and, where possible, the line number shown \
in the diff."""

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
