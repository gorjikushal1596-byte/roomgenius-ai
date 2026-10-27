"""
backend/smoke_test.py
---------------------
ONE-SHOT Baseten Muse Spark smoke test.
Muse Spark is a reasoning model — it populates `reasoning_content` first,
then sets `content` once reasoning is complete.
max_tokens must be high enough for the model to finish reasoning.

Usage:
    .venv\Scripts\python smoke_test.py
"""

import os, sys, json
import urllib.request, urllib.error

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")
except ImportError:
    pass

API_KEY = os.getenv("BASETEN_API_KEY")
BASE_URL = os.getenv("BASETEN_BASE_URL", "https://inference.baseten.co/v1")
MODEL    = os.getenv("BASETEN_MODEL", "meta-models/muse-spark-open")

if not API_KEY:
    sys.exit("FAIL: BASETEN_API_KEY not found in backend/.env")

# reasoning_effort controls depth; reasoning.max_tokens caps the thinking budget.
# max_tokens must be > reasoning.max_tokens to leave room for the final answer.
PAYLOAD = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "In one sentence, confirm you are ready to help arrange room furniture."}
    ],
    "max_tokens": 400,          # total budget: reasoning + final answer
    "temperature": 0.0,
    "stream": False,
    "reasoning_effort": "low",  # minimal thinking for a simple confirmation
    "reasoning": {"max_tokens": 100},  # cap thinking tokens
}

req = urllib.request.Request(
    url=f"{BASE_URL}/chat/completions",
    data=json.dumps(PAYLOAD).encode("utf-8"),
    method="POST",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    },
)

print(f"Calling {BASE_URL}")
print(f"Model  : {MODEL}")
print("Tokens : max_tokens=512 (reasoning model needs space)\n")

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        choice  = data["choices"][0]
        message = choice.get("message", {})
        content  = (message.get("content") or "").strip()
        reasoning = (message.get("reasoning_content") or "").strip()
        finish   = choice.get("finish_reason")
        usage    = data.get("usage", {})

        if finish != "stop":
            print(f"WARNING: finish_reason={finish} (model may have been cut off)")

        print("PASSED: Smoke test successful\n")
        if content:
            print(f"  Final answer   : {content}")
        if reasoning:
            preview = reasoning[:120] + ("..." if len(reasoning) > 120 else "")
            print(f"  Reasoning peek : {preview}")
        print(f"  Tokens used    : {usage.get('prompt_tokens','?')} in / "
              f"{usage.get('completion_tokens','?')} out  "
              f"(total={usage.get('total_tokens','?')})")

except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print(f"FAIL HTTP {e.code}: {body[:800]}")
    sys.exit(1)
except Exception as exc:
    print(f"FAIL: {exc}")
    sys.exit(1)
