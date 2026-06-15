import re

HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def changed_lines(patch: str | None) -> set[int]:
    if not patch:
        return set()

    changed: set[int] = set()
    current_line = 0

    for line in patch.splitlines():
        header_match = HUNK_HEADER.match(line)
        if header_match:
            current_line = int(header_match.group(1))
            continue

        if line.startswith("+") and not line.startswith("+++"):
            changed.add(current_line)
            current_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
        else:
            current_line += 1

    return changed
