"""Review change loading and application helpers."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import ReviewApplyError
from .models import ChangeOp, ReviewChange, RoleKind


@dataclass(slots=True)
class ChangeApplyResult:
    """Result of attempting to apply one review change."""

    content: str
    applied: bool
    message: str | None = None


def _parse_change(table: dict[str, object], source: Path) -> ReviewChange:
    """Parse one review change table from TOML data."""
    target_kind_raw = table.get("target_kind")
    if not isinstance(target_kind_raw, str):
        raise ReviewApplyError(f"'target_kind' must be a string in {source}")

    try:
        target_kind = RoleKind(target_kind_raw)
    except ValueError as error:
        raise ReviewApplyError(
            f"Unsupported target kind '{target_kind_raw}' in {source}"
        ) from error

    target_slug = table.get("target_slug")
    if not isinstance(target_slug, str) or not target_slug:
        raise ReviewApplyError(f"'target_slug' must be a non-empty string in {source}")

    op_raw = table.get("op")
    if not isinstance(op_raw, str):
        raise ReviewApplyError(f"'op' must be a string in {source}")

    try:
        op = ChangeOp(op_raw)
    except ValueError as error:
        raise ReviewApplyError(f"Unsupported op '{op_raw}' in {source}") from error

    anchor = table.get("anchor")
    text = table.get("text")
    old_text = table.get("old_text")
    new_text = table.get("new_text")

    if anchor is not None and not isinstance(anchor, str):
        raise ReviewApplyError(f"'anchor' must be a string in {source}")
    if text is not None and not isinstance(text, str):
        raise ReviewApplyError(f"'text' must be a string in {source}")
    if old_text is not None and not isinstance(old_text, str):
        raise ReviewApplyError(f"'old_text' must be a string in {source}")
    if new_text is not None and not isinstance(new_text, str):
        raise ReviewApplyError(f"'new_text' must be a string in {source}")

    if op is ChangeOp.ADD and not text:
        raise ReviewApplyError(f"'text' is required for add operations in {source}")
    if op is ChangeOp.REMOVE and not text:
        raise ReviewApplyError(f"'text' is required for remove operations in {source}")
    if op is ChangeOp.MODIFY and (not old_text or new_text is None):
        raise ReviewApplyError(
            f"'old_text' and 'new_text' are required for modify operations in {source}"
        )

    return ReviewChange(
        target_kind=target_kind,
        target_slug=target_slug,
        op=op,
        anchor=anchor,
        text=text,
        old_text=old_text,
        new_text=new_text,
    )


def load_review_changes(path: Path) -> list[ReviewChange]:
    """Load proposed review changes from a TOML file."""
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    raw_changes = raw.get("changes", [])
    if not isinstance(raw_changes, list):
        raise ReviewApplyError(f"'changes' must be an array of tables in {path}")

    changes: list[ReviewChange] = []
    for change in raw_changes:
        if not isinstance(change, dict):
            raise ReviewApplyError(f"Each change entry must be a table in {path}")
        changes.append(_parse_change(change, path))
    return changes


def stub_review_changes(target_sub_roles: list[str]) -> list[ReviewChange]:
    """Create deterministic placeholder review changes for MVP workflows."""
    return [
        ReviewChange(
            target_kind=RoleKind.SUB_ROLE,
            target_slug=target,
            op=ChangeOp.ADD,
            anchor="## Evaluation Areas",
            text="- Add explicit acceptance-criteria checks for each reported issue.",
        )
        for target in target_sub_roles
    ]


def apply_change(content: str, change: ReviewChange) -> tuple[str, bool]:
    """Apply a single change operation to role text."""
    if change.target_kind is not RoleKind.SUB_ROLE:
        raise ReviewApplyError("Review updates may only target sub-role files")

    if change.op is ChangeOp.ADD:
        return _apply_add(content, change)
    if change.op is ChangeOp.REMOVE:
        return _apply_remove(content, change)
    return _apply_modify(content, change)


def apply_change_with_result(content: str, change: ReviewChange) -> ChangeApplyResult:
    """Apply one change and return status metadata for UX accounting."""
    new_content, applied = apply_change(content, change)
    if applied:
        return ChangeApplyResult(content=new_content, applied=True)

    return ChangeApplyResult(
        content=new_content,
        applied=False,
        message=_no_op_message(change, content),
    )


def _no_op_message(change: ReviewChange, original_content: str) -> str:
    """Return a user-facing no-op reason for a non-applied change."""
    if change.op in {ChangeOp.REMOVE, ChangeOp.MODIFY}:
        return "no-op (target text not found)"

    if change.anchor and change.anchor not in original_content:
        return "no-op (anchor not found; text already present)"

    return "no-op (text already present)"


def _apply_add(content: str, change: ReviewChange) -> tuple[str, bool]:
    """Apply add change."""
    if change.text is None:
        raise ReviewApplyError("add operation requires text")

    text_to_add = change.text.strip()
    if change.anchor and change.anchor in content:
        anchor_start = content.find(change.anchor)
        anchor_end = anchor_start + len(change.anchor)
        trailing = content[anchor_end:]
        expected_prefix = f"\n{text_to_add}"
        if trailing.startswith(expected_prefix):
            return content, False

        return (
            f"{content[:anchor_end]}{expected_prefix}{content[anchor_end:]}",
            True,
        )

    trimmed = content.rstrip()
    if text_to_add in trimmed:
        return content, False

    return f"{trimmed}\n\n{text_to_add}\n", True


def _apply_remove(content: str, change: ReviewChange) -> tuple[str, bool]:
    """Apply remove change."""
    if change.text is None:
        raise ReviewApplyError("remove operation requires text")
    if change.text not in content:
        return content, False

    return content.replace(change.text, "", 1), True


def _apply_modify(content: str, change: ReviewChange) -> tuple[str, bool]:
    """Apply modify change."""
    if change.old_text is None or change.new_text is None:
        raise ReviewApplyError("modify operation requires old_text and new_text")

    if change.old_text not in content:
        return content, False

    return content.replace(change.old_text, change.new_text, 1), True
