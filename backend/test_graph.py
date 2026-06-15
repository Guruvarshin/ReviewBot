import asyncio
import json
import time

from app.graph import graph


async def main():
    start = time.monotonic()
    result = await graph.ainvoke(
        {
            "pr_url": "https://github.com/psf/requests/pull/7502",
            "agent_results": [],
            "started_at": time.monotonic(),
        }
    )
    elapsed = time.monotonic() - start

    print(json.dumps(result["final_review"].model_dump(mode="json"), indent=2))
    print(f"\nTotal time: {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
