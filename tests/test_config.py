from pathlib import Path

import pytest

from roly.config import load_config, write_config
from roly.errors import ConfigError
from roly.models import RolyConfig


def test_load_config_supports_new_roles_list_and_setup(tmp_path: Path):
    config_file = tmp_path / "roly.config"
    config_file.write_text(
        """version = 1

[setup]
agent = "none"
skill_dir = "roly_review_skill.md"

[[user_roles]]
name = "reviewer-default"
roles = ["code-review", "project-audit"]
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.setup.agent == "none"
    assert config.setup.skill_dir == "roly_review_skill.md"
    assert config.user_roles[0].resolved_roles() == ["code-review", "project-audit"]


def test_load_config_legacy_top_level_and_sub_roles_still_work(tmp_path: Path):
    config_file = tmp_path / "roly.config"
    config_file.write_text(
        """version = 1

[[user_roles]]
name = "legacy"
top_level_role = "reviewer"
sub_roles = ["code-review"]
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.user_roles[0].resolved_roles() == ["reviewer", "code-review"]


def test_load_config_rejects_invalid_setup_agent(tmp_path: Path):
    config_file = tmp_path / "roly.config"
    config_file.write_text(
        """version = 1

[setup]
agent = "unknown"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(config_file)


def test_load_config_requires_roles_or_legacy_top_level(tmp_path: Path):
    config_file = tmp_path / "roly.config"
    config_file.write_text(
        """version = 1

[[user_roles]]
name = "invalid"
sub_roles = ["code-review"]
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(config_file)


def test_write_config_persists_setup_defaults(tmp_path: Path):
    config = RolyConfig(version=1)
    config.setup.agent = "codex"
    config.setup.codex_dir = str(tmp_path / "codex")
    config.user_roles = []
    config_file = tmp_path / "roly.config"

    write_config(config_file, config)
    loaded = load_config(config_file)

    assert loaded.setup.agent == "codex"
    assert loaded.setup.codex_dir == str(tmp_path / "codex")
