# rollie

## Development

Run lint checks:

```bash
uv run ruff check .
```

Apply safe lint fixes:

```bash
uv run ruff check --fix .
```

Format code:

```bash
uv run ruff format .
```

Check formatting in CI/local verification:

```bash
uv run ruff format --check .
```

## Testing

Run tests with coverage and HTML reports:

```bash
uv run pytest
```

Artifacts:

- Coverage HTML: `tests_output/htmlcov/index.html`
- Pytest HTML report: `tests_output/pytest-report.html`
