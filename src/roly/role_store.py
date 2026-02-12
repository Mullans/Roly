"""Role storage and resolution helpers."""

from __future__ import annotations

from pathlib import Path

from .errors import ConfigError, RoleNotFoundError
from .models import RoleDocument, RoleKind
from .paths import kind_dir, scope_root, slug_to_filename
from .role_parser import parse_role_file


def builtin_roles_root() -> Path:
    """Return filesystem path containing built-in roles."""
    return Path(__file__).resolve().parent / "builtin"


def _role_path(root: Path, kind: RoleKind, slug: str) -> Path:
    """Build a role file path from root/kind/slug."""
    return kind_dir(root, kind) / slug_to_filename(slug)


def load_role_from_root(
    root: Path, scope: str, kind: RoleKind, slug: str
) -> RoleDocument | None:
    """Load one role from a specific root if the file exists."""
    path = _role_path(root, kind, slug)
    if not path.exists():
        return None

    return parse_role_file(path, scope)


def resolve_role(
    *,
    kind: RoleKind,
    slug: str,
    project_root: Path,
    user_home: Path,
    project_roles_dir: str,
) -> RoleDocument:
    """Resolve a role using project > user > built-in precedence."""
    project = load_role_from_root(
        scope_root("project", project_root, user_home, project_roles_dir),
        "project",
        kind,
        slug,
    )
    if project is not None:
        return project

    user = load_role_from_root(
        scope_root("user", project_root, user_home, project_roles_dir),
        "user",
        kind,
        slug,
    )
    if user is not None:
        return user

    builtin = load_role_from_root(builtin_roles_root(), "builtin", kind, slug)
    if builtin is not None:
        return builtin

    raise RoleNotFoundError(f"Role not found ({kind}): {slug}")


def local_project_role(
    *, kind: RoleKind, slug: str, project_root: Path, project_roles_dir: str
) -> RoleDocument:
    """Load a project-local role and fail if missing."""
    root = project_root / project_roles_dir
    role = load_role_from_root(root, "project", kind, slug)
    if role is None:
        raise RoleNotFoundError(f"Project role not found ({kind}): {slug}")
    return role


def local_user_role(*, kind: RoleKind, slug: str, user_home: Path) -> RoleDocument:
    """Load a user-level role and fail if missing."""
    root = user_home / "roles"
    role = load_role_from_root(root, "user", kind, slug)
    if role is None:
        raise RoleNotFoundError(f"User role not found ({kind}): {slug}")
    return role


def local_user_role_path(*, kind: RoleKind, slug: str, user_home: Path) -> Path:
    """Return destination path for a user-level role file."""
    return _role_path(user_home / "roles", kind, slug)


def list_roles(
    *,
    project_root: Path,
    user_home: Path,
    project_roles_dir: str,
    scope_filter: str,
    kind_filter: str,
) -> list[RoleDocument]:
    """List roles across configured scopes with filters."""
    scopes: list[tuple[str, Path]] = []
    if scope_filter in {"all", "builtin"}:
        scopes.append(("builtin", builtin_roles_root()))
    if scope_filter in {"all", "user"}:
        scopes.append(("user", user_home / "roles"))
    if scope_filter in {"all", "project"}:
        scopes.append(("project", project_root / project_roles_dir))

    kinds: list[RoleKind] = []
    if kind_filter in {"all", "top-level"}:
        kinds.append(RoleKind.TOP_LEVEL)
    if kind_filter in {"all", "sub-role"}:
        kinds.append(RoleKind.SUB_ROLE)

    roles: list[RoleDocument] = []
    for scope_name, root in scopes:
        for kind in kinds:
            directory = kind_dir(root, kind)
            if not directory.exists():
                continue
            roles.extend(
                parse_role_file(file, scope_name)
                for file in sorted(directory.glob("*.md"))
            )

    return roles


def infer_role_kind(
    *,
    slug: str,
    project_root: Path,
    user_home: Path,
    project_roles_dir: str,
) -> RoleKind:
    """Infer role kind from slug and fail on ambiguity or absence."""
    matches: list[RoleKind] = []
    for kind in (RoleKind.TOP_LEVEL, RoleKind.SUB_ROLE):
        for root in (
            project_root / project_roles_dir,
            user_home / "roles",
            builtin_roles_root(),
        ):
            if _role_path(root, kind, slug).exists():
                matches.append(kind)
                break

    if not matches:
        raise RoleNotFoundError(f"Role not found: {slug}")
    if len(matches) > 1:
        raise ConfigError(
            f"Role slug '{slug}' matches multiple role kinds; provide --role-path"
        )
    return matches[0]


def infer_project_role_kind(
    *, slug: str, project_root: Path, project_roles_dir: str
) -> RoleKind:
    """Infer role kind from project-local role files."""
    matches = [
        kind
        for kind in (RoleKind.TOP_LEVEL, RoleKind.SUB_ROLE)
        if _role_path(project_root / project_roles_dir, kind, slug).exists()
    ]
    if not matches:
        raise RoleNotFoundError(f"Project role not found: {slug}")
    if len(matches) > 1:
        raise ConfigError(
            f"Project role slug '{slug}' matches multiple kinds; provide --role-path"
        )
    return matches[0]


def role_from_path(path: Path, *, scope: str = "project") -> RoleDocument:
    """Parse role file from explicit path."""
    return parse_role_file(path, scope)
