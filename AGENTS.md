# RoomGenius AI — Multi-Agent Configuration & Architectural Rules

## 1. System Overview & Core Philosophy
RoomGenius AI is an AI-powered room interior design application.
- **AI Role**: Interpret user natural language preferences, recommend design aesthetic styles, propose 2D/3D layout arrangements, and explain architectural reasoning.
- **Deterministic Engine Role**: Strictly enforce room dimensions, furniture bounding boxes, collision boundaries, egress pathways, and required clearance zones (doors, windows, radiators).
- **Golden Rule**: **Never claim that a layout is physically valid unless deterministic application validation confirms it.**

---

## 2. OmniRoute Confirmed Model Registry & Multi-Agent Matrix

| Agent Role | Model ID | OmniRoute Provider Route | Activation Triggers | Primary Output | Constraints |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Agent 1: Architect & Planner** | `openai/gpt-oss-120b` | `groq/openai/gpt-oss-120b` | New major features, unclear requirements, system architecture, geometry schema design, multi-module coordination | Implementation plan, affected files list, dependencies, acceptance criteria, risks, test strategy | Do NOT use for routine single-file code edits or micro-tasks |
| **Agent 2: Main Coding Agent** *(Default)* | `qwen/qwen3.8-27b` | `groq/qwen/qwen3.8-27b` | React/TypeScript UI, Python/FastAPI backend, geometry math & collisions, API integration, ordinary bug fixes | Working tested code, surgical diffs, unit/integration tests, file change summary | Default implementation agent. Adhere strictly to YAGNI and deterministic rules |
| **Agent 3: Fast Task Agent** | `openai/gpt-oss-20b` | `groq/openai/gpt-oss-20b` | Simple utility functions, single-component tweaks, isolated unit tests, type definitions, docstrings, cleanup | Immediate code patch, isolated test, doc file | Requires explicit bounded scope. Do NOT invoke for broad refactoring or architectural planning |
| **Agent 4: Debugging & Fallback Agent** | `gemini-3.1-flash-lite` | Direct OmniRoute Gemini Provider Route | Repeated test failures (>=2 attempts by Agent 2), obscure geometry errors, silent state bugs, runtime regressions | Diagnostic report, root-cause hypothesis, regression test proposals | Diagnostic first: does NOT directly write production code edits. Returns findings to Agent 2 for implementation |

> [!IMPORTANT]
> **Disallowed / Deprecated Models**: Do not use `Kimi K2 Thinking`, `Qwen3 Coder Plus`, `Qwen3 Coder Flash`, or `DeepSeek R1`.
> **Model Substitution Policy**: Never silently substitute models if a configured model fails or hits quota. Log/report the failure explicitly and prompt the user for an approved fallback.

---

## 3. Strict Task Routing Policy

When receiving a development task, classify and route according to these 6 rules:

1. **Complex Planning or Architecture** &rarr; Activate **Agent 1** (`openai/gpt-oss-120b`). Produce architecture/plan first; do not jump directly to code.
2. **Small, Clearly Scoped Task** &rarr; Activate **Agent 3** (`openai/gpt-oss-20b`). Execute bounded patch quickly.
3. **Normal Feature Development or Multi-File Implementation** &rarr; Activate **Agent 2** (`qwen/qwen3.8-27b`).
4. **Difficult Bug or Repeated Test Failure** &rarr; Activate **Agent 4** (`gemini-3.1-flash-lite`) to diagnose root cause, produce minimal reproduction test, then hand off to **Agent 2** to implement the fix.
5. **Major Feature with Unclear Requirements** &rarr; **Agent 1** plans and produces specification &rarr; **Agent 2** implements &rarr; deterministic validation and test suites verify.
6. **Model Failure or Rate Limit** &rarr; Halt the failing step immediately. Report exact model ID and error to the user. Request user approval or switch to an explicitly declared fallback.

*Note: Antigravity IDE uses the active model selected in the model picker or CLI profile. Switch model in the IDE chat selector to match the target Agent before executing the respective stage, or utilize specialized persona skills.*

---

## 4. RoomGenius AI Engineering & Architectural Standards

### 4.1 Boundary Separation
- **Frontend** (`src/web` or `frontend/`): React, TypeScript, Canvas/Three.js/WebGL for visual floorplan editing. Purely handles state, user gestures, and visual rendering.
- **Backend** (`src/api` or `backend/`): Python / FastAPI (or Node/Express), REST/WebSocket endpoints for layout generation and project persistence.
- **Deterministic Geometry & Validation** (`src/geometry` or `backend/engine/`): Pure functional logic calculating bounding boxes, polygons, convex hulls, clearance corridors, door swing clearances, and wall intersections.
- **AI Integration** (`src/ai` or `backend/ai/`): Prompts, schemas, and LLM calls via OmniRoute (`http://localhost:20128/v1`). Converts natural language into structured layout constraints.

### 4.2 Deterministic Safety Rules
1. **Physical Validity Guarantee**: Bounding boxes of furniture items must not overlap with walls, windows, doors, or other items unless explicitly defined as stackable (e.g., rugs under tables).
2. **Clearance Enforcements**: Egress pathways (minimum 75cm - 90cm depending on standard) must remain clear.
3. **Unit Consistency**: All internal coordinates and geometric calculations must standardize on millimeters (mm) or centimeters (cm). Never mix imperial and metric units internally.
4. **Idempotency & Precision**: Collision detection functions must be pure, deterministic, and covered with unit tests.

---

## 5. Agent Handoffs & Execution Safety Protocols

1. **Sequential Coordination**:
   - Agent 1 produces `PLAN.md` / `SPEC.md` &rarr; User reviews &rarr; Agent 2 executes.
   - Agent 4 produces `DIAGNOSIS.md` with regression test &rarr; Agent 2 applies fix.
2. **No Concurrent File Modification**: Multiple agents must never write to the same files simultaneously without coordination.
3. **Git & State Preservation**:
   - Never run destructive git commands (`git reset --hard`, `git clean -fd`, `git checkout -- .`) without explicit user permission.
   - Preserve existing Git branches and uncommitted changes.
4. **Verification Integrity**:
   - Run relevant test suites and build checks after every edit.
   - Honestly record failed tests, geometric inaccuracies, and unresolved bugs. Never claim success if a test failed.
