from langchain_anthropic import ChatAnthropic

from app import config  # noqa: F401 - ensures .env is loaded before ChatAnthropic reads env vars
from app.agents.context import build_pr_context
from app.models import AgentFindings, AgentResult

SYSTEM_PROMPT = """You are a senior application security engineer reviewing a GitHub pull \
request for SECURITY VULNERABILITIES.

Focus only on: injection (SQL, command, template), hardcoded secrets or credentials, \
authentication/authorization issues, unsafe deserialization, SSRF, path traversal, \
insecure use of cryptography, and unsafe handling of user input.

Pay close attention to any static analysis findings tagged with high severity or codes \
starting with "S" or "B" (bandit/ruff security rules) - they are strong signals, but use \
your judgement on exploitability and context rather than reporting every match blindly.

Do NOT comment on code style, performance, or test coverage - other specialists handle those.

For each finding, reference the exact file and, where possible, the line number shown \
in the diff. Give a score from 0 (severe, exploitable vulnerabilities present) to 100 \
(no security concerns) reflecting the changed code only."""

llm = (
    ChatAnthropic(model="claude-sonnet-4-6", temperature=0, max_tokens=4096)
    .with_structured_output(AgentFindings)
    .with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
)


async def security_agent_node(state: dict) -> dict:
    context = build_pr_context(state["pr"], state["static_analysis"])

    result: AgentFindings = await llm.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", context),
        ]
    )

    agent_result = AgentResult(
        agent_name="security_agent",
        dimension="security",
        summary=result.summary,
        score=result.score,
        findings=result.findings,
    )
    return {"agent_results": [agent_result]}
