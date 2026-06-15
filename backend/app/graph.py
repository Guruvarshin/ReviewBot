from langgraph.graph import END, START, StateGraph

from app.agents.performance_agent import performance_agent_node
from app.agents.persist import persist_node
from app.agents.quality_agent import quality_agent_node
from app.agents.security_agent import security_agent_node
from app.agents.synthesis import synthesize_node
from app.agents.testing_agent import testing_agent_node
from app.github_client import fetch_pr, parse_pr_url
from app.graph_state import ReviewState
from app.static_analysis import run_static_analysis


async def fetch_pr_node(state: ReviewState) -> dict:
    owner, repo, number = parse_pr_url(state["pr_url"])
    pr = await fetch_pr(owner, repo, number)
    return {"pr": pr}


async def static_analysis_node(state: ReviewState) -> dict:
    result = await run_static_analysis(state["pr"])
    return {"static_analysis": result}


graph_builder = StateGraph(ReviewState)
graph_builder.add_node("fetch_pr", fetch_pr_node)
graph_builder.add_node("run_static_analysis", static_analysis_node)
graph_builder.add_node("security_agent", security_agent_node)
graph_builder.add_node("performance_agent", performance_agent_node)
graph_builder.add_node("quality_agent", quality_agent_node)
graph_builder.add_node("testing_agent", testing_agent_node)
graph_builder.add_node("synthesize", synthesize_node)
graph_builder.add_node("persist", persist_node)

graph_builder.add_edge(START, "fetch_pr")
graph_builder.add_edge("fetch_pr", "run_static_analysis")

for agent_node in ["security_agent", "performance_agent", "quality_agent", "testing_agent"]:
    graph_builder.add_edge("run_static_analysis", agent_node)
    graph_builder.add_edge(agent_node, "synthesize")

graph_builder.add_edge("synthesize", "persist")
graph_builder.add_edge("persist", END)

graph = graph_builder.compile()
