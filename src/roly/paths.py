"""Filesystem path helpers for Roly."""

from __future__ import annotations

from pathlib import Path

from .models import RoleKind

DEFAULT_PROJECT_ROLES_DIR = ".roly/roles"
DEFAULT_OUTPUT_DIR = ".roly/generated"


def config_path(project_root: Path) -> Path:
    """Return the default config path for a project root."""
    return project_root / "roly.config"


def scope_root(
    scope: str, project_root: Path, user_home: Path, project_roles_dir: str
) -> Path:
    """Return role root path for the given scope name."""
    if scope == "project":
        return project_root / project_roles_dir
    if scope == "user":
        return user_home / "roles"

    raise ValueError(f"unsupported scope: {scope}")


def kind_dir(root: Path, kind: RoleKind) -> Path:
    """Return the directory containing role files for the given kind."""
    if kind is RoleKind.TOP_LEVEL:
        return root / "top_level"

    return root / "sub_roles"


def slug_to_filename(slug: str) -> str:
    """Return canonical role filename for a slug."""
    return f"{slug}.md"
