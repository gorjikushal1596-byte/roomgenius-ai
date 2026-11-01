# 🏠 RoomGenius AI

> **Deterministic 2D Room Geometry Engine + Meta Muse Spark Architectural Intelligence**  
> *Built for the Meta Global AI Developer Hackathon*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.3.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.3-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Meta Model API](https://img.shields.io/badge/Meta%20Muse%20Spark-1.3-0668E1?logo=meta&logoColor=white)](https://api.meta.ai)
[![Pytest Tests](https://img.shields.io/badge/Pytest-73%20passed-success)](https://pytest.org)
[![CodeRabbit Clean](https://img.shields.io/badge/CodeRabbit-0%20findings-brightgreen)](https://coderabbit.ai)

---

## 1. Project Overview

**RoomGenius AI** is an intelligent interior design application that generates guaranteed physical 2D room layouts and provides human-readable architectural critiques.

Unlike pure generative AI tools that hallucinate furniture through walls or overlap items, RoomGenius AI follows a **strict dual-engine philosophy**:
- **Deterministic Engine (Python)**: Acts as the unyielding physical source of truth, calculating bounding boxes, collision boundaries, and room clearances.
- **Meta Muse Spark (`muse-spark-1.3`)**: Acts as the architectural interior design consultant, interpreting user natural language aesthetic preferences and explaining *why* the arrangement works.

> **Golden Architectural Rule**: The AI model is strictly grounded in deterministic layout coordinates. It is physically impossible for the AI to override coordinates, move walls, or fabricate impossible placements.

---

## 2. Problem Statement & Solution

### The Problem
Generative AI models and text-to-3D tools suffer from **spatial hallucinations**:
- Furniture items overlap into the same physical space.
- Items are placed outside room perimeter boundaries.
- Walkway egress paths and door clearances are ignored.
- LLM prompt estimates fail basic geometric collision checks.

### The Solution: Dual-Engine Synergy
RoomGenius AI decouples **spatial physics** from **aesthetic reasoning**:
1. **Mathematical Safety**: A pure Python 2D Axis-Aligned Bounding Box (AABB) candidate-anchor engine packs furniture items with zero positive-area overlap and guaranteed boundary containment.
2. **Architectural Rationale**: Meta Muse Spark interprets the user's aesthetic style (e.g., *Minimalist Scandinavian*, *Modern Industrial*) and provides step-by-step physical arrangement guidance, lighting recommendations, and space trade-offs.

---

## 3. Main Features

- 📐 **Deterministic Physical Packing**: Mathematical collision detection with 0° and 90° orientation support.
- 🖼️ **Interactive Responsive 2D SVG Visualizer**: Real-time vector floorplan rendering with dynamic dimension scaling ($S$) supporting rooms from 100 cm up to 2,000 cm.
- ⚖️ **Truthful Before / After Comparison**: Side-by-side view showing unarranged user inventory alongside the resulting 2D floorplan with floor utilization metrics.
- ✨ **Meta Muse Spark Architectural Critique**: Explains layout rationale, ergonomic circulation paths, and clearance trade-offs using official Meta Model API reasoning.
- ⚡ **Demo Quick-Presets**: 1-click loading of curated rooms (*Master Bedroom*, *Home Office*, *Crowded Studio*) for effortless judge evaluation.
- 🛡️ **Offline & DoS Resilience**: Built-in zero-credit deterministic mock engine, concurrency limiters (`BoundedSemaphore`), and CWE-770 input bounds.
- ♿ **Accessible & Keyboard Friendly**: Full keyboard navigation (`Tab`, `Enter`, `Space`) with cross-highlighting across floorplan and inventory tables.

---

## 4. Technology Stack

### Backend
- **Language**: Python 3.11+ / 3.14
- **Web Framework**: FastAPI & Starlette
- **Geometry & Validation**: Pydantic v2 + Python Standard Library (`dataclasses`, `urllib.request`)
- **Testing**: Pytest (108 automated tests)
- **AI Models**:
  - **Meta Muse Spark** (`muse-spark-1.3`): Natural language architectural reasoning and layout critique
  - **Meta SAM 3.1** (`sam-3.1`): Zero-shot furniture object segmentation and 2D bounding boxes from room photos
  - **Depth Anything V2** (`vits` Metric Indoor): $Z$-axis depth layering and scene structure visualization
  - **Meta Muse Image** (`muse-image-1.0`): Photorealistic interior redesign concept rendering grounded in deterministic coordinates

### Frontend
- **Framework**: React 19 + TypeScript + Vite
- **Visuals**: Native SVG with dynamic viewBox and marker scaling
- **Linting & Quality**: Oxlint (0 warnings, 0 errors)
- **Code Review**: CodeRabbit CLI (0 findings)

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Browser (React 19 + TS)                 │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Room & Furniture Form│  │ 2D Vector Visualizer (SVG)       │ │
│  │ & Demo Quick-Presets │  │ Before / After Comparison Grid   │ │
│  └──────────┬───────────┘  └─────────────────▲────────────────┘ │
└─────────────┼────────────────────────────────┼──────────────────┘
              │ POST /layout                   │
              │ (Dimensions & Furniture)       │ Coordinates (x, y)
              ▼                                │ & Rotations (0°/90°)
┌──────────────────────────────────────────────┴──────────────────┐
│                   FastAPI Backend (port 8000)                   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Pydantic Request Validation (Schemas & String Bounds)     │ │
│  └──────────────────────────┬─────────────────────────────────┘ │
│                             ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Deterministic 2D Geometry Engine (geometry.py)            │ │
│  │  - Axis-Aligned Bounding Box (AABB) Collision Detection    │ │
│  │  - Candidate-Anchor Top-Left Corner Placement              │ │
│  │  - 0° and 90° Rotations with Boundary Containment Check   │ │
│  │  - Unplaced Item Classification & Reason Assignment        │ │
│  └──────────────────────────┬─────────────────────────────────┘ │
│                             │                                   │
│                             ▼ POST /ai/explain                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Meta Muse Spark Service (ai.py)                           │ │
│  │  - Concurrency Limiter (BoundedSemaphore)                  │ │
│  │  - Physical Safety System Prompt (Locked Coordinates)      │ │
│  │  - Zero-Credit Mock Engine & Offline Fallback              │ │
│  └──────────────────────────┬─────────────────────────────────┘ │
└─────────────────────────────┼───────────────────────────────────┘
                              │ HTTPS (Bearer Auth)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│             Official Meta Model API (api.meta.ai)               │
│                Model: muse-spark-1.3                            │
│  - Internal Architectural Reasoning Trace                       │
│  - Structured JSON Output (Summary, Reasoning, Tips, Tradeoffs) │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. How the Deterministic Layout Engine Works

Located in [`backend/geometry.py`](backend/geometry.py), the geometry engine operates in centimetre (`cm`) units using an origin `(0, 0)` at the room's top-left corner:

1. **Sorting**: Sorts incoming furniture by footprint area descending (`width * length`) with stable unique ID tie-breaking.
2. **Anchor Point Generation**: Evaluates candidate coordinates $(x, y)$ starting at `(0, 0)` and along edges/corners of previously placed items:
   $$(x_{\text{right}}, y),\quad (x_{\text{right}}, 0),\quad (x, y_{\text{bottom}}),\quad (0, y_{\text{bottom}}),\quad (x_{\text{right}}, y_{\text{bottom}})$$
3. **Boundary Verification**: Evaluates containment within room boundary $[0, W] \times [0, L]$:
   $$x \ge 0,\quad y \ge 0,\quad x + w_{\text{eff}} \le W + \epsilon,\quad y + l_{\text{eff}} \le L + \epsilon$$
4. **Collision Checking**: Uses Axis-Aligned Bounding Box (AABB) intersection testing. Zero-area touching borders are allowed; positive-area overlap ($> 10^{-4}\text{ cm}$) is strictly rejected:
   $$\text{overlap}_x = \min(r_1.\text{right}, r_2.\text{right}) - \max(r_1.x, r_2.x) > \epsilon$$
   $$\text{overlap}_y = \min(r_1.\text{bottom}, r_2.\text{bottom}) - \max(r_1.y, r_2.y) > \epsilon$$
5. **Orientation Switching**: Attempts standard 0° orientation first; if it collides or exceeds boundaries, evaluates 90° swapped orientation.
6. **Rejection Details**: If an item cannot fit at any candidate point in any orientation, it is recorded in `unplaced_items` with an explicit architectural rejection reason.

---

## 7. Meta Model API Integration

Located in [`backend/ai.py`](backend/ai.py):
- **Model**: `muse-spark-1.3`
- **Endpoint**: `https://api.meta.ai/v1/chat/completions`
- **Protocol**: HTTPS POST via Python standard library `urllib.request` (zero SDK dependencies).
- **Physical Safety Guardrail**: The system prompt provides the exact deterministic coordinates and commands the model:
  > *"The 2D coordinates (x, y) and orientations (0° or 90°) have been deterministically computed and validated by our physical geometry engine. You must NEVER alter, fabricate, or contradict these coordinates."*
- **Reasoning Handling**: Meta Muse Spark is a reasoning model. The service sets `reasoning_effort: "low"` and parses both `reasoning_content` (the model's thought process) and `content` (structured JSON).
- **Credit Conservation & Mock Engine**: Includes [`generate_mock_explanation()`](backend/ai.py), ensuring **zero credits** are consumed during testing, automated CI/CD runs, or offline demonstrations.

---

## 8. Project Directory Structure

```
ROOMGENIUS AI/
├── .env.example              # Template for environment variables (safe placeholders)
├── .gitignore                # Git ignore rules (.env, node_modules, .venv, etc.)
├── AGENTS.md                 # Multi-agent architecture and model routing guidelines
├── PROJECT_STATUS.md         # Daily development logs, verified tests, and audit trails
├── README.md                 # Complete project documentation and guide
│
├── backend/
│   ├── .env                  # Backend credentials (git-ignored, never committed)
│   ├── .env.example          # Backend-specific environment template
│   ├── ai.py                 # Meta Muse Spark service, prompt guardrails & mock engine
│   ├── geometry.py           # Pure deterministic 2D AABB geometry & collision engine
│   ├── main.py               # FastAPI application entry point, CORS & endpoints
│   ├── requirements.txt      # Python dependencies (fastapi, uvicorn, pydantic, pytest)
│   ├── schemas.py            # Pydantic v2 schemas and DoS string length bounds
│   ├── smoke_test_meta.py    # One-shot live smoke test for official Meta Model API
│   ├── smoke_test_baseten.py # Historical smoke test for Baseten provider
│   ├── test_ai.py            # 13 tests for AI service, prompts, and DoS limits
│   ├── test_e2e_scenarios.py # 12 E2E integration tests covering all hackathon scenarios
│   ├── test_geometry.py      # 14 tests for collision math, rotation & boundaries
│   └── test_layout.py        # 25 tests for FastAPI layout endpoint validation
│
└── frontend/
    ├── index.html            # Single page app entry HTML
    ├── package.json          # React, Vite, TypeScript, and Oxlint scripts
    ├── vite.config.ts        # Vite build config with /api reverse proxy to backend
    └── src/
        ├── App.tsx           # Main React component, state, form & AI explanation card
        ├── App.css           # Responsive styles, comparison grid, and animations
        ├── RoomVisualizer.tsx# Native responsive SVG floorplan visualizer
        ├── main.tsx          # React DOM entry point
        └── index.css         # Reset and global base styles
```

---

## 9. Prerequisites

- **Windows 11 / macOS / Linux**
- **Python 3.11+** (Python 3.14 verified)
- **Node.js 18+** & `npm`
- **Meta Model API Key** (optional: app automatically uses instant mock mode if key is omitted)

---

## 10. Frontend Installation & Startup

```powershell
# 1. Navigate to frontend folder
cd "frontend"

# 2. Install dependencies
npm install

# 3. Start development server (port 5173)
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## 11. Backend Installation & Startup

```powershell
# 1. Navigate to backend folder
cd "backend"

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
# source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start FastAPI server (port 8000)
uvicorn main:app --port 8000 --reload
```

Interactive API documentation (Swagger) is available at `http://localhost:8000/docs`.

---

## 12. Environment Variable Configuration

Copy `.env.example` to `backend/.env`:

```powershell
cp .env.example backend/.env
```

Edit `backend/.env` with your credentials:

```ini
# Official Meta Model API (Day 5 & 6)
META_API_KEY="LLM_your_official_meta_api_key_here"
META_BASE_URL="https://api.meta.ai/v1"
META_MODEL="muse-spark-1.3"

# Optional: Set to true to force zero-credit deterministic mock mode
MOCK_AI="false"
```

> **Security Guarantee**: `backend/.env` is listed in `.gitignore` and is **never** committed to version control.

---

## 13. Testing Commands

All 108 tests run with **zero external API calls** to conserve model credits:

```powershell
# Run full backend test suite (108 tests)
cd "backend"
.venv\Scripts\python.exe -m pytest -v

# Run frontend type-check & lint
cd "../frontend"
npx tsc --noEmit
npm run lint

# Run frontend production build
npm run build
```

---

## 14. Sample Input & Expected Output

### Input: `POST /layout`
```json
{
  "width": 400.0,
  "length": 500.0,
  "unit": "cm",
  "furniture": [
    {"id": "bed-1", "name": "Queen Bed", "width": 160.0, "length": 200.0},
    {"id": "desk-1", "name": "Study Desk", "width": 120.0, "length": 60.0}
  ],
  "preferences": {"style": "minimalist"}
}
```

### Output: `LayoutResponse`
```json
{
  "status": "accepted",
  "feasible": true,
  "summary": {
    "room_width_cm": 400.0,
    "room_length_cm": 500.0,
    "furniture_count": 2,
    "placed_count": 2,
    "unplaced_count": 0
  },
  "placed_items": [
    {
      "id": "bed-1",
      "name": "Queen Bed",
      "placed": true,
      "x": 0.0,
      "y": 0.0,
      "width": 160.0,
      "length": 200.0,
      "rotation": 0,
      "within_bounds": true
    },
    {
      "id": "desk-1",
      "name": "Study Desk",
      "placed": true,
      "x": 160.0,
      "y": 0.0,
      "width": 120.0,
      "length": 60.0,
      "rotation": 0,
      "within_bounds": true
    }
  ],
  "unplaced_items": []
}
```

---

## 15. Known Limitations

- **Orthogonal Orientations**: The deterministic engine currently supports 0° and 90° rotations (diagonal 45° placements are not supported in the 2D AABB engine).
- **Rectangular Rooms**: Rooms are modeled as 2D bounding rectangles $[0, W] \times [0, L]$ (non-orthogonal L-shaped rooms are not currently supported).
- **Stackable Exceptions**: Rugs under tables and wall-mounted shelves are treated as bounding boxes in the 2D plane unless designated separate vertical clearances.

---

## 🏆 Hackathon Credits
Built for the **Meta Global AI Developer Hackathon**. Designed with safety, mathematical determinism, and generative intelligence working in perfect harmony.

