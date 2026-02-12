from pathlib import Path

from roly.models import RoleKind
from roly.paths import kind_dir
from roly.role_store import list_roles, resolve_role


def _write_role_file(root: Path, kind: RoleKind, slug: str, body: str) -> Path:
    dependency_line = (
        'depends_on_top_level = "reviewer"\n' if kind is RoleKind.SUB_ROLE else ""
    )
    path = kind_dir(root, kind) / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """+++
kind = "{kind}"
name = "{name}"
slug = "{slug}"
version = "1.0.0"
{dependency_line}
+++

{body}
""".format(
            kind=kind.value,
            name=slug.replace("-", " ").title(),
            slug=slug,
            dependency_line=dependency_line,
            body=body,
        ),
        encoding="utf-8",
    )
    return path


def test_resolve_role_prefers_project_over_user_and_builtin(tmp_path: Path):
    project_root = tmp_path
    user_home = tmp_path / "home"
    _write_role_file(
        user_home / "roles",
        RoleKind.TOP_LEVEL,
        "reviewer",
        "user-level reviewer body",
    )
    _write_role_file(
        project_root / ".roly" / "roles",
        RoleKind.TOP_LEVEL,
        "reviewer",
        "project-level reviewer body",
    )

    role = resolve_role(
        kind=RoleKind.TOP_LEVEL,
        slug="reviewer",
        project_root=project_root,
        user_home=user_home,
        project_roles_dir=".roly/roles",
    )

    assert role.source_scope == "project"
    assert "project-level reviewer body" in role.body


def test_resolve_role_prefers_user_when_project_missing(tmp_path: Path):
    project_root = tmp_path
    user_home = tmp_path / "home"
    _write_role_file(
        user_home / "roles",
        RoleKind.SUB_ROLE,
        "code-review",
        "user-level code-review body",
    )

    role = resolve_role(
        kind=RoleKind.SUB_ROLE,
        slug="code-review",
        project_root=project_root,
        user_home=user_home,
        project_roles_dir=".roly/roles",
    )

    assert role.source_scope == "user"
    assert "user-level code-review body" in role.body


def test_resolve_role_falls_back_to_builtin(tmp_path: Path):
    role = resolve_role(
        kind=RoleKind.TOP_LEVEL,
        slug="reviewer",
        project_root=tmp_path,
        user_home=tmp_path / "home",
        project_roles_dir=".roly/roles",
    )

    assert role.source_scope == "builtin"
    assert role.slug == "reviewer"


def test_list_roles_honors_scope_and_kind_filters(tmp_path: Path):
    project_root = tmp_path
    user_home = tmp_path / "home"
    _write_role_file(
        project_root / ".roly" / "roles",
        RoleKind.SUB_ROLE,
        "project-only",
        "project body",
    )
    _write_role_file(
        user_home / "roles",
        RoleKind.TOP_LEVEL,
        "user-only-top",
        "user body",
    )

    project_sub_roles = list_roles(
        project_root=project_root,
        user_home=user_home,
        project_roles_dir=".roly/roles",
        scope_filter="project",
        kind_filter="sub-role",
    )
    assert {(role.source_scope, role.slug) for role in project_sub_roles} == {
        ("project", "project-only")
    }

    user_top_roles = list_roles(
        project_root=project_root,
        user_home=user_home,
        project_roles_dir=".roly/roles",
        scope_filter="user",
        kind_filter="top-level",
    )
    assert {(role.source_scope, role.slug) for role in user_top_roles} == {
        ("user", "user-only-top")
    }
