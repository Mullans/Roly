# Roly Development Guide

This document contains development-only workflows for contributors.

## Environment Setup

Sync dependencies from `uv.lock`:

```bash
uv sync
```

## Local CLI Commands

List available roles:

```bash
uv run roly list --no-color
```

Assemble from config:

```bash
uv run roly assemble --config examples/roly.config --user-role reviewer-default --no-color
```

Assemble ad-hoc:

```bash
uv run roly assemble --role code-review --role project-audit --name reviewer-ad-hoc --no-color
```

Show diff between project-local and user-level role:

```bash
uv run roly diff --role code-review --no-color
```

Promote a project-local role to user-level:

```bash
uv run roly promote --role code-review --yes --no-color
```

Run review workflow with interactive approvals:

```bash
uv run roly review --target-sub-role code-review --target-sub-role project-audit --changes-file changes.toml --no-color
```

Setup review skill output (portable markdown prompt):

```bash
uv run roly setup --agent none --yes --no-color
```

Setup Codex skill install:

```bash
uv run roly setup --agent codex --yes --no-color
```

## Quality Checks

Lint:

```bash
uv run ruff check .
```

Format check:

```bash
uv run ruff format . --check
```

Tests:

```bash
uv run pytest
```

## Standard Validation Sequence

1. `uv sync`
2. `uv run ruff check .`
3. `uv run ruff format . --check`
4. `uv run pytest`
