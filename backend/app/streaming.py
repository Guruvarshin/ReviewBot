import json
import time
from typing import AsyncIterator

from app.github_client import GitHubRateLimitError, PRNotFoundError
from app.graph import graph


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_review(pr_url: str) -> AsyncIterator[str]:
    try:
        async for update in graph.astream(
            {"pr_url": pr_url, "agent_results": [], "started_at": time.monotonic()},
            stream_mode="updates",
        ):
            for node_name, node_output in update.items():
                if node_name == "fetch_pr":
                    pr = node_output["pr"]
                    yield _sse(
                        "pr_fetched",
                        {
                            "title": pr.title,
                            "author": pr.author,
                            "base_branch": pr.base_branch,
                            "head_branch": pr.head_branch,
                            "changed_files": pr.changed_files,
                            "additions": pr.additions,
                            "deletions": pr.deletions,
                        },
                    )
                elif node_name == "run_static_analysis":
                    yield _sse(
                        "static_analysis_complete",
                        {
                            "python_files_analyzed": node_output[
                                "static_analysis"
                            ].python_files_analyzed,
                        },
                    )
                elif node_name == "synthesize":
                    yield _sse(
                        "review_complete",
                        node_output["final_review"].model_dump(mode="json"),
                    )
                elif node_name == "persist":
                    continue
                else:
                    result = node_output["agent_results"][0]
                    yield _sse("agent_complete", result.model_dump())
    except (PRNotFoundError, GitHubRateLimitError, ValueError) as exc:
        yield _sse("error", {"message": str(exc)})
