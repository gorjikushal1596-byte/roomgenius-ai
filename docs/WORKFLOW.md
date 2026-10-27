# RoomGenius AI — Reusable Multi-Agent Development Workflow

This document details the standardized multi-agent workflow for engineering RoomGenius AI.

---

## 1. Multi-Agent Team Composition

```
                           +---------------------------+
                           |       User / Product      |
                           +-------------+-------------+
                                         |
                                         v
                            [Task Classification Engine]
                                         |
        +------------------+-------------+-------------+------------------+
        |                  |                           |                  |
        v                  v                           v                  v
+---------------+  +---------------+           +---------------+  +---------------+
|    Agent 1    |  |    Agent 3    |           |    Agent 2    |  |    Agent 4    |
|   Architect   |  |   Fast Task   |           |  Main Coder   |  |   Debugger    |
|  gpt-oss-120b |  |  gpt-oss-20b  |           | qwen3.8-27b   |  | flash-lite    |
+-------+-------+  +-------+-------+           +-------+-------+  +-------+-------+
        |                  |                           ^                  ^
        | Spec & Plan      | Direct patch              | Implementation   | Diagnoses
        +------------------|---------------------------+                  |
                           |                                              |
                           |                   Test Failure (>=2 times)   |
                           +----------------------------------------------+
```

---

## 2. Standard Stage-by-Stage Workflow

### Stage 1: Problem Definition & Architecture (Agent 1)
- **Model**: `openai/gpt-oss-120b` (Route: `groq/openai/gpt-oss-120b`)
- **Trigger**: New feature request, multi-module change, schema change, geometry engine modification.
- **Actions**:
  1. Inspect existing interfaces and dependencies.
  2. Formulate step-by-step implementation plan.
  3. Formulate physical validity requirements (clearance, bounding boxes, collision formulas).
  4. Define acceptance criteria and test strategies.
- **Output Artifact**: `docs/plans/<feature-name>-PLAN.md`

### Stage 2: Core Implementation (Agent 2)
- **Model**: `qwen/qwen3.8-27b` (Route: `groq/qwen/qwen3.8-27b`)
- **Trigger**: Approved implementation plan from Agent 1, or standard feature request.
- **Actions**:
  1. Follow the exact specifications in the plan.
  2. Adhere to YAGNI and standard libraries.
  3. Implement frontend UI, backend API endpoints, and geometry engine rules.
  4. Write unit tests for new logic and collision mathematics.
  5. Run tests locally.
- **Output**: Functional code, clean diffs, passing test suite.

### Stage 3: Rapid Micro-Tasks & Polish (Agent 3)
- **Model**: `openai/gpt-oss-20b` (Route: `groq/openai/gpt-oss-20b`)
- **Trigger**: Well-defined, localized tasks (e.g. "Add a helper to convert meters to millimeters", "Write tests for door swing arc calculation", "Document API schema").
- **Actions**:
  1. Make surgical code modifications.
  2. Run single test or lint check.
- **Output**: Minimal single-file update or test.

### Stage 4: Deep Failure Analysis & Regression Triaging (Agent 4)
- **Model**: `gemini-3.1-flash-lite` (OmniRoute Gemini Provider)
- **Trigger**: Bug persists after 2 attempts by Agent 2, or obscure test failure occurs.
- **Actions**:
  1. Inspect logs, stack traces, and deterministic geometry state.
  2. Isolate the failure into a minimal reproduction case.
  3. Formulate the root-cause hypothesis.
  4. Produce a diagnostic summary and suggested fix strategy.
- **Handoff**: Provide diagnostic findings to **Agent 2** for surgical code application.

---

## 3. RoomGenius AI Architecture Separation & Integrity

```
[ Frontend: React / Three.js / Canvas ]
                 │
                 │ HTTP / WebSocket (GeoJSON / Room Dimensions)
                 ▼
[ Backend: FastAPI (Python) ]
     │                              │
     ▼ (Deterministic Math)         ▼ (AI Natural Language Design Suggestions)
[ Deterministic Geometry Engine ]  [ OmniRoute AI Gateway: http://localhost:20128/v1 ]
 - Collision Detection              - gpt-oss-120b (Architecture/Layout reasoning)
 - Minimum Clearances               - qwen3.8-27b (Code/Schema generation)
 - Door/Window Swing Polygons       - gpt-oss-20b (Fast micro tasks)
 - Bounding Box Clipping            - gemini-3.1-flash-lite (Debugging)
```

**Crucial Engineering Rule:**
The AI models propose room arrangements, furniture groupings, and color palettes. However, the layout **MUST ALWAYS** pass through the deterministic geometry engine before being saved or marked as "valid". If an AI-suggested placement produces a bounding collision or violates egress clearance, the application must flag it or snap it to a valid position.

---

## 4. Test Prompts for Each Agent

1. **Agent 1 (Architect)**:
   > "We need to design the data model and API contract for multi-wall room definitions, including angled walls and door cutouts. Provide the complete architecture plan, data schemas, collision boundary strategy, and test plan."

2. **Agent 2 (Main Coder)**:
   > "Implement the 2D bounding box collision detection utility in `src/geometry/collision.ts` according to the architecture specification. Support oriented bounding boxes (OBB) with rotation angles. Include unit tests."

3. **Agent 3 (Fast Task)**:
   > "Create a utility function `convertDimensions(val, fromUnit, toUnit)` that converts between millimeters, centimeters, meters, and inches with standard precision. Add unit tests."

4. **Agent 4 (Debugging & Fallback)**:
   > "The collision detector fails intermittently when furniture is placed exactly flush (0 distance) with south-facing angled walls. Here are the failing test logs and coordinate data. Diagnose the floating-point or vertex-ordering issue and provide the reproduction test."
