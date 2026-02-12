You are an expert Python engineer (assume **Python 3.12**) implementing a tool called **Roly**.

Your job: implement the *design exactly* as specified below. Prioritize correctness, predictability, and a clean UX over cleverness or premature complexity. This is a CLI-first product that can optionally integrate with “agent skills” workflows, but it must stand on its own as a Python package.

## Product Summary (What Roly Is)

Roly is a modular “role system” for coding agents, where:

* A **Top-Level Role** (e.g., Planner / Programmer / Reviewer) defines the phase mindset and default output skeleton.
* One or more **Sub-Roles** overlay domain specifics (e.g., Code Review / Project Audit / Python specialization).
* A **User Role** is a deterministic assembled artifact (single file) used for a session.

Roly supports:

* **User-level** reusable roles/sub-roles in a home directory
* **Project-level** configuration + local edits in a repo
* A **review/update** workflow that proposes diffs to sub-roles and lets a user approve changes via a terminal UI
* A **promotion** workflow that explicitly overwrites user-level roles with a project-local version (no branching/merging complexity)

## Key Philosophy (Do Not Violate)

* Deterministic assembly. No runtime mutation of roles during execution.
* Explicit control. No hidden merges or “magic” reconciliation.
* Keep context lean. Top-level roles are general; sub-roles contain specifics.
* We tolerate conceptual “conflicts” in merged guidance; user resolves by curation (role selection/editing).

## Storage & Configuration Layers

Implement two scopes:

### 1) User-level scope (global)

* Stored under a home directory location (recommend: `~/.roly/`).
* Contains user’s global “baseline” roles/sub-roles and assembled user roles if desired.

### 2) Project-level scope (local)

* Stored in repo root via a project config file: `roly.config`
* Defines which user roles to assemble for this project and where to output them.
* Project-local role/sub-role edits are allowed.

## Promotion Model (Simplified Overwrite)

* All edits happen locally by default.
* If user wants to “push” local improvements up to user-level, they run a command that **fully overwrites** the corresponding user-level role/sub-role with the local one.
* No partial promotion. No dependency tracking. No branch graphs.

## Output Definition + Merge Policy

This is critical.

Each role/sub-role may declare an easy-to-parse **Output Definition** describing:

* Output filename template/defaults (optional)
* Output sections (stable keys)
* Section types (`text` or `list`)
* Optional per-section “fields guidance” (e.g., what each issue item should include)

### Merge behavior when assembling a User Role

* Merge by **section name** (stable key, case-normalized).
* `text` sections: merge guidance into one section (union). Conflicts are tolerated; user resolves later.
* `list` sections: merged into one shared list; multiple sub-roles append to the same list.

Example (Reviewer):

* Top-level Reviewer defines keys: Summary (text), Strengths (list), Issues (list), Open Questions (list), Suggestions (list).
* Code Review sub-role adds Issues items.
* Project Audit sub-role adds Issues items.
  => Final output has a single Issues list.

## Output File Naming Default

If no output filename is specified by a sub-role, default naming is:

* `review_{subrole-or-role}_{timestamp}.md`
  Resolution:
* If an active sub-role exists and lacks its own filename setting, use the sub-role name in `{subrole-or-role}`
* Else use the top-level role name

## Roles to Implement First

We are prototyping Reviewer role + 2 sub-roles.

### Top-Level Role: Reviewer (general posture + defaults)

Keep it lean. It should define:

* Diff-first review default (don’t scan entire repo unless needed)
* Severity taxonomy (Critical / Major / Minor)
* General output skeleton (section names only, not deep per-field detail)
* Efficiency rules (high-impact first, avoid nitpicks)
* Failure modes (don’t rewrite code, don’t redesign, etc.)
* Merge policy for output definition blocks (section merge behavior described above)

### Sub-role: Code Review (specific evaluation criteria)

Defines what to look for in implementation quality:

* correctness, maintainability, tests, edge cases, performance pitfalls, etc.
* It should contribute primarily to the Issues list and (optionally) specify the desired fields per issue item.

### Sub-role: Project Audit (plan/compliance evaluation criteria)

Defines what to look for in plan/spec adherence:

* acceptance criteria, completeness, doc/schema alignment, drift, scope creep, etc.
* Also contributes to Issues list (and questions/checklists if needed).

## CLI Requirements (Entry Points)

Implement a CLI (recommend Typer or argparse; choose one and keep it consistent).

Minimum commands (names can vary slightly but should map cleanly):

* `roly list`
  List available roles/sub-roles (built-in, user, project).
* `roly assemble`
  Assemble a User Role from config and/or CLI args. Must be deterministic. Must write output file(s).
* `roly diff`
  Show differences between project-local and user-level versions for a named role/sub-role.
* `roly promote`
  Overwrite user-level role/sub-role with project-local version (explicit, confirm).
* `roly review` (scaffolding is fine)
  Runs the review/update workflow that produces proposed diffs and walks user through approvals.

## Review + Update Workflow (Terminal Approval)

This is the “self-improvement loop.” Implement the mechanics even if the LLM integration is stubbed initially.

Flow:

1. Inputs: conversation transcript (or a file), active User Role, and target sub-role(s) to update.
2. LLM (or stub) returns structured “changes” (add/remove/modify) targeting sub-role file(s).
3. CLI presents changes one-by-one with terminal color:

   * Green additions
   * Red removals
   * Yellow modifications
4. User options:

   * [y] accept
   * [n] reject
   * [a] accept all remaining
   * [q] quit
5. Apply accepted changes to the sub-role file.
6. Optionally allow `roly promote` afterward.

NOTE: Top-level roles should not be auto-modified by this workflow. Only sub-roles (and optionally project-local user-role artifacts).

## File Formats (Implementation Guidance)

Choose a format that is:

* human-editable
* machine-parseable
* merge-friendly

Recommendation:

* Role/sub-role files: Markdown with a clearly delimited YAML (or TOML) front-matter block for the Output Definition + metadata, followed by human-readable instructions.
* `roly.config`: TOML or YAML.

But you must implement:

* stable parsing of Output Definition blocks
* section merge logic
* deterministic assembly output

## Deterministic Assembly Rules

* Exactly one top-level role in a User Role.
* 0..N sub-roles.
* Assembly is concatenation in a defined order:

  1. top-level role content
  2. each sub-role content
* Output Definition blocks are merged per policy into a resolved output schema.

## Non-Goals (Do Not Implement Yet)

* No complex branching/version graphs
* No automatic upstream merges
* No “smart” semantic conflict resolution
* No cloud services
* No heavy UI beyond terminal

## Deliverables

1. A Python package `roly` installable via pip.
2. CLI entry points functioning for list/assemble/diff/promote; review workflow can be stubbed but must include the interactive diff approval mechanism.
3. A default library of built-in roles/sub-roles:

   * Reviewer (top-level)
   * Code Review (sub-role)
   * Project Audit (sub-role)
4. A sample `roly.config` and sample assembled output file(s) showing the merge behavior (especially Issues list shared across both sub-roles).

## Acceptance Criteria (How We’ll Evaluate)

* I can install Roly, run `roly assemble`, and get a single deterministic role file.
* Output Definition merge works: shared “Issues” list receives contributions from both sub-roles.
* `roly promote` overwrites user-level definitions explicitly and safely.
* Review update approval UI works (even if upstream LLM diff generation is mocked).
* The system stays lean: top-level role is general; sub-roles carry specifics.

## Questions You Should Decide Without Asking Me (Make Best Calls)

* Choose YAML vs TOML vs JSON for config and front-matter; pick what’s simplest and robust.
* Choose CLI framework; prefer minimal dependency and good UX.
* Decide directory layout under `~/.roly/` (keep it clean).

Now implement Roly to match this spec. Keep it simple, deterministic, and testable.
