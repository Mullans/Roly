from pathlib import Path

import pytest

from roly.errors import RoleParseError
from roly.models import RoleKind, SectionType
from roly.role_parser import parse_role_file


def test_parse_role_file_success(tmp_path: Path):
    role_file = tmp_path / "reviewer.md"
    role_file.write_text(
        """+++
kind = "top-level"
name = "Reviewer"
slug = "reviewer"
version = "1.0.0"

[output]

[[output.sections]]
key = "Issues"
type = "list"
guidance = ["foo"]
fields = ["severity"]
item_contributions = ["bar"]
+++

# Body
""",
        encoding="utf-8",
    )

    parsed = parse_role_file(role_file, "project")

    assert parsed.kind is RoleKind.TOP_LEVEL
    assert parsed.slug == "reviewer"
    assert parsed.source_scope == "project"
    assert len(parsed.output.sections) == 1
    section = parsed.output.sections[0]
    assert section.type is SectionType.LIST
    assert section.fields == ["severity"]


def test_parse_role_file_requires_front_matter(tmp_path: Path):
    role_file = tmp_path / "invalid.md"
    role_file.write_text("# no front matter", encoding="utf-8")

    with pytest.raises(RoleParseError):
        parse_role_file(role_file, "project")


def test_parse_role_file_errors_for_invalid_kind(tmp_path: Path):
    role_file = tmp_path / "invalid-kind.md"
    role_file.write_text(
        """+++
kind = "unsupported"
name = "Invalid Kind"
slug = "invalid-kind"
version = "1.0.0"
+++

# Body
""",
        encoding="utf-8",
    )

    with pytest.raises(RoleParseError):
        parse_role_file(role_file, "project")


def test_parse_role_file_requires_closing_front_matter_delimiter(tmp_path: Path):
    role_file = tmp_path / "missing-close.md"
    role_file.write_text(
        """+++
kind = "top-level"
name = "Missing Close"
slug = "missing-close"
version = "1.0.0"

# Body
""",
        encoding="utf-8",
    )

    with pytest.raises(RoleParseError):
        parse_role_file(role_file, "project")


def test_parse_role_file_errors_for_invalid_section_type(tmp_path: Path):
    role_file = tmp_path / "invalid-section.md"
    role_file.write_text(
        """+++
kind = "top-level"
name = "Invalid Section"
slug = "invalid-section"
version = "1.0.0"

[output]

[[output.sections]]
key = "Summary"
type = "unsupported"
+++

# Body
""",
        encoding="utf-8",
    )

    with pytest.raises(RoleParseError):
        parse_role_file(role_file, "project")


def test_parse_role_file_requires_sub_role_dependency_field(tmp_path: Path):
    role_file = tmp_path / "sub-role-missing-dependency.md"
    role_file.write_text(
        """+++
kind = "sub-role"
name = "Missing Dependency"
slug = "missing-dependency"
version = "1.0.0"
+++

# Body
""",
        encoding="utf-8",
    )

    with pytest.raises(RoleParseError):
        parse_role_file(role_file, "project")
