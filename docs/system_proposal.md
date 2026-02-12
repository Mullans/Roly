# Modular Role System for Coding Agents

## 1. Core Concepts

### 1.1 Role (Top-Level Role)

* Foundational behavioral and epistemic identity.
* Example: Programmer, Reviewer, UX Designer, Systems Architect.
* Contains:

  * Core reasoning style
  * Quality standards
  * Failure modes to avoid
  * Validation philosophy
* Should be stable and rarely auto-modified.

### 1.2 Sub-Role

* Refinement layer applied on top of a Role.
* Contextual and domain-specific.
* Example:

  * Python Specialist
  * SQLite Expert
  * Frontend Accessibility Focus
  * Performance Optimization Focus
* Assumes the Role already exists.
* May be iteratively improved.

### 1.3 User Role

* Assembled artifact used by the agent.

* Constructed as:

  [Top-Level Role]
  +
  [One or More Sub-Roles]

* Stored as a single generated file.

* Immutable during execution.

* Versioned.

---

## 2. Assembly Model

### 2.1 Composition Rules

* Exactly one Top-Level Role.
* Zero or more Sub-Roles.
* Sub-Roles are ordered (later ones override earlier ones if conflicts exist).
* No dynamic rewriting during execution.

### 2.2 File Generation

Concatenation order:

1. Top-Level Role content
2. Sub-Role 1
3. Sub-Role 2
4. ...

Each section clearly delimited.

---

## 3. Review System (Separate Skill)

### 3.1 Philosophy

Review is explicit, not automatic.
Triggered intentionally by the user.

### 3.2 Review Inputs

* Conversation transcript
* Active User Role
* Sub-Roles only (Top-Level excluded from modification scope)

### 3.3 Review Output

The LLM produces:

* Strengths of role performance
* Pain points or failure patterns
* Proposed improvements

Improvements formatted as structured diffs against Sub-Role files.

Example structure:

* ADD: <instruction>
* REMOVE: <instruction>
* MODIFY: <old> → <new>

---

## 4. Interactive Update Mechanism

### 4.1 CLI Workflow

For each proposed change:

1. Display diff (color-coded)

   * Green: additions
   * Red: removals
   * Yellow: modifications

2. Prompt user:

   * [y] accept
   * [n] reject
   * [a] accept all remaining
   * [q] quit

3. Apply accepted changes to Sub-Role file.

### 4.2 Safeguards

* Top-Level Roles cannot be auto-modified.
* All changes require confirmation unless “accept all” chosen.
* Version history maintained.

---

## 5. Design Decisions to Refine

1. Should Sub-Roles declare dependencies?
2. Should conflicts be detected automatically?
3. Should role performance metrics be stored across sessions?
4. Should roles be project-scoped or global by default?
5. Should we allow temporary session-only Sub-Roles?

---

## 6. Architectural Options

### Option A: Role Assembler Skill

* Handles:

  * Role discovery
  * Composition
  * File generation
  * Versioning

### Option B: External CLI Tool

* Written in Python.
* Skills only consume final User Role.
* Cleaner separation of responsibilities.

### Option C: Hybrid

* CLI manages filesystem.
* Skill handles semantic reasoning.

---

## 7. Key Insight

The system should optimize for:

* Predictability
* Composability
* Human trust
* Iterative refinement

Not maximum automation.

---

## 8. Open Strategic Question

Is this primarily:

* A productivity tool?
* A research framework for prompt-role experimentation?
* A reusable infrastructure layer?

The answer affects complexity tolerance and UX philosophy.

---

## 9. Refined Conceptual Model (Tightened Definitions)

### 9.1 Role = Workflow-Phase Operating Mode

A Top-Level Role is best defined as a **workflow-phase operating mode**—a reusable mindset that tells the agent *how to behave* during a specific phase of work.

This matches your examples directly:

* **Planner**: reads schemas/planning docs, identifies gaps, proposes refinements, converges on a coherent plan.
* **Programmer**: implements the agreed plan with strong engineering practices.
* **Reviewer**: evaluates progress on a feature, checks code quality, correctness, tests, and alignment to the plan.

Roles should encode:

* Primary objective for the phase
* What inputs to trust (docs, schemas, codebase)
* What outputs to produce (plan deltas, PR-ready changes, review notes)
* Quality bar and acceptance criteria
* Default tradeoffs (speed vs rigor, minimal changes vs refactor)
* Common failure modes to avoid

Roles should **not** encode:

* Specific tech stacks (Python vs Rust)
* Project-local conventions (unless they’re globally true for you)

Roles are stable, phase-shaped, and intentionally reusable across projects.

---

### 9.2 Sub-Role = Domain + Constraint Overlay

A Sub-Role is an overlay that adds domain expertise or constraints *within the active phase role*.

Examples:

* **Python 3.12 + typing-first**
* **SQLite / migrations / performance**
* **ONNX / TensorRT / Triton integration**
* **UI/UX friction finder**
* **Security-first**
* **Test strategy (unit/integration/e2e)**

Sub-Roles:

* Assume a Top-Level Role (Planner/Programmer/Reviewer)
* Narrow the agent’s attention and standards
* Can be composed and iterated frequently
* Are the primary target of automatic review-driven updates

Heuristic: keep sub-roles small and single-purpose.

---

### 9.3 User Role = Resolved Execution Contract

A User Role is the assembled, deterministic prompt artifact provided to the agent for a session.

It is:

* One Top-Level Role (Planner *or* Programmer *or* Reviewer)
* Plus 0..N Sub-Roles
* Plus (optionally) project-local addenda (coding standards, repo conventions)

Key properties:

* Deterministic (no runtime mutation)
* Versioned and reproducible
* Traceable to component source files

---

### 9.4 Skills vs Roles (Boundary)

* **Roles** shape mindset and outputs (how to think + what to produce).
* **Skills** provide capabilities (read files, run tests, apply diffs, generate artifacts).

A clean rule:

* The Planner/Programmer/Reviewer *role text* defines behavioral defaults.
* The Review/Assembler *skill* does mechanical work (diffing, applying patches, prompting for approval).

This keeps "who I am" separate from "what tools I can use."

---

### 9.5 Practical Mapping to Your Workflow

Your workflow becomes a consistent triad:

* **Planning phase**: invoke Planner role + relevant domain sub-roles → refine docs/schemas.
* **Implementation phase**: invoke Programmer role + language/framework sub-roles → implement plan.
* **Review phase**: invoke Reviewer role + domain sub-roles → evaluate feature or milestone.

This reduces repeated prompting because the *mindset* is embedded.

---

## 10. Plan of Next Steps

### Phase 1 — Conceptual Solidification (Current Phase)

* [ ] Stress-test refined model with concrete examples
* [ ] Identify edge cases (conflicting sub-roles, ordering rules)
* [ ] Decide on dependency model (if any)

### Phase 2 — UX & Workflow Design

* [ ] Define user flow for creating a User Role
* [ ] Define directory structure for Role/Sub-Role storage
* [ ] Design CLI interaction model for assembly
* [ ] Design CLI interaction model for review + diff approval

### Phase 3 — Review System Formalization

* [ ] Define structured diff schema
* [ ] Define versioning strategy
* [ ] Define change-approval protocol
* [ ] Define rollback mechanism

### Phase 4 — Implementation Architecture

* [ ] Decide CLI vs Skill vs Hybrid model
* [ ] Define Python package structure
* [ ] Define configuration format (YAML / JSON / TOML)
* [ ] Define integration points with coding agents

### Phase 5 — Validation & Iteration

* [ ] Test with 2–3 real workflows
* [ ] Measure perceived output quality differences
* [ ] Refine Sub-Role granularity heuristics

---

### Current Position

We are in: **Phase 1 — Conceptual Solidification**

Next immediate action: Stress-test with a realistic scenario.

---

## 11. Reviewer Prototype (Top-Level + Sub-Roles)

### 11.1 Top-Level Role: Reviewer (General Evaluation Posture)

**Purpose**

* Evaluate work without redesigning it.
* Identify risks, gaps, and quality issues.
* Classify issues by severity.

**Scope Discipline**

* Default to reviewing diffs rather than entire codebase.
* Only expand scope if necessary.
* Avoid speculative redesign.

**Output Structure (General Format)**

* Summary
* Strengths
* Issues (grouped by severity)
* Open Questions
* Optional Suggestions (clearly marked as non-blocking)

**Severity Model**

* Critical (must fix)
* Major (should fix)
* Minor (nice to improve)

**Efficiency Principles**

* Focus on high-impact issues first.
* Avoid nitpicking unless it signals deeper problems.
* Be concise but precise.

**Failure Modes to Avoid**

* Turning review into implementation.
* Rewriting code unnecessarily.
* Ignoring original plan or requirements.
* Over-indexing on personal style.

---

### 11.2 Sub-Role: Code Review

**Primary Focus**

* Code correctness
* Readability and maintainability
* Test coverage and validity
* Edge-case handling
* Performance pitfalls

**Evaluation Areas**

* Does the implementation match the plan?
* Are types, validations, and error handling sufficient?
* Are abstractions clean and minimal?
* Are there hidden coupling or future maintenance risks?

**Diff-Specific Checks**

* Are unrelated changes included?
* Are refactors justified?
* Is the diff size appropriate for the change?

**Testing Checks**

* Are new behaviors covered?
* Are tests meaningful (not superficial)?

**Common Code Smells**

* Over-engineering
* Premature optimization
* Missing validation
* Magic constants
* Silent failure paths

---

### 11.3 Sub-Role: Project Audit

**Primary Focus**

* Plan compliance
* Feature completeness
* Schema/document alignment
* Milestone integrity

**Evaluation Areas**

* Does implementation match the planning documents?
* Are all acceptance criteria satisfied?
* Are edge cases addressed per plan?
* Are any requirements partially implemented?

**Cross-Artifact Checks**

* Code vs plan consistency
* Schema vs implementation consistency
* Documentation drift

**Risk Assessment**

* Architectural fragility
* Incomplete features masked as done
* Technical debt accumulation

**Audit Output Emphasis**

* Explicitly call out missing deliverables
* Flag plan ambiguities
* Highlight scope creep

---

## 12. Output Definition + Merge Policy

### 12.1 Goal

Enable multiple sub-roles to contribute to a single coherent output by defining output requirements in a structured, easy-to-parse way.

### 12.2 Output Definition Block (Role/Sub-Role)

Each Role/Sub-Role may include an **Output Definition** block that declares:

* Output file naming defaults (optional)
* Output sections (by stable section name)
* Section type (text vs list)
* Optional section-specific fields (sub-role specific)

### 12.3 Merge Rule (User Role Assembly)

When assembling a User Role with multiple sub-roles:

1. **Collect** all Output Definition blocks.
2. **Merge by section name** (stable string key, case-normalized).
3. **Section type governs merge behavior**:

   * **text**: merged into one section; content guidance is unioned. Any conflicting guidance is left for the user to resolve when curating User Roles.
   * **list**: merged into one shared list; each sub-role contributes items to the same list object.

### 12.4 Intended Reviewer Example

Top-level Reviewer defines the global skeleton and section keys:

* Summary (text)
* Strengths (list)
* Issues (list)
* Open Questions (list)
* Suggestions (list)

Sub-roles contribute to the same keys:

* Code Review adds Issue items and optionally fields guidance for each Issue.
* Project Audit adds Issue items and optionally fields guidance for each Issue.

Result:

* A single **Issues** list containing both code-review and audit findings.

### 12.5 Conflict Handling Policy

* The system does not attempt deep semantic reconciliation.
* Conflicts are tolerated; the assembled User Role contains merged guidance.
* If conflicts degrade quality, the user resolves by adjusting sub-role selection or editing the generated User Role.

### 12.6 Output File Naming Default

* If no explicit output filename is provided by any sub-role:

  * Use top-level default template.
  * Populate `{role}` with the *active sub-role name* if present, else the top-level role name.

---

This structure keeps:

* Top-Level = posture + format keys + merge policy
* Sub-Roles = what to evaluate + domain-specific criteria + section contributions

---

## 13. Delivery Architecture — Roly Python Package

### 13.1 Package Overview

The role system will be delivered as a Python package named:

**Roly (R-O-L-L-I-E)**

Responsibilities:

* Store built-in Top-Level Roles and Sub-Roles
* Assemble User Roles
* Manage project-level and user-level configurations
* Provide CLI entry points
* Provide optional skill integration
* Handle diff-based review + update workflow

---

### 13.2 Configuration Layers

Roly supports two configuration scopes:

#### 1️⃣ User-Level Configuration

* Stored in user home directory (e.g., `~/.roly/`)
* Contains reusable roles and sub-roles
* Acts as the global baseline

#### 2️⃣ Project-Level Configuration

* Stored in project root (e.g., `roly.config`)
* Defines which roles are used in this project
* May contain project-specific overrides

---

### 13.3 Role Storage Model

#### Built-in Roles

* Shipped with Roly package
* Read-only by default

#### User-Level Roles

* Created or promoted from projects
* Overwrite-based model (no complex branching)

#### Project-Level Roles

* Derived from user-level or built-in roles
* Editable locally
* May diverge intentionally

---

## 14. Local vs Global Update Model (Simplified)

### 14.1 Default Rule

All edits occur locally (project-level) by default.

### 14.2 Promotion Model

If a user decides local improvements should become global:

They explicitly run:

* "Promote to user-level"

This action:

* Fully replaces the user-level version of that role
* Does not attempt partial merges
* Avoids complex dependency tracking

This keeps the system simple and predictable.

### 14.3 No Automatic Branch Tracking

We intentionally do NOT:

* Track branching trees
* Auto-merge upstream changes
* Maintain dependency graphs

Instead:

* Local roles are forks
* Promotion is explicit overwrite
* User is always in control

---

## 15. CLI Entry Points

Roly exposes CLI entry points such as:

* `roly assemble`
* `roly review`
* `roly promote`
* `roly list`
* `roly diff`

Capabilities:

* Assemble User Role from config
* Generate role file at specified output path
* Run review diff workflow
* Promote local role to global

---

## 16. Roly Skill Integration

Roly may optionally install a skill into:

* Project-level agent skill directory
* User-level agent skill directory

Skill responsibilities:

* Invoke review workflow
* Trigger diff display (green/red/yellow)
* Guide interactive approval process
* Update sub-role files

Skill does NOT:

* Redefine role architecture
* Perform hidden merges

---

## 17. Review + Self-Improvement Workflow

1. Agent performs task using User Role.
2. User invokes review pathway.
3. Review skill:

   * Analyzes conversation
   * Generates structured diffs against Sub-Roles
4. CLI displays:

   * Additions (green)
   * Removals (red)
   * Modifications (yellow)
5. User chooses:

   * Accept
   * Reject
   * Accept all
   * Quit
6. Accepted changes update local Sub-Role.

Optional:

* Promote updated Sub-Role to user-level.

---

## 18. Output Definition Merge Model (Refined)

### Merge by Section Name

* Sections identified by stable keys
* Case-normalized

### Section Types

* `text`
* `list`

### List Behavior

When multiple sub-roles define the same list section:

* All contributions append to a shared list

Example:

Reviewer defines:

* Issues (list)

Code Review adds issue items.
Project Audit adds issue items.

Final User Role has one unified Issues list.

---

## 19. Output File Naming Policy

If no sub-role specifies output filename:

Top-level default template:

`review_{subrole-or-role}_{timestamp}.md`

Resolution rule:

* If sub-role active → use sub-role name
* Else → use top-level role name

---

## 20. System Philosophy

Roly optimizes for:

* Predictability over automation
* Explicit control over hidden magic
* Layered configuration (global → project)
* Deterministic role assembly
* Lightweight mental overhead

---

### Updated Current Position

We have now defined:

* Conceptual model (Role vs Sub-Role vs User Role)
* Reviewer prototype
* Output merge policy
* Package architecture (Roly)
* Local vs global promotion model
* CLI + skill integration

Next major design decision:

Define the exact on-disk schema format for:

* Role files
* Output definition blocks
* roly.config structure
