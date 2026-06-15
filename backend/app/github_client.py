import base64
import re

import httpx

from app.config import GITHUB_TOKEN
from app.models import PRFile, PRMetadata, infer_language

GITHUB_API_BASE = "https://api.github.com"
MAX_FILES = 300
MAX_PATCH_LINES = 500

PR_URL_PATTERN = re.compile(
    r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
)


class PRNotFoundError(Exception):
    pass


class GitHubRateLimitError(Exception):
    pass


def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    match = PR_URL_PATTERN.search(pr_url)
    if not match:
        raise ValueError(f"Not a valid GitHub PR URL: {pr_url}")
    return match["owner"], match["repo"], int(match["number"])


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _truncate_patch(patch: str | None) -> tuple[str | None, bool]:
    if patch is None:
        return None, False
    lines = patch.splitlines()
    if len(lines) <= MAX_PATCH_LINES:
        return patch, False
    truncated = "\n".join(lines[:MAX_PATCH_LINES])
    truncated += f"\n... diff truncated ({len(lines) - MAX_PATCH_LINES} more lines) ..."
    return truncated, True


async def _get(client: httpx.AsyncClient, url: str, params: dict | None = None) -> httpx.Response:
    response = await client.get(url, headers=_headers(), params=params)
    if response.status_code == 404:
        raise PRNotFoundError(f"PR not found: {url}")
    if response.status_code in (403, 429):
        raise GitHubRateLimitError(
            f"GitHub API rate limit or access error ({response.status_code}): {response.text}"
        )
    response.raise_for_status()
    return response


async def fetch_file_content(owner: str, repo: str, ref: str, path: str) -> str | None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
            headers=_headers(),
            params={"ref": ref},
        )
    if response.status_code != 200:
        return None

    data = response.json()
    if data.get("encoding") != "base64":
        return None

    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


async def fetch_pr(owner: str, repo: str, number: int) -> PRMetadata:
    async with httpx.AsyncClient(timeout=30.0) as client:
        pr_response = await _get(
            client, f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}"
        )
        pr_data = pr_response.json()

        files: list[PRFile] = []
        files_truncated = False
        page = 1
        while True:
            files_response = await _get(
                client,
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}/files",
                params={"per_page": 100, "page": page},
            )
            page_files = files_response.json()
            if not page_files:
                break

            for file_data in page_files:
                if len(files) >= MAX_FILES:
                    files_truncated = True
                    break

                patch, patch_truncated = _truncate_patch(file_data.get("patch"))
                files.append(
                    PRFile(
                        filename=file_data["filename"],
                        status=file_data["status"],
                        additions=file_data["additions"],
                        deletions=file_data["deletions"],
                        changes=file_data["changes"],
                        patch=patch,
                        language=infer_language(file_data["filename"]),
                        patch_truncated=patch_truncated,
                    )
                )

            if files_truncated or len(page_files) < 100:
                break
            page += 1

    return PRMetadata(
        owner=owner,
        repo=repo,
        number=number,
        title=pr_data["title"],
        author=pr_data["user"]["login"],
        base_branch=pr_data["base"]["ref"],
        head_branch=pr_data["head"]["ref"],
        head_sha=pr_data["head"]["sha"],
        additions=pr_data["additions"],
        deletions=pr_data["deletions"],
        changed_files=pr_data["changed_files"],
        files=files,
        files_truncated=files_truncated,
    )
