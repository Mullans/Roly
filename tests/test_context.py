from pathlib import Path

from roly.context import resolve_user_home


def test_resolve_user_home_prefers_explicit_path(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ROLY_HOME", str(tmp_path / "env-home"))
    explicit = tmp_path / "explicit-home"

    assert resolve_user_home(explicit) == explicit.resolve()


def test_resolve_user_home_uses_roly_home_env(monkeypatch, tmp_path: Path):
    env_home = tmp_path / "env-home"
    monkeypatch.setenv("ROLY_HOME", str(env_home))

    assert resolve_user_home(None) == env_home.resolve()


def test_resolve_user_home_defaults_to_dot_roly(monkeypatch):
    monkeypatch.delenv("ROLY_HOME", raising=False)

    assert resolve_user_home(None) == Path("~/.roly").expanduser().resolve()
