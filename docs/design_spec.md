# Roly Design Spec

## Document Status

- Status: Active (living specification)
- Scope: Entire Roly project
- Source of truth: This document is the authoritative design reference for behavior, architecture, and workflows.

## Source-of-Truth Process (Mandatory)

1. Any request that changes behavior, architecture, file formats, workflows, or interfaces must update this document first.
2. The design update must be committed in the same change set as implementation.
3. If a requested change is ambiguous, clarify and update this document before code changes.
4. If code and this document conflict, treat this document as the target behavior and reconcile code accordingly.

## Product Definition

Roly is a deterministic, CLI-first role system for coding-agent workflows.

Core entities:

- Top-Level Role: phase-oriented operating mode (e.g., Reviewer).
- Sub-Role: domain or constraint overlay (e.g., Code Review, Project Audit).
- User Role: resolved execution artifact assembled from one top-level role plus zero or more ordered sub-roles.

Design priorities:

- Predictability over automation.
- Deterministic assembly and file generation.
- Explicit user control over updates and promotion.
- Lean operational model (no branching graphs, no hidden merges).

## Technical Baseline

- Python: `>=3.12`
- Package manager and execution: `uv`
- CLI framework: `Typer`
- Terminal UX: `Rich`
- Lint/format: `ruff`
- Tests: `pytest`

## Architecture Overview

Code is implemented in `src/roly/`.

Primary modules:

- `src/roly/cli.py`: Typer app and command routing.
- `src/roly/context.py`: app context and `ROLY_HOME` resolution.
- `src/roly/models.py`: core dataclasses and enums.
- `src/roly/config.py`: `roly.config` parsing/validation.
- `src/roly/role_parser.py`: role front-matter parsing.
- `src/roly/role_store.py`: role listing and precedence resolution.
- `src/roly/assembler.py`: output definition merge and artifact rendering.
- `src/roly/diffing.py`: unified diff generation.
- `src/roly/review.py`: review-change parsing and apply mechanics.
- `src/roly/ui.py`: Rich rendering helpers.

Built-in role library:

- `src/roly/builtin/top_level/reviewer.md`
- `src/roly/builtin/sub_roles/code-review.md`
- `src/roly/builtin/sub_roles/project-audit.md`

## Storage Model

User-level scope:

- Root: `${ROLY_HOME}` if set, else `~/.roly`
- Roles: `${user_home}/roles/top_level/*.md` and `${user_home}/roles/sub_roles/*.md`

Project-level scope:

- Config: `<project_root>/roly.config`
- Default roles path: `<project_root>/.roly/roles`
- Default assembled output path: `<project_root>/.roly/generated`

Scope precedence for role resolution:

1. project
2. user
3. built-in

## File Formats

### 1) Role files (Markdown + TOML front matter)

Delimiter:

- Opening: `+++`
- Closing: `+++`

Required front-matter fields:

- `kind`: `top-level` | `sub-role`
- `name`: string
- `slug`: string
- `version`: string
- `depends_on_top_level`: string (required when `kind = "sub-role"`)

Optional output definition:

- `[output]`
- `filename_template`: string
- `[[output.sections]]` entries with:
  - `key`: string
  - `type`: `text` | `list`
  - `guidance`: `list[str]` (optional)
  - `fields`: `list[str]` (optional)
  - `item_contributions`: `list[str]` (optional)

### 2) Project config (`roly.config`, TOML)

Top-level keys:

- `version` (int, default `1`)
- `[paths]` with:
  - `project_roles_dir` (default `.roly/roles`)
  - `output_dir` (default `.roly/generated`)
- `[[user_roles]]` entries with:
  - `name` (required)
  - `roles` (`list[str]`, preferred)
  - `top_level_role` (legacy, transition compatibility)
  - `sub_roles` (`list[str]`, legacy, transition compatibility)
  - `output_filename` (optional)
- `[setup]` with:
  - `agent` (`none` | `codex`, default `none`)
  - `skill_dir` (optional)
  - `codex_dir` (optional)
  - `roly_home` (optional)

### 3) Review change input (`--changes-file`, TOML)

Schema:

- `[[changes]]` entries containing:
  - `target_kind`: must be `sub-role` for apply flow
  - `target_slug`: sub-role slug
  - `op`: `add` | `remove` | `modify`
  - `anchor` (optional, for add)
  - `text` (required for add/remove)
  - `old_text` and `new_text` (required for modify)

## CLI Contract

Global options (root callback):

- `--project-root PATH`
- `--user-home PATH`
- `--no-color`

Commands:

1. `roly list`

- Options: `--scope all|builtin|user|project`, `--kind all|top-level|sub-role`
- Output: role table (scope, kind, slug, name, path)

1. `roly assemble`

- Modes:
  - Config mode via `roly.config` (optionally `--user-role`)
  - Ad-hoc mode via repeated `--role` slug values with kind inference
- Optional `--config PATH` override for config mode. If provided explicitly and the path does not exist, command fails with a config-not-found error.
- Optional `--name` for explicit assembled role name in ad-hoc mode
- Optional `--output` for explicit file path
- Behavior: deterministic assembly and file write; sub-role dependencies auto-insert required top-level role if missing

1. `roly setup`

- Purpose: configure review skill integration and setup defaults
- Options:
  - `--agent none|codex` (default `none`)
  - `--skill-dir PATH` (used for `agent=none`, default `roly_review_skill.md` in project root)
  - `--codex-dir PATH` (optional override for codex install root)
  - `--roly-home PATH` (optional setup default persisted into config)
  - `--force` (overwrite/reinstall even if up to date)
  - `--yes` (non-interactive confirmation mode)
- Behavior:
  - No-arg invocation runs interactive setup wizard
  - `agent=codex` installs/updates skill bundle under codex skills root
  - `agent=none` writes portable review-skill prompt file
  - Install artifacts include template metadata timestamp/version and update checks
  - Persists selected defaults into `[setup]` in `roly.config`

1. `roly diff`

- Required: `--role`
- Optional: `--role-path` as explicit disambiguation/escape hatch
- Role kind is inferred when possible (and can be parsed from explicit role path).
- Compares user-level file vs project-local file and prints unified diff

1. `roly promote`

- Required: `--role`
- Optional: `--role-path` as explicit disambiguation/escape hatch
- Role kind is inferred when possible (and can be parsed from explicit role path).
- Optional: `--yes` to skip confirmation
- Behavior: explicit overwrite from project-local file to user-level file

1. `roly review`

- Required: one or more `--target-sub-role`
- Optional: `--changes-file`, `--transcript`, `--active-user-role`
- Behavior: interactive approval loop (`y/n/a/q`) and apply accepted changes to project sub-role files only

## Deterministic Assembly Rules

1. Exactly one top-level role.
2. Zero or more ordered sub-roles.
3. Instruction concatenation order:

- top-level body
- each sub-role body in provided order

4. Output-section merge key: case-normalized section key (`strip + casefold`).
5. Sub-role dependency insertion: if a sub-role declares `depends_on_top_level`, assembly inserts that top-level role immediately before the first such sub-role unless already included.

Merge behavior:

- `text` sections: union guidance in insertion order.
- `list` sections: union guidance, fields, and item contributions in insertion order.
- Type conflicts: keep first type encountered and append conflict guidance note.

Filename resolution order:

1. explicit `--output`
2. config `output_filename`
3. resolved role template (`filename_template`)
4. default `review_{subrole-or-role}_{timestamp}.md`

Default token resolution:

- `{subrole-or-role}`: first active sub-role slug if any, else top-level slug
- `{timestamp}`: UTC format `%Y%m%dT%H%M%SZ`

## Review and Update Workflow

1. Load target project sub-role files.
2. Load proposed changes from `--changes-file` (typically produced by configured agent skill), or generate deterministic stub changes when explicitly requested.
3. Render each proposal with color coding:

- add: green
- remove: red
- modify/meta: yellow

4. Prompt user per change:

- `y` accept
- `n` reject
- `a` accept all remaining
- `q` quit

5. Apply accepted operations in-memory:

- add: after first anchor match (idempotent at the anchor location), else append
- remove: first exact text match; no-op if not found
- modify: first exact old-text match; no-op if not found
- Accepted no-op operations are surfaced to the user during review.

6. Persist modified target files and print summary (`accepted_applied`, `accepted_noop`, `rejected`, `skipped`, `files written`).

Safety rule:

- Top-level roles cannot be auto-modified by review apply flow.

Setup-to-review integration:

- `roly setup` installs or writes review skill prompts that can produce structured changes for `roly review --changes-file`.

## Promotion Model

- Default edits are project-local.
- Promotion is explicit user action and full overwrite to user-level.
- No partial merges, branch graphs, or dependency tracking.

## Built-in Roles (Current)

- Top-level: `reviewer`
- Sub-roles: `code-review`, `project-audit`

Shared-issues behavior:

- Both sub-roles contribute to one merged `Issues` list section during assembly.

## Non-Goals (Current)

- No cloud services.
- No automatic upstream merges.
- No semantic conflict reconciliation beyond deterministic merge rules.
- No heavy UI beyond terminal interactions.

## Validation and Quality Gates

Standard local validation before completion:

1. `uv sync`
2. `uv run ruff check .`
3. `uv run ruff format . --check`
4. `uv run pytest`

## Change Log

- Added initial living design spec and established mandatory pre-change spec update process.
