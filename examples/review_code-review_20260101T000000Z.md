# User Role: reviewer-default

## Composition
- Top-Level Role: `reviewer` (builtin)
- Sub-Roles:
  - `code-review` (builtin)
  - `project-audit` (builtin)

## Resolved Output Definition

### Summary (text)
- Guidance:
  - Provide a concise overall assessment of quality and readiness.

### Strengths (list)
- Guidance:
  - Capture concrete strengths backed by evidence.

### Issues (list)
- Guidance:
  - List findings by severity: Critical, Major, Minor.
  - Identify correctness defects, maintainability risks, and test gaps.
  - Report plan or acceptance-criteria gaps with explicit references.
- Fields:
  - severity
  - title
  - evidence
  - impact
  - recommendation
  - plan_reference
- Item Contributions:
  - Validate implementation correctness against intended behavior.
  - Flag insufficient tests and missing edge-case coverage.
  - Highlight hidden coupling and maintainability risks.
  - Check feature completeness against declared acceptance criteria.
  - Flag documentation or schema drift from implementation.
  - Highlight scope creep or partial delivery risks.

### Open Questions (list)
- Guidance:
  - Call out blockers, ambiguities, or missing context.
  - Ask for missing technical context that affects review confidence.
  - Capture unresolved requirement ambiguities affecting sign-off.

### Suggestions (list)
- Guidance:
  - Include only optional, non-blocking improvements.

## Instructions

### Top-Level Role: Reviewer
(omitted in sample)

### Sub-Role: Code Review
(omitted in sample)

### Sub-Role: Project Audit
(omitted in sample)
