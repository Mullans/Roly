"""Setup workflow for installing review skills."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .models import SetupConfig

TEMPLATE_VERSION = "1"
TEMPLATE_TIMESTAMP = "2026-02-12T00:00:00Z"
SKILL_ID = "roly-review-skill"
CODEX_SKILL_NAME = "roly-review"


@dataclass(slots=True)
class SetupResult:
    """Result of one setup write operation."""

    destination: Path
    action: str


def resolve_codex_skills_dir(codex_dir: Path | None) -> Path:
    """Resolve Codex skills root directory."""
    if codex_dir is not None:
        return codex_dir.expanduser().resolve()
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return (Path(env_home).expanduser().resolve()) / "skills"
    return Path("~/.codex/skills").expanduser().resolve()


def default_none_skill_path(project_root: Path) -> Path:
    """Return default portable skill output path."""
    return project_root / "roly_review_skill.md"


def render_none_prompt() -> str:
    """Render portable review skill prompt."""
    return "\n".join(
        [
            f"roly_skill_id: {SKILL_ID}",
            f"roly_template_version: {TEMPLATE_VERSION}",
            f"roly_template_timestamp: {TEMPLATE_TIMESTAMP}",
            "",
            "# Roly Review Skill",
            "",
            "Use this workflow to generate review changes for Roly.",
            "",
            "## Inputs",
            "- Active assembled user role",
            "- Conversation context and user feedback",
            "- Target sub-role slugs",
            "",
            "## Output format",
            "Produce TOML with `[[changes]]` entries:",
            '- `target_kind = "sub-role"`',
            '- `target_slug = "..."`',
            '- `op = "add"|"remove"|"modify"`',
            "- `anchor`, `text`, `old_text`, `new_text` as required by op",
            "",
            "## Constraints",
            "- Never target top-level roles.",
            "- Prefer minimal, deterministic text edits.",
            "- Keep suggestions concrete and verifiable.",
            "",
        ]
    )


def render_codex_skill_md() -> str:
    """Render Codex SKILL.md for review workflow."""
    return "\n".join(
        [
            "---",
            "name: roly-review",
            "description: Generate deterministic Roly review changes in TOML for roly review --changes-file.",
            "---",
            "",
            f"roly_skill_id: {SKILL_ID}",
            f"roly_template_version: {TEMPLATE_VERSION}",
            f"roly_template_timestamp: {TEMPLATE_TIMESTAMP}",
            "",
            "# Roly Review",
            "",
            "Generate `[[changes]]` TOML entries for Roly sub-role updates.",
            "",
            "Required behavior:",
            '- Only emit `target_kind = "sub-role"`.',
            "- Keep changes minimal and deterministic.",
            "- Prefer `modify` over broad `remove`+`add` when possible.",
            "- Include exact anchor/text values that can be applied safely.",
            "",
        ]
    )


def _extract_metadata(content: str) -> tuple[str | None, str | None, str | None]:
    """Extract roly metadata triple from file contents."""
    skill_id: str | None = None
    version: str | None = None
    timestamp: str | None = None
    for line in content.splitlines():
        if line.startswith("roly_skill_id:"):
            skill_id = line.split(":", 1)[1].strip()
        elif line.startswith("roly_template_version:"):
            version = line.split(":", 1)[1].strip()
        elif line.startswith("roly_template_timestamp:"):
            timestamp = line.split(":", 1)[1].strip()
    return skill_id, version, timestamp


def needs_update(destination: Path, content: str, *, force: bool) -> bool:
    """Return whether destination should be overwritten."""
    if force or not destination.exists():
        return True
    existing = destination.read_text(encoding="utf-8")
    existing_id, existing_version, existing_timestamp = _extract_metadata(existing)
    new_id, new_version, new_timestamp = _extract_metadata(content)
    if existing_id != new_id:
        return True
    if existing_version != new_version:
        return True
    return existing_timestamp != new_timestamp


def write_if_needed(destination: Path, content: str, *, force: bool) -> SetupResult:
    """Write file if missing or outdated."""
    existed = destination.exists()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if needs_update(destination, content, force=force):
        destination.write_text(content, encoding="utf-8")
        action = "updated" if existed else "installed"
        return SetupResult(destination=destination, action=action)
    return SetupResult(destination=destination, action="up-to-date")


def install_none_prompt(
    *, project_root: Path, skill_dir: Path | None, force: bool
) -> SetupResult:
    """Install portable prompt file."""
    if skill_dir is None:
        destination = default_none_skill_path(project_root)
    else:
        destination = skill_dir
        if not destination.is_absolute():
            destination = project_root / destination
        destination = destination.expanduser().resolve()
    return write_if_needed(destination, render_none_prompt(), force=force)


def install_codex_skill(*, codex_dir: Path | None, force: bool) -> SetupResult:
    """Install/update Codex skill folder content."""
    root = resolve_codex_skills_dir(codex_dir)
    destination = root / CODEX_SKILL_NAME / "SKILL.md"
    return write_if_needed(destination, render_codex_skill_md(), force=force)


def merged_setup_config(
    *,
    existing: SetupConfig,
    agent: str,
    skill_dir: Path | None,
    codex_dir: Path | None,
    roly_home: Path | None,
) -> SetupConfig:
    """Build persisted setup defaults by merging explicit overrides."""
    return SetupConfig(
        agent=agent,
        skill_dir=(
            str(skill_dir.expanduser().resolve())
            if skill_dir is not None
            else existing.skill_dir
        ),
        codex_dir=(
            str(codex_dir.expanduser().resolve())
            if codex_dir is not None
            else existing.codex_dir
        ),
        roly_home=(
            str(roly_home.expanduser().resolve())
            if roly_home is not None
            else existing.roly_home
        ),
    )
