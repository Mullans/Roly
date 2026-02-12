+++
kind = "sub-role"
name = "Code Review"
slug = "code-review"
version = "1.0.0"
depends_on_top_level = "reviewer"

[output]

[[output.sections]]
key = "Issues"
type = "list"
guidance = [
  "Identify correctness defects, maintainability risks, and test gaps.",
]
fields = ["severity", "title", "evidence", "impact", "recommendation"]
item_contributions = [
  "Validate implementation correctness against intended behavior.",
  "Flag insufficient tests and missing edge-case coverage.",
  "Highlight hidden coupling and maintainability risks.",
]

[[output.sections]]
key = "Open Questions"
type = "list"
guidance = [
  "Ask for missing technical context that affects review confidence.",
]
+++

# Code Review

## Primary Focus
- Correctness, readability, maintainability, and test quality.

## Evaluation Areas
- Compare implementation behavior to expected behavior.
- Check error handling, data validation, and failure paths.
- Evaluate abstractions for unnecessary complexity.
- Identify performance pitfalls that are likely to matter.

## Diff-Specific Checks
- Detect unrelated changes in the diff.
- Confirm refactors are justified by the change objective.
- Ensure diff size matches the requested scope.

## Testing Checks
- Confirm coverage for new or changed behavior.
- Flag superficial tests that do not validate outcomes.
