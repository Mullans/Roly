"""Roly package entrypoints."""

from .cli import app


def main() -> None:
    """Run the Roly command-line interface."""
    app()


__all__ = ["app", "main"]
