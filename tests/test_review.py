from pathlib import Path

import pytest

from roly.errors import ReviewApplyError
from roly.models import ChangeOp, ReviewChange, RoleKind
from roly.review import apply_change, apply_change_with_result, load_review_changes


def test_apply_modify_change_updates_text():
    content = "alpha beta gamma"
    change = ReviewChange(
        target_kind=RoleKind.SUB_ROLE,
        target_slug="code-review",
        op=ChangeOp.MODIFY,
        old_text="beta",
        new_text="delta",
    )

    new_content, applied = apply_change(content, change)

    assert applied is True
    assert new_content == "alpha delta gamma"


def test_load_review_changes_from_file(tmp_path: Path):
    change_file = tmp_path / "changes.toml"
    change_file.write_text(
        """[[changes]]
target_kind = "sub-role"
target_slug = "code-review"
op = "add"
anchor = "## Evaluation Areas"
text = "- extra check"
""",
        encoding="utf-8",
    )

    changes = load_review_changes(change_file)

    assert len(changes) == 1
    assert changes[0].target_slug == "code-review"


def test_apply_add_with_anchor_is_idempotent():
    content = "# Code Review\n\n## Evaluation Areas\n- existing item\n"
    change = ReviewChange(
        target_kind=RoleKind.SUB_ROLE,
        target_slug="code-review",
        op=ChangeOp.ADD,
        anchor="## Evaluation Areas",
        text="- extra check",
    )

    updated_once, applied_once = apply_change(content, change)
    updated_twice, applied_twice = apply_change(updated_once, change)

    assert applied_once is True
    assert applied_twice is False
    assert updated_twice.count("- extra check") == 1


def test_apply_change_with_result_reports_noop_target_not_found():
    content = "alpha beta gamma"
    change = ReviewChange(
        target_kind=RoleKind.SUB_ROLE,
        target_slug="code-review",
        op=ChangeOp.MODIFY,
        old_text="delta",
        new_text="epsilon",
    )

    result = apply_change_with_result(content, change)

    assert result.applied is False
    assert result.content == content
    assert result.message == "no-op (target text not found)"


def test_apply_add_without_anchor_appends_text():
    content = "# Role Body\n"
    change = ReviewChange(
        target_kind=RoleKind.SUB_ROLE,
        target_slug="code-review",
        op=ChangeOp.ADD,
        text="- appended item",
    )

    updated, applied = apply_change(content, change)

    assert applied is True
    assert updated.endswith("- appended item\n")


def test_apply_remove_only_removes_first_exact_match():
    content = "alpha\nbeta\nbeta\n"
    change = ReviewChange(
        target_kind=RoleKind.SUB_ROLE,
        target_slug="code-review",
        op=ChangeOp.REMOVE,
        text="beta",
    )

    updated, applied = apply_change(content, change)

    assert applied is True
    assert updated.count("beta") == 1


def test_apply_modify_only_replaces_first_exact_match():
    content = "alpha beta beta"
    change = ReviewChange(
        target_kind=RoleKind.SUB_ROLE,
        target_slug="code-review",
        op=ChangeOp.MODIFY,
        old_text="beta",
        new_text="delta",
    )

    updated, applied = apply_change(content, change)

    assert applied is True
    assert updated == "alpha delta beta"


def test_apply_change_rejects_non_sub_role_target():
    change = ReviewChange(
        target_kind=RoleKind.TOP_LEVEL,
        target_slug="reviewer",
        op=ChangeOp.ADD,
        text="- change",
    )

    with pytest.raises(ReviewApplyError):
        apply_change("body", change)


def test_apply_change_with_result_reports_anchor_not_found_noop():
    content = "# Body\n\n- already present"
    change = ReviewChange(
        target_kind=RoleKind.SUB_ROLE,
        target_slug="code-review",
        op=ChangeOp.ADD,
        anchor="## Missing Anchor",
        text="- already present",
    )

    result = apply_change_with_result(content, change)

    assert result.applied is False
    assert result.message == "no-op (anchor not found; text already present)"
