from datetime import UTC, datetime
from pathlib import Path

from roly.assembler import merge_output_definitions, resolve_output_filename
from roly.models import (
    OutputDefinition,
    OutputSection,
    RoleDocument,
    RoleKind,
    SectionType,
)


def _role(
    *,
    kind: RoleKind,
    slug: str,
    sections: list[OutputSection],
    filename_template: str | None = None,
) -> RoleDocument:
    return RoleDocument(
        kind=kind,
        name=slug,
        slug=slug,
        version="1.0.0",
        depends_on_top_level="reviewer" if kind is RoleKind.SUB_ROLE else None,
        output=OutputDefinition(filename_template=filename_template, sections=sections),
        body=f"Body for {slug}",
        source_scope="builtin",
        source_path=Path(f"{slug}.md"),
    )


def test_merge_shared_issues_list_contributions():
    top = _role(
        kind=RoleKind.TOP_LEVEL,
        slug="reviewer",
        filename_template="review_{subrole-or-role}_{timestamp}.md",
        sections=[
            OutputSection(
                key="Issues",
                type=SectionType.LIST,
                guidance=["top guidance"],
                fields=["severity"],
            )
        ],
    )
    code = _role(
        kind=RoleKind.SUB_ROLE,
        slug="code-review",
        sections=[
            OutputSection(
                key="Issues",
                type=SectionType.LIST,
                guidance=["code guidance"],
                fields=["evidence"],
                item_contributions=["code contribution"],
            )
        ],
    )
    audit = _role(
        kind=RoleKind.SUB_ROLE,
        slug="project-audit",
        sections=[
            OutputSection(
                key="issues",
                type=SectionType.LIST,
                guidance=["audit guidance"],
                fields=["plan_reference"],
                item_contributions=["audit contribution"],
            )
        ],
    )

    merged = merge_output_definitions(top, [code, audit])

    assert len(merged.sections) == 1
    issues = merged.sections[0]
    assert issues.guidance == ["top guidance", "code guidance", "audit guidance"]
    assert issues.fields == ["severity", "evidence", "plan_reference"]
    assert issues.item_contributions == ["code contribution", "audit contribution"]


def test_default_filename_uses_first_sub_role_slug_and_timestamp():
    top = _role(
        kind=RoleKind.TOP_LEVEL,
        slug="reviewer",
        filename_template="review_{subrole-or-role}_{timestamp}.md",
        sections=[],
    )
    sub = _role(kind=RoleKind.SUB_ROLE, slug="code-review", sections=[])
    merged = merge_output_definitions(top, [sub])

    filename = resolve_output_filename(
        output_override=None,
        config_output_filename=None,
        merged_output=merged,
        top_role=top,
        sub_roles=[sub],
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert filename == "review_code-review_20260101T000000Z.md"


def test_merge_type_conflict_keeps_first_type_and_adds_guidance_note():
    top = _role(
        kind=RoleKind.TOP_LEVEL,
        slug="reviewer",
        sections=[
            OutputSection(
                key="Summary",
                type=SectionType.TEXT,
                guidance=["text guidance"],
            )
        ],
    )
    conflicting_sub = _role(
        kind=RoleKind.SUB_ROLE,
        slug="code-review",
        sections=[
            OutputSection(
                key="summary",
                type=SectionType.LIST,
                guidance=["list guidance"],
                fields=["severity"],
            )
        ],
    )

    merged = merge_output_definitions(top, [conflicting_sub])

    assert len(merged.sections) == 1
    summary = merged.sections[0]
    assert summary.type is SectionType.TEXT
    assert any(
        "Conflict detected: section type mismatch" in item for item in summary.guidance
    )


def test_filename_resolution_prefers_config_output_filename():
    top = _role(
        kind=RoleKind.TOP_LEVEL,
        slug="reviewer",
        filename_template="top_{timestamp}.md",
        sections=[],
    )
    sub = _role(
        kind=RoleKind.SUB_ROLE,
        slug="code-review",
        filename_template="sub_{timestamp}.md",
        sections=[],
    )
    merged = merge_output_definitions(top, [sub])

    filename = resolve_output_filename(
        output_override=None,
        config_output_filename="from-config.md",
        merged_output=merged,
        top_role=top,
        sub_roles=[sub],
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert filename == "from-config.md"


def test_filename_resolution_uses_default_template_without_role_templates():
    top = _role(
        kind=RoleKind.TOP_LEVEL,
        slug="reviewer",
        sections=[],
    )
    merged = merge_output_definitions(top, [])

    filename = resolve_output_filename(
        output_override=None,
        config_output_filename=None,
        merged_output=merged,
        top_role=top,
        sub_roles=[],
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert filename == "review_reviewer_20260101T000000Z.md"
