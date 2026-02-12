"""Configuration loading for roly.config."""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import ConfigError
from .models import PathsConfig, RolyConfig, SetupConfig, UserRoleConfig
from .paths import DEFAULT_OUTPUT_DIR, DEFAULT_PROJECT_ROLES_DIR


def _expect_string(
    data: dict[str, object], key: str, *, required: bool = True
) -> str | None:
    """Read a string key from a TOML dictionary."""
    value = data.get(key)
    if value is None:
        if required:
            raise ConfigError(f"Missing required key '{key}'")
        return None

    if not isinstance(value, str):
        raise ConfigError(f"Expected '{key}' to be a string")

    return value


def _expect_list_of_strings(data: dict[str, object], key: str) -> list[str]:
    """Read a list[str] key from a TOML dictionary."""
    raw = data.get(key)
    if raw is None:
        return []

    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ConfigError(f"Expected '{key}' to be an array of strings")

    return list(raw)


def _render_toml_string(value: str) -> str:
    """Render one TOML string literal."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _render_toml_string_list(values: list[str]) -> str:
    """Render one TOML list[str] literal."""
    rendered = ", ".join(_render_toml_string(value) for value in values)
    return f"[{rendered}]"


def _parse_setup(raw_setup: object) -> SetupConfig:
    """Parse optional [setup] table."""
    setup = SetupConfig()
    if raw_setup is None:
        return setup
    if not isinstance(raw_setup, dict):
        raise ConfigError("'setup' must be a table")

    agent = _expect_string(raw_setup, "agent", required=False)
    if agent is not None:
        if agent not in {"none", "codex"}:
            raise ConfigError("'setup.agent' must be 'none' or 'codex'")
        setup.agent = agent

    setup.skill_dir = _expect_string(raw_setup, "skill_dir", required=False)
    setup.codex_dir = _expect_string(raw_setup, "codex_dir", required=False)
    setup.roly_home = _expect_string(raw_setup, "roly_home", required=False)
    return setup


def _parse_user_role(entry: object) -> UserRoleConfig:
    """Parse one [[user_roles]] entry."""
    if not isinstance(entry, dict):
        raise ConfigError("Each 'user_roles' entry must be a table")

    name = _expect_string(entry, "name") or ""
    roles = _expect_list_of_strings(entry, "roles")
    top_level_role = _expect_string(entry, "top_level_role", required=False)
    sub_roles = _expect_list_of_strings(entry, "sub_roles")
    output_filename = _expect_string(entry, "output_filename", required=False)

    if not roles and top_level_role is None:
        raise ConfigError(
            "Each 'user_roles' entry must define either 'roles' or 'top_level_role'"
        )

    return UserRoleConfig(
        name=name,
        roles=roles,
        top_level_role=top_level_role,
        sub_roles=sub_roles,
        output_filename=output_filename,
    )


def load_config(path: Path) -> RolyConfig:
    """Load and validate a Roly config file."""
    if not path.exists():
        raise ConfigError(f"Config not found: {path}")

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a TOML table")

    version = raw.get("version", 1)
    if not isinstance(version, int):
        raise ConfigError("'version' must be an integer")

    paths_cfg = PathsConfig(
        project_roles_dir=DEFAULT_PROJECT_ROLES_DIR,
        output_dir=DEFAULT_OUTPUT_DIR,
    )
    raw_paths = raw.get("paths", {})
    if raw_paths:
        if not isinstance(raw_paths, dict):
            raise ConfigError("'paths' must be a table")

        project_roles_dir = _expect_string(
            raw_paths, "project_roles_dir", required=False
        )
        output_dir = _expect_string(raw_paths, "output_dir", required=False)
        if project_roles_dir:
            paths_cfg.project_roles_dir = project_roles_dir
        if output_dir:
            paths_cfg.output_dir = output_dir

    user_roles_raw = raw.get("user_roles", [])
    if not isinstance(user_roles_raw, list):
        raise ConfigError("'user_roles' must be an array of tables")

    user_roles = [_parse_user_role(entry) for entry in user_roles_raw]
    setup_cfg = _parse_setup(raw.get("setup"))

    return RolyConfig(
        version=version,
        paths=paths_cfg,
        setup=setup_cfg,
        user_roles=user_roles,
    )


def write_config(path: Path, config: RolyConfig) -> None:
    """Write roly.config using deterministic key ordering."""
    lines: list[str] = [f"version = {config.version}", ""]
    lines.extend(
        [
            "[paths]",
            f"project_roles_dir = {_render_toml_string(config.paths.project_roles_dir)}",
            f"output_dir = {_render_toml_string(config.paths.output_dir)}",
            "",
            "[setup]",
            f"agent = {_render_toml_string(config.setup.agent)}",
        ]
    )
    if config.setup.skill_dir is not None:
        lines.append(f"skill_dir = {_render_toml_string(config.setup.skill_dir)}")
    if config.setup.codex_dir is not None:
        lines.append(f"codex_dir = {_render_toml_string(config.setup.codex_dir)}")
    if config.setup.roly_home is not None:
        lines.append(f"roly_home = {_render_toml_string(config.setup.roly_home)}")

    for role in config.user_roles:
        lines.extend(["", "[[user_roles]]", f"name = {_render_toml_string(role.name)}"])
        if role.roles:
            lines.append(f"roles = {_render_toml_string_list(role.roles)}")
        elif role.top_level_role:
            lines.append(f"top_level_role = {_render_toml_string(role.top_level_role)}")
            if role.sub_roles:
                lines.append(f"sub_roles = {_render_toml_string_list(role.sub_roles)}")
        if role.output_filename is not None:
            lines.append(
                f"output_filename = {_render_toml_string(role.output_filename)}"
            )

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
