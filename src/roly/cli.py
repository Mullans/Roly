"""Typer CLI for Roly."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from .assembler import (
    merge_output_definitions,
    render_assembled_role,
    resolve_output_filename,
    write_assembled_role,
)
from .config import load_config, write_config
from .context import AppContext, resolve_user_home
from .diffing import build_unified_diff
from .errors import ConfigError, ReviewApplyError, RolyError
from .models import RoleDocument, RoleKind, RolyConfig
from .paths import DEFAULT_OUTPUT_DIR, DEFAULT_PROJECT_ROLES_DIR, config_path
from .review import apply_change_with_result, load_review_changes, stub_review_changes
from .role_store import (
    infer_project_role_kind,
    infer_role_kind,
    local_project_role,
    local_user_role,
    local_user_role_path,
    resolve_role,
    role_from_path,
)
from .role_store import (
    list_roles as store_list_roles,
)
from .setup import (
    default_none_skill_path,
    install_codex_skill,
    install_none_prompt,
    merged_setup_config,
    resolve_codex_skills_dir,
)
from .ui import (
    print_change_preview,
    print_diff,
    print_roles_table,
    prompt_change_action,
)

app = typer.Typer(help="Roly CLI", no_args_is_help=True, add_completion=False)


class ScopeFilter(StrEnum):
    """Supported list command scope filters."""

    ALL = "all"
    BUILTIN = "builtin"
    USER = "user"
    PROJECT = "project"


class KindFilter(StrEnum):
    """Supported list command kind filters."""

    ALL = "all"
    TOP_LEVEL = "top-level"
    SUB_ROLE = "sub-role"


class SetupAgent(StrEnum):
    """Setup integration targets."""

    NONE = "none"
    CODEX = "codex"


@app.callback()
def cli_callback(
    ctx: typer.Context,
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help="Project root directory.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
    user_home: Annotated[
        Path | None,
        typer.Option(
            "--user-home",
            help="Roly user home (defaults to ROLY_HOME or ~/.roly).",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color", help="Disable ANSI styling for deterministic output."
        ),
    ] = False,
) -> None:
    """Initialize shared CLI context."""
    effective_project_root = project_root.expanduser().resolve()
    effective_user_home = resolve_user_home(user_home)
    console = Console(no_color=no_color)
    ctx.obj = AppContext(
        project_root=effective_project_root,
        user_home=effective_user_home,
        console=console,
        no_color=no_color,
    )


def _app_context(ctx: typer.Context) -> AppContext:
    """Return typed application context."""
    return cast(AppContext, ctx.obj)


def _optional_config(
    app_ctx: AppContext, explicit_config: Path | None = None
) -> RolyConfig | None:
    """Load config if path exists; otherwise return None."""
    if explicit_config is not None:
        if not explicit_config.exists():
            raise ConfigError(f"Config not found: {explicit_config}")
        candidate = explicit_config
    else:
        candidate = config_path(app_ctx.project_root)
        if not candidate.exists():
            return None

    return load_config(candidate)


def _config_or_default(app_ctx: AppContext) -> RolyConfig:
    """Return loaded config or defaults if absent."""
    cfg = _optional_config(app_ctx)
    if cfg is not None:
        return cfg
    return RolyConfig(version=1)


def _handle_error(app_ctx: AppContext, error: Exception) -> None:
    """Print user-facing error and exit."""
    app_ctx.console.print(f"Error: {error}")
    raise typer.Exit(code=1) from error


def _resolve_role_chain(
    *,
    app_ctx: AppContext,
    role_slugs: list[str],
    project_roles_dir: str,
) -> tuple[RoleDocument, list[RoleDocument]]:
    """Resolve ordered role chain and inject dependent top-level role as needed."""
    if not role_slugs:
        raise ConfigError("At least one role slug is required")

    top_role: RoleDocument | None = None
    selected_sub_roles: list[RoleDocument] = []
    seen_sub_roles: set[str] = set()

    for slug in role_slugs:
        kind = infer_role_kind(
            slug=slug,
            project_root=app_ctx.project_root,
            user_home=app_ctx.user_home,
            project_roles_dir=project_roles_dir,
        )
        role_doc = resolve_role(
            kind=kind,
            slug=slug,
            project_root=app_ctx.project_root,
            user_home=app_ctx.user_home,
            project_roles_dir=project_roles_dir,
        )

        if kind is RoleKind.TOP_LEVEL:
            if top_role is None:
                top_role = role_doc
            elif top_role.slug != role_doc.slug:
                raise ConfigError(
                    "Resolved roles include multiple top-level roles; choose one compatible set"
                )
            continue

        dependency_slug = role_doc.depends_on_top_level
        if dependency_slug is None:
            raise ConfigError(
                f"Sub-role '{role_doc.slug}' is missing dependency metadata"
            )
        dependency_doc = resolve_role(
            kind=RoleKind.TOP_LEVEL,
            slug=dependency_slug,
            project_root=app_ctx.project_root,
            user_home=app_ctx.user_home,
            project_roles_dir=project_roles_dir,
        )
        if top_role is None:
            top_role = dependency_doc
        elif top_role.slug != dependency_doc.slug:
            raise ConfigError(
                "Resolved roles require conflicting top-level dependencies; cannot assemble"
            )

        if role_doc.slug in seen_sub_roles:
            continue
        seen_sub_roles.add(role_doc.slug)
        selected_sub_roles.append(role_doc)

    if top_role is None:
        raise ConfigError("Could not resolve a top-level role from requested roles")
    return top_role, selected_sub_roles


def _resolve_role_target(
    *,
    app_ctx: AppContext,
    role: str | None,
    role_path: Path | None,
    project_roles_dir: str,
    for_promote: bool,
) -> tuple[RoleKind, str]:
    """Resolve target role kind and slug from slug or explicit role file path."""
    if role is None and role_path is None:
        raise ConfigError("Provide --role or --role-path")
    if role is not None and role_path is not None:
        raise ConfigError("Provide either --role or --role-path, not both")

    if role_path is not None:
        parsed = role_from_path(role_path, scope="project")
        return parsed.kind, parsed.slug

    if role is None:
        raise ConfigError("Provide --role when --role-path is not set")
    if for_promote:
        kind = infer_project_role_kind(
            slug=role,
            project_root=app_ctx.project_root,
            project_roles_dir=project_roles_dir,
        )
    else:
        kind = infer_role_kind(
            slug=role,
            project_root=app_ctx.project_root,
            user_home=app_ctx.user_home,
            project_roles_dir=project_roles_dir,
        )
    return kind, role


@app.command("list")
def list_command(
    ctx: typer.Context,
    scope: Annotated[
        ScopeFilter,
        typer.Option("--scope", help="Filter by role source scope."),
    ] = ScopeFilter.ALL,
    kind: Annotated[
        KindFilter,
        typer.Option("--kind", help="Filter by role kind."),
    ] = KindFilter.ALL,
) -> None:
    """List available roles across builtin/user/project scopes."""
    app_ctx = _app_context(ctx)
    try:
        cfg = _optional_config(app_ctx)
        project_roles_dir = (
            cfg.paths.project_roles_dir
            if cfg is not None
            else DEFAULT_PROJECT_ROLES_DIR
        )
        roles = store_list_roles(
            project_root=app_ctx.project_root,
            user_home=app_ctx.user_home,
            project_roles_dir=project_roles_dir,
            scope_filter=scope.value,
            kind_filter=kind.value,
        )
        print_roles_table(app_ctx.console, roles)
    except RolyError as error:
        _handle_error(app_ctx, error)


@app.command("setup")
def setup_command(
    ctx: typer.Context,
    agent: Annotated[
        SetupAgent | None, typer.Option("--agent", help="Setup target agent.")
    ] = None,
    skill_dir: Annotated[
        Path | None,
        typer.Option(
            "--skill-dir",
            help="Portable prompt output path for --agent none.",
            resolve_path=True,
        ),
    ] = None,
    codex_dir: Annotated[
        Path | None,
        typer.Option(
            "--codex-dir",
            help="Codex skills root directory (defaults to CODEX_HOME/skills or ~/.codex/skills).",
            resolve_path=True,
        ),
    ] = None,
    roly_home: Annotated[
        Path | None,
        typer.Option(
            "--roly-home",
            help="Persisted Roly home override for setup defaults.",
            resolve_path=True,
        ),
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", help="Overwrite existing install target.")
    ] = False,
    yes: Annotated[
        bool, typer.Option("--yes", help="Skip interactive confirmation prompts.")
    ] = False,
) -> None:
    """Install/update review skill and persist setup defaults."""
    app_ctx = _app_context(ctx)
    try:
        cfg = _config_or_default(app_ctx)
        interactive = (
            agent is None
            and skill_dir is None
            and codex_dir is None
            and roly_home is None
            and not force
            and not yes
        )

        chosen_agent = (
            agent.value
            if agent is not None
            else (cfg.setup.agent if not interactive else None)
        )
        chosen_skill_dir = skill_dir
        chosen_codex_dir = codex_dir
        chosen_roly_home = roly_home

        if interactive:
            chosen_agent = Prompt.ask(
                "Agent target",
                choices=["none", "codex"],
                default=cfg.setup.agent,
                console=app_ctx.console,
            )
            if chosen_agent == "none":
                default_path = cfg.setup.skill_dir or str(
                    default_none_skill_path(app_ctx.project_root)
                )
                chosen_skill_dir = Path(
                    Prompt.ask(
                        "Portable prompt path",
                        default=default_path,
                        console=app_ctx.console,
                    )
                )
            else:
                default_codex = cfg.setup.codex_dir or str(
                    resolve_codex_skills_dir(None)
                )
                chosen_codex_dir = Path(
                    Prompt.ask(
                        "Codex skills root",
                        default=default_codex,
                        console=app_ctx.console,
                    )
                )
            if cfg.setup.roly_home:
                chosen_roly_home = Path(
                    Prompt.ask(
                        "Roly home override",
                        default=cfg.setup.roly_home,
                        console=app_ctx.console,
                    )
                )
            should_apply = Confirm.ask(
                "Apply setup changes?", default=True, console=app_ctx.console
            )
            if not should_apply:
                app_ctx.console.print("Setup cancelled.")
                return

        if chosen_agent is None:
            chosen_agent = "none"

        if chosen_agent == "none":
            result = install_none_prompt(
                project_root=app_ctx.project_root,
                skill_dir=chosen_skill_dir,
                force=force,
            )
        else:
            result = install_codex_skill(codex_dir=chosen_codex_dir, force=force)

        persisted_setup = merged_setup_config(
            existing=cfg.setup,
            agent=chosen_agent,
            skill_dir=chosen_skill_dir,
            codex_dir=chosen_codex_dir,
            roly_home=chosen_roly_home,
        )
        cfg.setup = persisted_setup

        config_file = config_path(app_ctx.project_root)
        should_persist = yes or Confirm.ask(
            f"Persist setup defaults to {config_file}?",
            default=True,
            console=app_ctx.console,
        )
        if should_persist:
            write_config(config_file, cfg)

        app_ctx.console.print(
            Panel.fit(
                "\n".join(
                    [
                        f"agent: {chosen_agent}",
                        f"destination: {result.destination}",
                        f"status: {result.action}",
                    ]
                ),
                title="Setup Complete",
            )
        )
    except (RolyError, OSError) as error:
        _handle_error(app_ctx, error)


@app.command("assemble")
def assemble_command(
    ctx: typer.Context,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            help="Path to roly.config (defaults to <project-root>/roly.config).",
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    user_role: Annotated[
        str | None,
        typer.Option("--user-role", help="Named user role from config."),
    ] = None,
    role: Annotated[
        list[str] | None,
        typer.Option("--role", help="Role slug (repeat flag for ad-hoc mode)."),
    ] = None,
    name: Annotated[
        str | None,
        typer.Option("--name", help="Assembled role name (ad-hoc mode)."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Output file path override."),
    ] = None,
) -> None:
    """Assemble a deterministic user role artifact."""
    app_ctx = _app_context(ctx)

    try:
        cfg = _optional_config(app_ctx, config)
        project_roles_dir = (
            cfg.paths.project_roles_dir if cfg else DEFAULT_PROJECT_ROLES_DIR
        )
        output_dir_cfg = cfg.paths.output_dir if cfg else DEFAULT_OUTPUT_DIR

        config_output_filename: str | None = None
        user_role_name: str
        requested_roles: list[str]

        if role:
            requested_roles = list(role)
            user_role_name = name or f"{requested_roles[0]}-ad-hoc"
        else:
            if cfg is None:
                raise ConfigError("No config found and no --role values provided")
            if not cfg.user_roles:
                raise ConfigError("Config has no [[user_roles]] entries")
            if user_role is None:
                if len(cfg.user_roles) != 1:
                    raise ConfigError(
                        "Multiple user roles in config; choose one with --user-role"
                    )
                selected = cfg.user_roles[0]
            else:
                matches = [entry for entry in cfg.user_roles if entry.name == user_role]
                if not matches:
                    raise ConfigError(f"User role not found in config: {user_role}")
                selected = matches[0]

            requested_roles = selected.resolved_roles()
            if selected.roles == [] and selected.top_level_role is not None:
                app_ctx.console.print(
                    "[yellow]Config uses legacy top_level_role/sub_roles; migrate to 'roles' list.[/yellow]"
                )
            if not requested_roles:
                raise ConfigError("Selected user role has no roles configured")
            config_output_filename = selected.output_filename
            user_role_name = selected.name

        top_role_doc, sub_role_docs = _resolve_role_chain(
            app_ctx=app_ctx,
            role_slugs=requested_roles,
            project_roles_dir=project_roles_dir,
        )

        merged_output = merge_output_definitions(top_role_doc, sub_role_docs)
        content = render_assembled_role(
            user_role_name=user_role_name,
            top_role=top_role_doc,
            sub_roles=sub_role_docs,
            merged_output=merged_output,
        )

        if output is not None:
            destination = output
            if not destination.is_absolute():
                destination = app_ctx.project_root / destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
        else:
            filename = resolve_output_filename(
                output_override=None,
                config_output_filename=config_output_filename,
                merged_output=merged_output,
                top_role=top_role_doc,
                sub_roles=sub_role_docs,
            )
            destination = write_assembled_role(
                content=content,
                output_dir=app_ctx.project_root / output_dir_cfg,
                filename=filename,
            )

        app_ctx.console.print(
            Panel.fit(
                "\n".join(
                    [
                        f"output: {destination}",
                        f"top-level: {top_role_doc.slug}",
                        (
                            f"sub-roles: {', '.join(role.slug for role in sub_role_docs)}"
                            if sub_role_docs
                            else "sub-roles: (none)"
                        ),
                    ]
                ),
                title="Assemble Complete",
            )
        )
    except (RolyError, OSError) as error:
        _handle_error(app_ctx, error)


@app.command("diff")
def diff_command(
    ctx: typer.Context,
    role: Annotated[
        str | None,
        typer.Option("--role", help="Role slug (kind inferred when possible)."),
    ] = None,
    role_path: Annotated[
        Path | None,
        typer.Option(
            "--role-path", help="Explicit role file path used to infer kind and slug."
        ),
    ] = None,
) -> None:
    """Show diff between project-local and user-level role versions."""
    app_ctx = _app_context(ctx)

    try:
        cfg = _optional_config(app_ctx)
        project_roles_dir = (
            cfg.paths.project_roles_dir if cfg else DEFAULT_PROJECT_ROLES_DIR
        )
        role_kind, role_slug = _resolve_role_target(
            app_ctx=app_ctx,
            role=role,
            role_path=role_path,
            project_roles_dir=project_roles_dir,
            for_promote=False,
        )

        project_role = local_project_role(
            kind=role_kind,
            slug=role_slug,
            project_root=app_ctx.project_root,
            project_roles_dir=project_roles_dir,
        )
        user_role = local_user_role(
            kind=role_kind, slug=role_slug, user_home=app_ctx.user_home
        )

        diff_lines = build_unified_diff(
            before=user_role.source_path.read_text(encoding="utf-8"),
            after=project_role.source_path.read_text(encoding="utf-8"),
            from_label=str(user_role.source_path),
            to_label=str(project_role.source_path),
        )
        print_diff(app_ctx.console, diff_lines)
    except (RolyError, OSError) as error:
        _handle_error(app_ctx, error)


@app.command("promote")
def promote_command(
    ctx: typer.Context,
    role: Annotated[
        str | None,
        typer.Option("--role", help="Project-local role slug (kind inferred)."),
    ] = None,
    role_path: Annotated[
        Path | None,
        typer.Option(
            "--role-path", help="Explicit role file path used to infer kind and slug."
        ),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Promote a project-local role to user-level by overwrite."""
    app_ctx = _app_context(ctx)

    try:
        cfg = _optional_config(app_ctx)
        project_roles_dir = (
            cfg.paths.project_roles_dir if cfg else DEFAULT_PROJECT_ROLES_DIR
        )
        role_kind, role_slug = _resolve_role_target(
            app_ctx=app_ctx,
            role=role,
            role_path=role_path,
            project_roles_dir=project_roles_dir,
            for_promote=True,
        )

        project_role = local_project_role(
            kind=role_kind,
            slug=role_slug,
            project_root=app_ctx.project_root,
            project_roles_dir=project_roles_dir,
        )
        destination = local_user_role_path(
            kind=role_kind,
            slug=role_slug,
            user_home=app_ctx.user_home,
        )

        should_write = yes or Confirm.ask(
            f"Overwrite user-level role at {destination}?",
            console=app_ctx.console,
            default=False,
        )
        if not should_write:
            app_ctx.console.print("Promotion cancelled.")
            return

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            project_role.source_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        app_ctx.console.print(
            f"Promoted {role_kind.value}:{role_slug} -> {destination}"
        )
    except (RolyError, OSError) as error:
        _handle_error(app_ctx, error)


@app.command("review")
def review_command(
    ctx: typer.Context,
    target_sub_role: Annotated[
        list[str] | None,
        typer.Option(
            "--target-sub-role",
            help="Target sub-role slug for updates (repeat for multiple).",
        ),
    ] = None,
    changes_file: Annotated[
        Path | None,
        typer.Option("--changes-file", help="TOML file with proposed changes."),
    ] = None,
    transcript: Annotated[
        Path | None,
        typer.Option("--transcript", help="Conversation transcript input (reserved)."),
    ] = None,
    active_user_role: Annotated[
        Path | None,
        typer.Option(
            "--active-user-role",
            help="Assembled user role input for review context (reserved).",
        ),
    ] = None,
    use_stub: Annotated[
        bool,
        typer.Option(
            "--use-stub",
            help="Use deterministic stub changes when --changes-file is not provided.",
        ),
    ] = False,
) -> None:
    """Run interactive review update approval flow for sub-role files."""
    app_ctx = _app_context(ctx)
    _ = transcript
    _ = active_user_role

    if not target_sub_role:
        _handle_error(app_ctx, ConfigError("Provide at least one --target-sub-role"))

    try:
        cfg = _optional_config(app_ctx)
        project_roles_dir = (
            cfg.paths.project_roles_dir if cfg else DEFAULT_PROJECT_ROLES_DIR
        )

        targets = target_sub_role or []
        if changes_file is None and not use_stub:
            raise ConfigError("Provide --changes-file or pass --use-stub")
        if changes_file is None:
            changes = stub_review_changes(targets)
        else:
            changes = load_review_changes(changes_file)

        role_text_by_slug: dict[str, str] = {}
        role_path_by_slug: dict[str, Path] = {}
        for slug in targets:
            role_doc = local_project_role(
                kind=RoleKind.SUB_ROLE,
                slug=slug,
                project_root=app_ctx.project_root,
                project_roles_dir=project_roles_dir,
            )
            role_text_by_slug[slug] = role_doc.source_path.read_text(encoding="utf-8")
            role_path_by_slug[slug] = role_doc.source_path

        accepted_applied = 0
        accepted_noop = 0
        rejected = 0
        skipped = 0
        written_files: set[str] = set()
        accept_all = False

        for index, change in enumerate(changes):
            if change.target_kind is not RoleKind.SUB_ROLE:
                raise ReviewApplyError(
                    "Review workflow cannot auto-modify top-level roles"
                )
            if change.target_slug not in role_text_by_slug:
                raise ReviewApplyError(
                    f"Review change target '{change.target_slug}' is not in --target-sub-role"
                )

            print_change_preview(app_ctx.console, change)
            action = "y" if accept_all else prompt_change_action(app_ctx.console)
            if action == "q":
                skipped += len(changes) - index
                break
            if action == "n":
                rejected += 1
                continue
            if action == "a":
                accept_all = True
                action = "y"

            result = apply_change_with_result(
                role_text_by_slug[change.target_slug], change
            )
            if result.applied:
                role_text_by_slug[change.target_slug] = result.content
                written_files.add(change.target_slug)
                accepted_applied += 1
            else:
                accepted_noop += 1
                if result.message:
                    app_ctx.console.print(
                        f"[yellow]{result.message}[/yellow] for {change.target_slug}"
                    )

        for slug in sorted(written_files):
            role_path_by_slug[slug].write_text(
                role_text_by_slug[slug], encoding="utf-8"
            )

        app_ctx.console.print(
            Panel.fit(
                "\n".join(
                    [
                        f"accepted_applied: {accepted_applied}",
                        f"accepted_noop: {accepted_noop}",
                        f"rejected: {rejected}",
                        f"skipped: {skipped}",
                        f"files written: {len(written_files)}",
                    ]
                ),
                title="Review Update Summary",
            )
        )
    except (RolyError, OSError) as error:
        _handle_error(app_ctx, error)
