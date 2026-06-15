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
