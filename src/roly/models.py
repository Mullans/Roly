"""Data models for Roly."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class RoleKind(StrEnum):
    """Supported role kinds."""

    TOP_LEVEL = "top-level"
    SUB_ROLE = "sub-role"


class SectionType(StrEnum):
    """Supported output section types."""

    TEXT = "text"
    LIST = "list"


class ChangeOp(StrEnum):
    """Supported review change operations."""

    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"


@dataclass(slots=True)
class OutputSection:
    """Output section definition."""

    key: str
    type: SectionType
    guidance: list[str] = field(default_factory=list)
    fields: list[str] = field(default_factory=list)
    item_contributions: list[str] = field(default_factory=list)

    @property
    def normalized_key(self) -> str:
        """Return case-normalized key used for deterministic merging."""
        return self.key.strip().casefold()


@dataclass(slots=True)
class OutputDefinition:
    """Output definition merged from one or more roles."""

    filename_template: str | None = None
    sections: list[OutputSection] = field(default_factory=list)


@dataclass(slots=True)
class RoleDocument:
    """Parsed role document with metadata and source context."""

    kind: RoleKind
    name: str
    slug: str
    version: str
    depends_on_top_level: str | None
    output: OutputDefinition
    body: str
    source_scope: str
    source_path: Path


@dataclass(slots=True)
class PathsConfig:
    """Path settings from roly.config."""

    project_roles_dir: str = ".roly/roles"
    output_dir: str = ".roly/generated"


@dataclass(slots=True)
class UserRoleConfig:
    """A named user role assembly definition from config."""

    name: str
    roles: list[str] = field(default_factory=list)
    top_level_role: str | None = None
    sub_roles: list[str] = field(default_factory=list)
    output_filename: str | None = None

    def resolved_roles(self) -> list[str]:
        """Return normalized role slugs, preferring the new `roles` field."""
        if self.roles:
            return list(self.roles)

        legacy: list[str] = []
        if self.top_level_role:
            legacy.append(self.top_level_role)
        legacy.extend(self.sub_roles)
        return legacy


@dataclass(slots=True)
class SetupConfig:
    """Persisted setup defaults from roly.config."""

    agent: str = "none"
    skill_dir: str | None = None
    codex_dir: str | None = None
    roly_home: str | None = None


@dataclass(slots=True)
class RolyConfig:
    """Project configuration loaded from roly.config."""

    version: int
    paths: PathsConfig = field(default_factory=PathsConfig)
    setup: SetupConfig = field(default_factory=SetupConfig)
    user_roles: list[UserRoleConfig] = field(default_factory=list)


@dataclass(slots=True)
class ReviewChange:
    """A proposed edit to a sub-role file."""

    target_kind: RoleKind
    target_slug: str
    op: ChangeOp
    anchor: str | None = None
    text: str | None = None
    old_text: str | None = None
    new_text: str | None = None
