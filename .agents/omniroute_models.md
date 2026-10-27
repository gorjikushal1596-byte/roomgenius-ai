# RoomGenius AI — OmniRoute & Model Configuration Registry

## 1. Local OmniRoute Endpoint
- **Base URL**: `http://localhost:20128/v1` (Default local OpenAI-compatible endpoint)
- **Environment Variable**: `OMNIROUTE_BASE_URL` or `OPENAI_BASE_URL`
- **API Key Env Var**: `OMNIROUTE_API_KEY` (or standard `OPENAI_API_KEY`)
- **Security Rule**: Never hardcode keys in repository files or commit `.env` containing live secrets. Always use `.env.local` or OS-level environment variables.

---

## 2. Model Assignments & OmniRoute Routing Matrix

| Agent Key | Agent Name | Assigned Model ID | OmniRoute Upstream Provider Route | Role & Purpose | Activation Context |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `agent-1` | **Architect & Planner** | `openai/gpt-oss-120b` | `groq/openai/gpt-oss-120b` | High-level system design, schema definitions, complex task breakdown, technical trade-offs | New features, architectural refactors, vague specifications |
| `agent-2` | **Main Coding Agent** *(Default)* | `qwen/qwen3.8-27b` | `groq/qwen/qwen3.8-27b` | Core feature implementation, React/TS, Python/FastAPI, geometry engine integration, bugfixes | General coding, PR features, multi-file codebases |
| `agent-3` | **Fast Task Agent** | `openai/gpt-oss-20b` | `groq/openai/gpt-oss-20b` | High-speed bounded tasks, single-component tweaks, utility scripts, unit tests, docs | Tightly scoped micro-tasks, small fixes |
| `agent-4` | **Debugging & Fallback Agent** | `gemini-3.1-flash-lite` | Direct OmniRoute Gemini Provider Route | Root cause analysis, regression diagnosis, test suite failure triage | >2 failed fix attempts by Agent 2, test flakiness, deep errors |

---

## 3. Disallowed Models & Deprecation Notice
The following models are **strictly prohibited** in this project:
- ❌ `Kimi K2 Thinking`
- ❌ `Qwen3 Coder Plus`
- ❌ `Qwen3 Coder Flash`
- ❌ `DeepSeek R1`

If any configured model becomes unreachable or rate-limited:
1. Do **not** silently substitute an alternative model.
2. Halt the step, display the exact failure code (e.g. 401, 429, 503) and model ID.
3. Request explicit user selection or fallback confirmation.

---

## 4. Antigravity IDE Connection Profile Guide

Because Antigravity IDE executes agents within its conversational session, multi-model execution with OmniRoute is accomplished via:

1. **Option A: Custom OpenAI-compatible Provider in Antigravity Settings**
   - In IDE Settings / Provider Configuration:
     - Provider Name: `OmniRoute`
     - Base URL: `http://localhost:20128/v1`
     - API Key: `${env:OMNIROUTE_API_KEY}`
     - Available Models:
       - `openai/gpt-oss-120b`
       - `qwen/qwen3.8-27b`
       - `openai/gpt-oss-20b`
       - `gemini-3.1-flash-lite`

2. **Option B: Runtime Agent Model Selection in Antigravity**
   - Click the Model Selector at the bottom of the Antigravity chat window before dispatching a phase or task:
     - For Architecture / Planning &rarr; Select `openai/gpt-oss-120b`
     - For Implementation &rarr; Select `qwen/qwen3.8-27b`
     - For Quick Edits / Tests &rarr; Select `openai/gpt-oss-20b`
     - For Difficult Debugging &rarr; Select `gemini-3.1-flash-lite`
