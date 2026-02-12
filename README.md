<img src="assets/logo_wordmark.svg" alt="Roly logo" width="320">

# Roly

[![PyPI - Version](https://img.shields.io/pypi/v/roly.svg)](https://pypi.org/project/roly)

Deterministic role assembly for coding-agent workflows.

Roly helps build reusable role instructions that are composable, reviewable, and predictable.
No hidden merges. No implicit magic. Just a clean CLI flow from role definition to generated output.

## Quick Start

Try Roly from PyPI (no install):

```bash
uvx roly list --no-color
```

Run from source:

```bash
uv sync
uv run roly list --no-color
```

Assemble your first role output:

```bash
uv run roly assemble \
  --role code-review \
  --role project-audit \
  --name reviewer-ad-hoc \
  --no-color
```

Prefer config-based assembly:

```bash
uv run roly assemble --config examples/roly.config --user-role reviewer-default --no-color
```


## Why Roly

- Deterministic every time: one top-level role plus ordered sub-roles, assembled in a fixed order.
- Scope-aware by default: project, user, and built-in roles with explicit precedence.
- Safe review workflow: proposed sub-role edits go through interactive accept/reject approval.
- Explicit promotion model: project-local edits only become user-level when you promote them.

## What You Can Do

List available roles:

```bash
uv run roly list --no-color
```

Compare project-local vs user-level role definitions:

```bash
uv run roly diff --role code-review --no-color
```

Promote a project-local role to user-level:

```bash
uv run roly promote --role code-review --yes --no-color
```

Run interactive review + apply flow:

```bash
uv run roly review --target-sub-role code-review --target-sub-role project-audit --changes-file changes.toml --no-color
```

Create/setup review skill assets:

```bash
uv run roly setup --agent none --yes --no-color
```

## How It Works

1. Define roles as markdown files with TOML front matter.
2. Select ordered role slugs; dependency top-level role is auto-inserted for each sub-role.
3. Assemble deterministic output artifacts from role content + output definitions.
4. Keep experimental edits project-local, then promote only when ready.

## Example Use Cases

- Standardize engineering review prompts across repositories.
- Layer domain overlays (security, compliance, architecture) without copy-paste.
- Run repeatable role updates with human approval in the loop.
- Keep team prompts versioned, diffable, and shareable.

## Docs For Contributors

Development setup, lint/test commands, and contributor workflows are in `README_DEV.md`.
