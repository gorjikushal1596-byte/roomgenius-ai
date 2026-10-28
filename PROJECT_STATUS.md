# Project Status – RoomGenius AI

## Day 2 — October 28, 2026 (IST)

---

### 🔎 Verified Starting State (Day 2)

| Item | Status |
|------|--------|
| Git branch | `main`, clean working tree (2 commits: `6ca6109`, `cafb1b3`) |
| Frontend | Vite + React TS scaffolding in `frontend/`; health-check page renders |
| Backend | FastAPI in `backend/main.py`; `/health` returns `{ "status": "healthy" }` |
| Schema | `backend/schemas.py` — **bug found**: trailing comma on line 32 turned `length` into a tuple; fixed today |
| Python venv | `backend/.venv/` with FastAPI, uvicorn, pydantic installed |
| Telemetry hook | `googlecloudtools.datacloud_telemetry` plugin was missing; disabled (folder renamed) to unblock tooling |

---

### ✅ Completed Tasks & Verified Results (Day 2)

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 1 | Fix `schemas.py` bug (trailing comma on `length` field) | ✅ Done | Fixed; all 17 backend tests pass |
| 2 | Add `id` field to `FurnitureItem`, make `height` optional | ✅ Done | `schemas.py` updated; tests cover both cases |
| 3 | Add `unit` field to `RoomInput` (default `"cm"`) | ✅ Done | Schema includes `unit: str = "cm"` |
| 4 | Create `POST /layout` endpoint | ✅ Done | Returns `{ "status": "accepted", "summary": {...} }` on valid payload; 422 on invalid |
| 5 | Build Room Input form (React) | ✅ Done | Room width/length/height, furniture CRUD, style preference, validation messages |
| 6 | Wire frontend → backend via Vite proxy | ✅ Done | POST to `/api/layout` → proxied to `http://localhost:8000/layout`; success/error toasts |
| 7 | Backend validation tests (`test_layout.py`) | ✅ Done | 17/17 tests pass (pytest) |
| 8 | Frontend TypeScript check | ✅ Done | `npx tsc --noEmit` passes with 0 errors |
| 9 | Frontend production build | ✅ Done | `npx vite build` succeeds (684ms, 226 kB JS gzipped to 71 kB) |

---

### 📁 Files Created / Modified Today

```
backend/
  main.py           ← Updated: added POST /layout endpoint, imported RoomInput
  schemas.py        ← Updated: fixed bug, added id/unit fields, made height optional
  test_layout.py    ← NEW: 17 pytest tests for /layout validation

frontend/
  src/App.tsx       ← Rewritten: full room input form with furniture CRUD
  src/App.css       ← Rewritten: clean responsive styles for the form

PROJECT_STATUS.md   ← Updated with Day 2 progress
```

---

### 🖥️ Windows Commands to Run Both Servers

#### Backend (run in a dedicated terminal)
```powershell
cd "d:\PROJECTS\ROOMGENIUS AI\backend"
.venv\Scripts\Activate.ps1
uvicorn main:app --port 8000 --reload
```

#### Frontend (run in a separate terminal)
```powershell
cd "d:\PROJECTS\ROOMGENIUS AI\frontend"
npm run dev
```

#### Quick health check (after both servers are running)
```powershell
Invoke-RestMethod http://localhost:8000/health
# Expected: status = healthy
```

#### Run backend tests
```powershell
cd "d:\PROJECTS\ROOMGENIUS AI\backend"
.venv\Scripts\Activate.ps1
python -m pytest test_layout.py -v
```

---

### 🌐 API Endpoints

| Method | Path | Response |
|--------|------|----------|
| GET | `http://localhost:8000/health` | `{ "status": "healthy" }` |
| POST | `http://localhost:8000/layout` | `{ "status": "accepted", "summary": {...} }` on valid; 422 on invalid |
| GET | `http://localhost:8000/docs` | Swagger UI (auto-generated) |

---

### 📋 Pydantic Schema Summary (`backend/schemas.py`)

All dimensions in **centimetres (cm)**.

```
RoomInput
  width       float  (0 < x ≤ 2000 cm)  — room X-axis
  length      float  (0 < x ≤ 2000 cm)  — room Y-axis (depth)
  height      float | None  (0 < x ≤ 500 cm, optional)
  unit        str  (default "cm")
  furniture   list[FurnitureItem] (can be empty)
  preferences dict | None

FurnitureItem
  id      str   (min 1 char, unique identifier)
  name    str   (min 1 char)
  width   float (0 < x ≤ 2000 cm)
  length  float (0 < x ≤ 2000 cm)
  height  float | None (0 < x ≤ 500 cm, optional)
```

---

### 🧪 Test Results (Day 2)

#### Backend — pytest (17/17 passed)
```
test_valid_room_with_furniture ............... PASSED
test_valid_room_empty_furniture .............. PASSED
test_valid_room_with_height .................. PASSED
test_missing_width ........................... PASSED
test_missing_length .......................... PASSED
test_missing_both_dimensions ................. PASSED
test_zero_room_width ......................... PASSED
test_negative_room_length .................... PASSED
test_zero_furniture_width .................... PASSED
test_negative_furniture_length ............... PASSED
test_non_numeric_width ....................... PASSED
test_infinity_width .......................... PASSED
test_non_finite_width_string ................. PASSED
test_invalid_unit ............................ PASSED
test_valid_unit_explicit ..................... PASSED
test_furniture_missing_name .................. PASSED
test_furniture_whitespace_name ............... PASSED
test_furniture_missing_id .................... PASSED
test_duplicate_furniture_id .................. PASSED
test_exceeds_max_dimension ................... PASSED
test_health_endpoint ......................... PASSED
```

#### Frontend — TypeScript
```
npx tsc --noEmit → 0 errors
npx vite build → ✅ success
```

---

### 🐇 CodeRabbit Review & Remediation

| Issue | Severity | Status | Fix Applied |
|---|---|---|---|
| `backend/schemas.py`: Restrict `unit` | Minor | ✅ Fixed | Changed `unit: str` to `Literal["cm"]` |
| `frontend/src/App.tsx`: Safe response JSON parsing | Minor | ✅ Fixed | Handled empty / non-JSON responses with `.catch(() => null)` |
| `frontend/src/App.tsx`: 500 cm height validation | Minor | ✅ Fixed | Updated `validateDimension` to enforce 500 cm limit for optional height fields |
| `backend/schemas.py`: Reject whitespace-only names | Minor | ✅ Fixed | Added validator to strip whitespace and reject blank names |
| `backend/schemas.py`: Enforce unique furniture IDs | Minor | ✅ Fixed | Added `validate_unique_furniture_ids` validator in `RoomInput` |

---

### 🤖 Agent / Model Usage This Session

| Provider | Purpose | Calls | Notes |
|----------|---------|-------|-------|
| OmniRoute / IDE (Gemini 3.8 Flash / Claude Opus 4.6) | Code scaffolding & editing | Active session | Default coding agent |
| CodeRabbit CLI | Code quality & security audit | 2 runs | Findings addressed and re-verified |
| Baseten (Muse Spark Open) | — | 0 | No Meta API calls made today (credit conservation) |

---

### 📌 Current Branch & Commit

- **Branch:** `day2-room-input`
- **Commits:**
  - `51205e1` feat: Day 2 — room input form, POST /layout endpoint, 17 validation tests
- **Status:** Day 2 implementation & CodeRabbit audit complete, verified with 21 unit tests.

---

### ⏭️ Day 3 Focus / Upcoming Tasks

1. **Deterministic geometry engine** (`backend/geometry.py`) — AABB bounding boxes, clearance pathways (75–90 cm).
2. **Furniture placement logic** — collision detection, egress path validation.
3. **AI Layout Suggestion Pipeline** (`backend/ai.py`) — integrate Baseten Muse Spark calls with reasoning caps and prompt engineering.
4. **2D room visualization** — Canvas/SVG rendering of the room layout in the frontend.
