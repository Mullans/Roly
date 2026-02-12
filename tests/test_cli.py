from __future__ import annotations

import re
from pathlib import Path

from typer.testing import CliRunner

from roly.cli import app
from roly.models import RoleKind
from roly.paths import kind_dir

runner = CliRunner()


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
[output]

[[output.sections]]
key = "Issues"
type = "list"
guidance = ["guidance"]
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


def _role_root(path: Path) -> Path:
    return path / ".roly" / "roles"


def _write_config(path: Path, content: str) -> Path:
    config = path / "roly.config"
    config.write_text(content, encoding="utf-8")
    return config


def test_setup_none_writes_default_prompt_and_persists_config(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--no-color",
            "setup",
            "--agent",
            "none",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    prompt_path = tmp_path / "roly_review_skill.md"
    assert prompt_path.exists()
    assert "roly_skill_id: roly-review-skill" in prompt_path.read_text(encoding="utf-8")
    config_text = (tmp_path / "roly.config").read_text(encoding="utf-8")
    assert "[setup]" in config_text
    assert 'agent = "none"' in config_text


def test_setup_none_interactive_wizard(tmp_path: Path):
    interactive_input = "none\ncustom/skill.md\ny\ny\n"
    result = runner.invoke(
        app,
        ["--project-root", str(tmp_path), "--no-color", "setup"],
        input=interactive_input,
    )

    assert result.exit_code == 0
    assert (tmp_path / "custom" / "skill.md").exists()


def test_setup_codex_installs_skill(tmp_path: Path):
    codex_root = tmp_path / "codex-skills"
    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--no-color",
            "setup",
            "--agent",
            "codex",
            "--codex-dir",
            str(codex_root),
            "--yes",
        ],
    )

    assert result.exit_code == 0
    skill_path = codex_root / "roly-review" / "SKILL.md"
    assert skill_path.exists()
    assert "name: roly-review" in skill_path.read_text(encoding="utf-8")


def test_list_shows_builtin_roles_no_color(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "list",
        ],
    )

    assert result.exit_code == 0
    assert "reviewer" in result.stdout
    assert "code-review" in result.stdout
    assert "\x1b[" not in result.stdout


def test_assemble_errors_without_config_or_role(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "assemble",
        ],
    )

    assert result.exit_code == 1
    assert "No config found and no --role values provided" in result.stdout


def test_assemble_ad_hoc_infers_dependency_and_name(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "assemble",
            "--role",
            "code-review",
            "--name",
            "my-review-role",
        ],
    )

    assert result.exit_code == 0
    generated = sorted(
        (tmp_path / ".roly" / "generated").glob("review_code-review_*.md")
    )
    assert len(generated) == 1
    content = generated[0].read_text(encoding="utf-8")
    assert "# User Role: my-review-role" in content
    assert "`reviewer`" in content
    assert "`code-review`" in content


def test_assemble_ad_hoc_rejects_conflicting_sub_role_dependencies(tmp_path: Path):
    project_roles_root = _role_root(tmp_path)
    _write_role_file(
        project_roles_root,
        RoleKind.TOP_LEVEL,
        "auditor",
        "# Auditor",
    )
    other_sub = kind_dir(project_roles_root, RoleKind.SUB_ROLE) / "audit-only.md"
    other_sub.parent.mkdir(parents=True, exist_ok=True)
    other_sub.write_text(
        """+++
kind = "sub-role"
name = "Audit Only"
slug = "audit-only"
version = "1.0.0"
depends_on_top_level = "auditor"
+++

# Audit Only
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "assemble",
            "--role",
            "code-review",
            "--role",
            "audit-only",
        ],
    )

    assert result.exit_code == 1
    assert "conflicting top-level dependencies" in result.stdout


def test_assemble_config_mode_accepts_roles_list(tmp_path: Path):
    _write_config(
        tmp_path,
        """version = 1

[[user_roles]]
name = "reviewer-default"
roles = ["code-review", "project-audit"]
output_filename = "from-config.md"
""",
    )

    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "assemble",
        ],
    )

    assert result.exit_code == 0
    output_file = tmp_path / ".roly" / "generated" / "from-config.md"
    assert output_file.exists()


def test_assemble_config_legacy_fields_still_work(tmp_path: Path):
    _write_config(
        tmp_path,
        """version = 1

[[user_roles]]
name = "legacy"
top_level_role = "reviewer"
sub_roles = ["code-review"]
output_filename = "legacy.md"
""",
    )
    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "assemble",
        ],
    )

    assert result.exit_code == 0
    assert "legacy top_level_role/sub_roles" in result.stdout
    assert (tmp_path / ".roly" / "generated" / "legacy.md").exists()


def test_diff_infers_role_kind_from_slug(tmp_path: Path):
    project_root = _role_root(tmp_path)
    user_root = (tmp_path / "home") / "roles"
    _write_role_file(project_root, RoleKind.SUB_ROLE, "code-review", "project body")
    _write_role_file(user_root, RoleKind.SUB_ROLE, "code-review", "user body")

    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "diff",
            "--role",
            "code-review",
        ],
    )

    assert result.exit_code == 0
    assert "+project body" in result.stdout
    assert "-user body" in result.stdout


def test_diff_supports_role_path_escape_hatch(tmp_path: Path):
    project_root = _role_root(tmp_path)
    user_root = (tmp_path / "home") / "roles"
    project_file = _write_role_file(
        project_root, RoleKind.TOP_LEVEL, "reviewer", "project top"
    )
    _write_role_file(user_root, RoleKind.TOP_LEVEL, "reviewer", "user top")

    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "diff",
            "--role-path",
            str(project_file),
        ],
    )

    assert result.exit_code == 0
    assert "+project top" in result.stdout


def test_promote_infers_kind_and_overwrites(tmp_path: Path):
    project_root = _role_root(tmp_path)
    user_root = (tmp_path / "home") / "roles"
    project_role = _write_role_file(
        project_root, RoleKind.SUB_ROLE, "code-review", "project-promoted"
    )
    _write_role_file(user_root, RoleKind.SUB_ROLE, "code-review", "old-user")

    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "promote",
            "--role",
            "code-review",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    user_file = user_root / "sub_roles" / "code-review.md"
    assert user_file.read_text(encoding="utf-8") == project_role.read_text(
        encoding="utf-8"
    )


def test_review_requires_changes_file_or_stub(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "review",
            "--target-sub-role",
            "code-review",
        ],
    )
    assert result.exit_code == 1
    assert "Provide --changes-file or pass --use-stub" in result.stdout


def test_review_stub_flow_still_works_with_flag(tmp_path: Path):
    project_root = _role_root(tmp_path)
    role_file = _write_role_file(
        project_root,
        RoleKind.SUB_ROLE,
        "code-review",
        "# Code Review\n\n## Evaluation Areas\n- existing item",
    )
    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "review",
            "--target-sub-role",
            "code-review",
            "--use-stub",
        ],
        input="y\n",
    )

    assert result.exit_code == 0
    updated = role_file.read_text(encoding="utf-8")
    assert "acceptance-criteria checks" in updated


def test_review_quit_reports_skipped(tmp_path: Path):
    project_root = _role_root(tmp_path)
    _write_role_file(
        project_root,
        RoleKind.SUB_ROLE,
        "code-review",
        "# Code Review\n\n## Evaluation Areas\n- existing item",
    )
    result = runner.invoke(
        app,
        [
            "--project-root",
            str(tmp_path),
            "--user-home",
            str(tmp_path / "home"),
            "--no-color",
            "review",
            "--target-sub-role",
            "code-review",
            "--use-stub",
        ],
        input="q\n",
    )

    assert result.exit_code == 0
    assert re.search(r"skipped: [1-9]", result.stdout)
