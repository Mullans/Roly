"""Role file parsing utilities."""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import RoleParseError
from .models import OutputDefinition, OutputSection, RoleDocument, RoleKind, SectionType


def _extract_front_matter(raw_text: str, source_path: Path) -> tuple[str, str]:
    """Extract TOML front matter and body from a role markdown document."""
    lines = raw_text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "+++":
        raise RoleParseError(
            f"Role file must start with TOML front matter: {source_path}"
        )

    closing_index = -1
    for index in range(1, len(lines)):
        if lines[index].strip() == "+++":
            closing_index = index
            break

    if closing_index == -1:
        raise RoleParseError(
            f"Role file is missing front matter closing delimiter: {source_path}"
        )

    front_matter = "".join(lines[1:closing_index])
    body = "".join(lines[closing_index + 1 :]).lstrip("\n")
    return front_matter, body


def _expect_string(table: dict[str, object], key: str, source_path: Path) -> str:
    """Read required string keys from parsed TOML front matter."""
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RoleParseError(f"'{key}' must be a non-empty string in {source_path}")
    return value


def _read_string_list(value: object, key: str, source_path: Path) -> list[str]:
    """Read optional array-of-string values from parsed TOML."""
    if value is None:
        return []

    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RoleParseError(f"'{key}' must be an array of strings in {source_path}")

    return list(value)


def parse_role_file(path: Path, source_scope: str) -> RoleDocument:
    """Parse a role markdown file into a typed role document."""
    raw_text = path.read_text(encoding="utf-8")
    front_matter_text, body = _extract_front_matter(raw_text, path)

    try:
        table = tomllib.loads(front_matter_text)
    except tomllib.TOMLDecodeError as error:
        raise RoleParseError(f"Invalid TOML front matter in {path}: {error}") from error

    kind_raw = _expect_string(table, "kind", path)
    try:
        kind = RoleKind(kind_raw)
    except ValueError as error:
        raise RoleParseError(f"Unsupported role kind '{kind_raw}' in {path}") from error

    name = _expect_string(table, "name", path)
    slug = _expect_string(table, "slug", path)
    version = _expect_string(table, "version", path)
    depends_on_top_level = table.get("depends_on_top_level")
    if kind is RoleKind.SUB_ROLE:
        if (
            not isinstance(depends_on_top_level, str)
            or not depends_on_top_level.strip()
        ):
            raise RoleParseError(
                f"'depends_on_top_level' must be a non-empty string for sub-role in {path}"
            )
    elif depends_on_top_level is not None and not isinstance(depends_on_top_level, str):
        raise RoleParseError(f"'depends_on_top_level' must be a string in {path}")

    raw_output = table.get("output", {})
    if raw_output and not isinstance(raw_output, dict):
        raise RoleParseError(f"'output' must be a table in {path}")

    filename_template: str | None = None
    sections: list[OutputSection] = []

    if isinstance(raw_output, dict):
        filename_raw = raw_output.get("filename_template")
        if filename_raw is not None:
            if not isinstance(filename_raw, str):
                raise RoleParseError(
                    f"'output.filename_template' must be a string in {path}"
                )
            filename_template = filename_raw

        sections_raw = raw_output.get("sections", [])
        if not isinstance(sections_raw, list):
            raise RoleParseError(
                f"'output.sections' must be an array of tables in {path}"
            )

        for section in sections_raw:
            if not isinstance(section, dict):
                raise RoleParseError(f"Each output section must be a table in {path}")

            key = _expect_string(section, "key", path)
            section_type_raw = _expect_string(section, "type", path)
            try:
                section_type = SectionType(section_type_raw)
            except ValueError as error:
                raise RoleParseError(
                    f"Unsupported section type '{section_type_raw}' in {path}"
                ) from error

            guidance = _read_string_list(section.get("guidance"), "guidance", path)
            fields = _read_string_list(section.get("fields"), "fields", path)
            item_contributions = _read_string_list(
                section.get("item_contributions"), "item_contributions", path
            )

            sections.append(
                OutputSection(
                    key=key,
                    type=section_type,
                    guidance=guidance,
                    fields=fields,
                    item_contributions=item_contributions,
                )
            )

    output = OutputDefinition(filename_template=filename_template, sections=sections)

    return RoleDocument(
        kind=kind,
        name=name,
        slug=slug,
        version=version,
        depends_on_top_level=depends_on_top_level.strip()
        if isinstance(depends_on_top_level, str)
        else None,
        output=output,
        body=body,
        source_scope=source_scope,
        source_path=path,
    )
