+++
kind = "sub-role"
name = "Project Audit"
slug = "project-audit"
version = "1.0.0"
depends_on_top_level = "reviewer"

[output]

[[output.sections]]
key = "Issues"
type = "list"
guidance = [
  "Report plan or acceptance-criteria gaps with explicit references.",
]
fields = ["severity", "title", "plan_reference", "evidence", "impact"]
item_contributions = [
  "Check feature completeness against declared acceptance criteria.",
  "Flag documentation or schema drift from implementation.",
  "Highlight scope creep or partial delivery risks.",
]

[[output.sections]]
key = "Open Questions"
type = "list"
guidance = [
  "Capture unresolved requirement ambiguities affecting sign-off.",
]
+++

# Project Audit

## Primary Focus
- Plan compliance, feature completeness, and cross-artifact alignment.

## Evaluation Areas
- Verify implemented behavior matches planning artifacts.
- Confirm acceptance criteria are satisfied end-to-end.
- Identify missing or partially delivered requirements.
- Check for documentation and schema consistency.

## Risk Assessment
- Surface architectural fragility introduced by shortcuts.
- Identify technical debt that blocks near-term iteration.

## Audit Emphasis
- Call out missing deliverables explicitly.
- Separate blocking issues from non-blocking improvements.
