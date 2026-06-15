from app.models import AgentResult, PRFile, PRMetadata, StaticAnalysisResult


def is_test_file(filename: str) -> bool:
    name = filename.lower()
    parts = name.split("/")
    base = parts[-1]
    return (
        "test" in parts[:-1]
        or "tests" in parts[:-1]
        or base.startswith("test_")
        or base.endswith("_test.py")
        or ".test." in base
        or ".spec." in base
    )


def build_test_coverage_summary(pr: PRMetadata) -> str:
    source_files: list[PRFile] = []
    test_files: list[PRFile] = []
    for file in pr.files:
        if file.status == "removed":
            continue
        if is_test_file(file.filename):
            test_files.append(file)
        else:
            source_files.append(file)

    lines = [
        f"Source files changed ({len(source_files)}): "
        + (", ".join(f.filename for f in source_files) or "none"),
        f"Test files changed ({len(test_files)}): "
        + (", ".join(f.filename for f in test_files) or "none"),
    ]
    return "\n".join(lines)


def build_synthesis_context(pr: PRMetadata, agent_results: list[AgentResult]) -> str:
    parts = [
        f"PR: {pr.title} by {pr.author}",
        f"{pr.owner}/{pr.repo}#{pr.number}",
        f"Files changed: {pr.changed_files} (+{pr.additions}/-{pr.deletions})",
        "\n--- SPECIALIST AGENT RESULTS ---",
    ]
    for agent_result in agent_results:
        parts.append(
            f"\n[{agent_result.dimension.upper()}] score={agent_result.score}/100"
        )
        parts.append(f"Summary: {agent_result.summary}")
        if agent_result.findings:
            parts.append("Findings:")
            for finding in agent_result.findings:
                location = f"{finding.file}:{finding.line}" if finding.line else finding.file
                parts.append(
                    f"  - [{finding.severity}] {location} - {finding.title}: "
                    f"{finding.description}"
                )
        else:
            parts.append("Findings: none")

    return "\n".join(parts)


def build_pr_context(pr: PRMetadata, static_analysis: StaticAnalysisResult) -> str:
    parts = [
        f"PR: {pr.title} by {pr.author}",
        f"{pr.owner}/{pr.repo}#{pr.number}",
        f"Base: {pr.base_branch} <- Head: {pr.head_branch}",
        f"Files changed: {pr.changed_files} (+{pr.additions}/-{pr.deletions})",
    ]
    if pr.files_truncated:
        parts.append("NOTE: file list truncated to the first 300 files.")

    parts.append("\n--- CHANGED FILES ---")
    for file in pr.files:
        parts.append(
            f"\nFILE: {file.filename} "
            f"(language={file.language}, status={file.status}, +{file.additions}/-{file.deletions})"
        )
        if file.patch:
            parts.append(file.patch)
            if file.patch_truncated:
                parts.append("(diff truncated)")
        else:
            parts.append("(no diff available - binary file or too large)")

    if static_analysis.python_files_analyzed:
        parts.append("\n--- STATIC ANALYSIS RESULTS (Python files only) ---")
        for file_result in static_analysis.files:
            parts.append(f"\nFILE: {file_result.filename}")
            if file_result.cyclomatic_complexity is not None:
                parts.append(
                    f"  Average cyclomatic complexity: {file_result.cyclomatic_complexity:.1f}"
                )
            if file_result.maintainability_index is not None:
                parts.append(
                    f"  Maintainability index: {file_result.maintainability_index:.1f}"
                )
            for issue in file_result.issues:
                parts.append(
                    f"  [{issue.tool} {issue.code}] line {issue.line}: "
                    f"{issue.message} (severity: {issue.severity})"
                )
    else:
        parts.append(
            "\n(No Python files in this PR - no static analysis tool output available. "
            "Rely on direct reasoning over the diffs above.)"
        )

    return "\n".join(parts)
