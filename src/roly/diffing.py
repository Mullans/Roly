"""Diff helpers for Roly CLI."""

from __future__ import annotations

from difflib import unified_diff


def build_unified_diff(
    *,
    before: str,
    after: str,
    from_label: str,
    to_label: str,
) -> list[str]:
    """Build a unified diff between two text blobs."""
    return list(
        unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=from_label,
            tofile=to_label,
            lineterm="",
        )
    )


def classify_diff_line(line: str) -> str:
    """Classify a diff line for CLI color rendering."""
    if line.startswith(("+++", "---", "@@")):
        return "meta"
    if line.startswith("+"):
        return "add"
    if line.startswith("-"):
        return "remove"
    return "context"
