"""User role assembly logic."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from .models import OutputDefinition, OutputSection, RoleDocument, SectionType

DEFAULT_FILENAME_TEMPLATE = "review_{subrole-or-role}_{timestamp}.md"


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    """Append unique strings while preserving order."""
    seen = set(existing)
    merged = list(existing)
    for item in additions:
        if item not in seen:
            seen.add(item)
            merged.append(item)
    return merged


def merge_output_definitions(
    top_role: RoleDocument, sub_roles: list[RoleDocument]
) -> OutputDefinition:
    """Merge output definitions using deterministic section-key semantics."""
    merged_sections: list[OutputSection] = []
    index_by_key: dict[str, int] = {}

    ordered_roles = [top_role, *sub_roles]
    for role in ordered_roles:
        for section in role.output.sections:
            normalized = section.normalized_key
            index = index_by_key.get(normalized)
            if index is None:
                merged_sections.append(
                    OutputSection(
                        key=section.key,
                        type=section.type,
                        guidance=list(section.guidance),
                        fields=list(section.fields),
                        item_contributions=list(section.item_contributions),
                    )
                )
                index_by_key[normalized] = len(merged_sections) - 1
                continue

            current = merged_sections[index]
            if current.type is not section.type:
                note = (
                    "Conflict detected: section type mismatch encountered during merge; "
                    f"kept '{current.type.value}' from first definition."
                )
                current.guidance = _append_unique(current.guidance, [note])
                continue

            current.guidance = _append_unique(current.guidance, section.guidance)
            if current.type is SectionType.LIST:
                current.fields = _append_unique(current.fields, section.fields)
                current.item_contributions = _append_unique(
                    current.item_contributions,
                    section.item_contributions,
                )

    filename_template: str | None = None
    for role in sub_roles:
        if role.output.filename_template:
            filename_template = role.output.filename_template
            break

    if filename_template is None:
        filename_template = top_role.output.filename_template

    return OutputDefinition(
        filename_template=filename_template, sections=merged_sections
    )


def resolve_output_filename(
    *,
    output_override: Path | None,
    config_output_filename: str | None,
    merged_output: OutputDefinition,
    top_role: RoleDocument,
    sub_roles: list[RoleDocument],
    now: datetime | None = None,
) -> str:
    """Resolve output filename from explicit overrides and defaults."""
    if output_override is not None:
        return output_override.name

    if config_output_filename:
        return config_output_filename

    template = merged_output.filename_template or DEFAULT_FILENAME_TEMPLATE

    timestamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    token_value = sub_roles[0].slug if sub_roles else top_role.slug

    return template.replace("{subrole-or-role}", token_value).replace(
        "{timestamp}", timestamp
    )


def render_assembled_role(
    *,
    user_role_name: str,
    top_role: RoleDocument,
    sub_roles: list[RoleDocument],
    merged_output: OutputDefinition,
) -> str:
    """Render assembled user role markdown file content."""
    lines: list[str] = []
    lines.append(f"# User Role: {user_role_name}")
    lines.append("")
    lines.append("## Composition")
    lines.append(f"- Top-Level Role: `{top_role.slug}` ({top_role.source_scope})")
    if sub_roles:
        lines.append("- Sub-Roles:")
        lines.extend(
            f"  - `{sub_role.slug}` ({sub_role.source_scope})" for sub_role in sub_roles
        )
    else:
        lines.append("- Sub-Roles: (none)")
    lines.append("")

    lines.append("## Resolved Output Definition")
    for section in merged_output.sections:
        lines.append("")
        lines.append(f"### {section.key} ({section.type.value})")
        if section.guidance:
            lines.append("- Guidance:")
            lines.extend(f"  - {guidance}" for guidance in section.guidance)
        if section.type is SectionType.LIST and section.fields:
            lines.append("- Fields:")
            lines.extend(f"  - {field_name}" for field_name in section.fields)
        if section.type is SectionType.LIST and section.item_contributions:
            lines.append("- Item Contributions:")
            lines.extend(
                f"  - {contribution}" for contribution in section.item_contributions
            )

    lines.append("")
    lines.append("## Instructions")
    lines.append("")
    lines.append(f"### Top-Level Role: {top_role.name}")
    lines.append(top_role.body.rstrip())

    for sub_role in sub_roles:
        lines.append("")
        lines.append(f"### Sub-Role: {sub_role.name}")
        lines.append(sub_role.body.rstrip())

    lines.append("")
    return "\n".join(lines)


def write_assembled_role(*, content: str, output_dir: Path, filename: str) -> Path:
    """Write assembled role content to disk and return resulting path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / filename
    destination.write_text(content, encoding="utf-8")
    return destination


def clone_section(section: OutputSection) -> OutputSection:
    """Return a deep-ish clone of an output section."""
    return replace(
        section,
        guidance=list(section.guidance),
        fields=list(section.fields),
        item_contributions=list(section.item_contributions),
    )
