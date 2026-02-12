"""CLI context helpers for Roly."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console


@dataclass(slots=True)
class AppContext:
    """Shared CLI context."""

    project_root: Path
    user_home: Path
    console: Console
    no_color: bool


def resolve_user_home(user_home: Path | None) -> Path:
    """Resolve the effective user home directory for Roly data."""
    if user_home is not None:
        return user_home.expanduser().resolve()

    env_value = Path("~/.roly")
    from_env = os.environ.get("ROLY_HOME")
    if from_env:
        env_value = Path(from_env)

    return env_value.expanduser().resolve()
