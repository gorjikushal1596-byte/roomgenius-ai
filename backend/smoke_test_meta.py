"""
backend/smoke_test_meta.py
--------------------------
One-shot live smoke test for the official Meta Model API (Muse Spark).
Used to verify connectivity and authentication with minimal credit consumption.

Usage:
    cd backend
    .venv\\Scripts\\python.exe smoke_test_meta.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")
except ImportError:
    pass

API_KEY = os.getenv("META_API_KEY")
BASE_URL = os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
MODEL = os.getenv("META_MODEL", "muse-spark-1.3")

if not API_KEY:
    sys.exit("FAIL: META_API_KEY not found in backend/.env")

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": "In one concise sentence, confirm you are Meta Muse Spark ready for RoomGenius AI architectural review.",
        }
    ],
    "max_tokens": 250,
    "temperature": 0.1,
    "stream": False,
}

print(f"Calling {BASE_URL}/chat/completions")
print(f"Model  : {MODEL}")
print(f"Key    : set ({len(API_KEY)} chars)")

req = urllib.request.Request(
    url=f"{BASE_URL}/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "RoomGenius-AI-SmokeTest/1.0",
    },
    method="POST",
)

start_time = time.time()
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        elapsed = time.time() - start_time
        body = resp.read().decode("utf-8")
        data = json.loads(body)
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = (msg.get("content") or "").strip()
        reasoning = (msg.get("reasoning_content") or "").strip()
        usage = data.get("usage", {})

        print("\n✅ PASSED: Meta Model API connection verified successfully!")
        print(f"  Response ({elapsed:.2f}s): {content}")
        if reasoning:
            print(f"  Reasoning trace : {reasoning[:120]}...")
        print(f"  Tokens: {usage.get('prompt_tokens', '?')} in / {usage.get('completion_tokens', '?')} out (total: {usage.get('total_tokens', '?')})")

except urllib.error.HTTPError as err:
    body = ""
    try:
        body = err.read().decode("utf-8")
    except Exception:
        pass
    print(f"\n❌ HTTP {err.code} Error: {body[:500]}")
    sys.exit(1)
except Exception as exc:
    print(f"\n❌ Request failed: {exc}")
    sys.exit(1)
