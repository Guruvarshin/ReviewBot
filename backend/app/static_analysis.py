import asyncio
import json
import os
import subprocess
import sys
import tempfile

from app.diff_utils import changed_lines
from app.github_client import fetch_file_content
from app.models import FileStaticResult, PRMetadata, StaticAnalysisResult, StaticIssue

RUFF_SEVERITY_PREFIXES = {
    "S": "high",
    "F": "medium",
    "B": "medium",
}


def _ruff_severity(code: str) -> str:
    for prefix, severity in RUFF_SEVERITY_PREFIXES.items():
        if code.startswith(prefix):
            return severity
    return "low"


def _normalize_path(path: str, temp_dir: str) -> str:
    if os.path.isabs(path):
        path = os.path.relpath(path, temp_dir)
    return path.lstrip("./\\").replace(os.sep, "/")


def _run_tool(args: list[str], cwd: str) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _run_ruff(temp_dir: str) -> dict[str, list[StaticIssue]]:
    output = _run_tool(
        [sys.executable, "-m", "ruff", "check", ".", "--output-format=json", "--exit-zero"],
        temp_dir,
    )
    issues_by_file: dict[str, list[StaticIssue]] = {}
    for item in json.loads(output or "[]"):
        rel_path = _normalize_path(item["filename"], temp_dir)
        issues_by_file.setdefault(rel_path, []).append(
            StaticIssue(
                tool="ruff",
                line=item["location"]["row"],
                severity=_ruff_severity(item["code"]),
                code=item["code"],
                message=item["message"],
            )
        )
    return issues_by_file


def _run_bandit(temp_dir: str) -> dict[str, list[StaticIssue]]:
    output = _run_tool(
        [sys.executable, "-m", "bandit", "-r", "-f", "json", "-q", "."],
        temp_dir,
    )
    issues_by_file: dict[str, list[StaticIssue]] = {}
    if not output.strip():
        return issues_by_file

    data = json.loads(output)
    for item in data.get("results", []):
        rel_path = _normalize_path(item["filename"], temp_dir)
        issues_by_file.setdefault(rel_path, []).append(
            StaticIssue(
                tool="bandit",
                line=item["line_number"],
                severity=item["issue_severity"].lower(),
                code=item["test_id"],
                message=item["issue_text"],
            )
        )
    return issues_by_file


def _run_radon_cc(temp_dir: str) -> dict[str, float]:
    output = _run_tool([sys.executable, "-m", "radon", "cc", "-j", "."], temp_dir)
    data = json.loads(output or "{}")
    averages: dict[str, float] = {}
    for path, blocks in data.items():
        if not blocks:
            continue
        rel_path = _normalize_path(path, temp_dir)
        scores = [block["complexity"] for block in blocks]
        averages[rel_path] = sum(scores) / len(scores)
    return averages


def _run_radon_mi(temp_dir: str) -> dict[str, float]:
    output = _run_tool([sys.executable, "-m", "radon", "mi", "-j", "."], temp_dir)
    data = json.loads(output or "{}")
    return {
        _normalize_path(path, temp_dir): entry["mi"]
        for path, entry in data.items()
    }


def _analyze_directory(temp_dir: str) -> StaticAnalysisResult:
    ruff_issues = _run_ruff(temp_dir)
    bandit_issues = _run_bandit(temp_dir)
    complexity = _run_radon_cc(temp_dir)
    maintainability = _run_radon_mi(temp_dir)

    all_files = set(ruff_issues) | set(bandit_issues) | set(complexity) | set(maintainability)

    results = []
    for filename in sorted(all_files):
        issues = ruff_issues.get(filename, []) + bandit_issues.get(filename, [])
        results.append(
            FileStaticResult(
                filename=filename,
                issues=issues,
                cyclomatic_complexity=complexity.get(filename),
                maintainability_index=maintainability.get(filename),
            )
        )

    return StaticAnalysisResult(files=results, python_files_analyzed=len(all_files))


async def run_static_analysis(pr: PRMetadata) -> StaticAnalysisResult:
    python_files = [
        f for f in pr.files if f.language == "python" and f.status != "removed"
    ]

    if not python_files:
        return StaticAnalysisResult(files=[], python_files_analyzed=0)

    contents = await asyncio.gather(
        *(
            fetch_file_content(pr.owner, pr.repo, pr.head_sha, f.filename)
            for f in python_files
        )
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        for file, content in zip(python_files, contents):
            if content is None:
                continue
            target_path = os.path.join(temp_dir, file.filename)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)

        result = await asyncio.to_thread(_analyze_directory, temp_dir)

    pr_changed_lines = {f.filename: changed_lines(f.patch) for f in python_files}
    for file_result in result.files:
        added_lines = pr_changed_lines.get(file_result.filename, set())
        file_result.issues = [
            issue
            for issue in file_result.issues
            if issue.line is None or issue.line in added_lines
        ]

    return result
