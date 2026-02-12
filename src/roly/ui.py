"""Rich UI helpers for Roly CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from .diffing import classify_diff_line
from .models import ReviewChange, RoleDocument


def print_roles_table(console: Console, roles: list[RoleDocument]) -> None:
    """Render a role listing table."""
    table = Table(title="Available Roles")
    table.add_column("Scope")
    table.add_column("Kind")
    table.add_column("Slug")
    table.add_column("Name")
    table.add_column("Path")

    for role in roles:
        table.add_row(
            role.source_scope,
            role.kind.value,
            role.slug,
            role.name,
            str(role.source_path),
        )

    console.print(table)


def print_diff(console: Console, diff_lines: list[str]) -> None:
    """Render a unified diff with semantic coloring."""
    if not diff_lines:
        console.print("No differences found.")
        return

    for line in diff_lines:
        cls = classify_diff_line(line)
        if cls == "add":
            console.print(Text(line, style="green"))
        elif cls == "remove":
            console.print(Text(line, style="red"))
        elif cls == "meta":
            console.print(Text(line, style="yellow"))
        else:
            console.print(line)


def print_change_preview(console: Console, change: ReviewChange) -> None:
    """Render a single review change preview panel."""
    lines = [
        f"target: {change.target_kind.value}:{change.target_slug}",
        f"operation: {change.op.value}",
    ]

    if change.anchor:
        lines.append(f"anchor: {change.anchor}")
    if change.text:
        lines.append("text:")
        lines.append(change.text)
    if change.old_text:
        lines.append("old_text:")
        lines.append(change.old_text)
    if change.new_text:
        lines.append("new_text:")
        lines.append(change.new_text)

    style = {
        "add": "green",
        "remove": "red",
        "modify": "yellow",
    }[change.op.value]

    console.print(Panel("\n".join(lines), title="Proposed Change", border_style=style))


def prompt_change_action(console: Console) -> str:
    """Prompt for review approval action."""
    return Prompt.ask(
        "Action [y=accept, n=reject, a=accept all remaining, q=quit]",
        choices=["y", "n", "a", "q"],
        default="y",
        console=console,
    )
