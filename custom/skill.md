roly_skill_id: roly-review-skill
roly_template_version: 1
roly_template_timestamp: 2026-02-12T00:00:00Z

# Roly Review Skill

Use this workflow to generate review changes for Roly.

## Inputs
- Active assembled user role
- Conversation context and user feedback
- Target sub-role slugs

## Output format
Produce TOML with `[[changes]]` entries:
- `target_kind = "sub-role"`
- `target_slug = "..."`
- `op = "add"|"remove"|"modify"`
- `anchor`, `text`, `old_text`, `new_text` as required by op

## Constraints
- Never target top-level roles.
- Prefer minimal, deterministic text edits.
- Keep suggestions concrete and verifiable.
