from datetime import datetime
from typing import Literal

from pydantic import BaseModel

EXTENSION_LANGUAGE_MAP = {
    "py": "python",
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "go": "go",
    "java": "java",
    "rb": "ruby",
    "rs": "rust",
    "c": "c",
    "h": "c",
    "cpp": "cpp",
    "hpp": "cpp",
    "cs": "csharp",
    "php": "php",
    "md": "markdown",
    "json": "json",
    "yml": "yaml",
    "yaml": "yaml",
    "html": "html",
    "css": "css",
}


def infer_language(filename: str) -> str:
    if "." not in filename:
        return "other"
    extension = filename.rsplit(".", 1)[-1].lower()
    return EXTENSION_LANGUAGE_MAP.get(extension, "other")


class PRFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None
    language: str
    patch_truncated: bool


class StaticIssue(BaseModel):
    tool: str
    line: int | None
    severity: str
    code: str
    message: str


class FileStaticResult(BaseModel):
    filename: str
    issues: list[StaticIssue]
    cyclomatic_complexity: float | None
    maintainability_index: float | None


class StaticAnalysisResult(BaseModel):
    files: list[FileStaticResult]
    python_files_analyzed: int


class Finding(BaseModel):
    file: str
    line: int | None
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: str
    title: str
    description: str
    suggestion: str | None


class AgentFindings(BaseModel):
    summary: str
    score: int
    findings: list[Finding]


class AgentResult(BaseModel):
    agent_name: str
    dimension: Literal["security", "performance", "quality", "testing"]
    summary: str
    score: int
    findings: list[Finding]


class SynthesisOutput(BaseModel):
    overall_score: int
    consolidated_summary: str


class ReviewResult(BaseModel):
    pr_url: str
    repo_owner: str
    repo_name: str
    pr_number: int
    pr_title: str
    overall_score: int
    dimension_scores: dict[str, int]
    consolidated_summary: str
    agent_results: list[AgentResult]
    created_at: datetime
    review_duration_seconds: float


class ReviewSummary(BaseModel):
    id: str
    pr_url: str
    repo_owner: str
    repo_name: str
    pr_number: int
    pr_title: str
    overall_score: int
    dimension_scores: dict[str, int]
    created_at: datetime


class ReviewDetail(ReviewResult):
    id: str


class PRMetadata(BaseModel):
    owner: str
    repo: str
    number: int
    title: str
    author: str
    base_branch: str
    head_branch: str
    head_sha: str
    additions: int
    deletions: int
    changed_files: int
    files: list[PRFile]
    files_truncated: bool
