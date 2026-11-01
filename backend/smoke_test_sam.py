"""
backend/smoke_test_sam.py
-------------------------
Opt-in live smoke test for Meta SAM 3.1 segmentation API.
Verifies connectivity and model availability with minimal payload.

Usage:
    cd backend
    .venv\\Scripts\\python.exe smoke_test_sam.py
"""

import base64
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

API_KEY = os.getenv("META_API_KEY", "").strip()
BASE_URL = os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
MODEL = "sam-3.1"

if not API_KEY:
    print("INFO: META_API_KEY not found in backend/.env — skipping live SAM test.")
    sys.exit(0)

# Minimal 1x1 transparent PNG data URI
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
DATA_URI = f"data:image/png;base64,{TINY_PNG_B64}"

payload = {
    "model": MODEL,
    "stream": False,
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Detect bed, desk, chair, sofa in interior room",
                },
                {
                    "type": "input_image",
                    "image_url": DATA_URI,
                },
            ],
        }
    ],
}

print("=" * 60)
print("Meta SAM 3.1 Live Smoke Test")
print("=" * 60)
print(f"Endpoint : {BASE_URL}/responses")
print(f"Model    : {MODEL}")
print(f"Key      : set ({len(API_KEY)} chars, redacted)")
print("Sending minimal test payload...")

start_time = time.time()
req = urllib.request.Request(
    url=f"{BASE_URL}/responses",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "RoomGenius-AI-SmokeTest/1.0",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=15) as response:
        elapsed = time.time() - start_time
        resp_data = json.loads(response.read().decode("utf-8"))
        print(f"SUCCESS ({elapsed:.2f}s) — HTTP {response.status}")
        print("Response keys:", list(resp_data.keys()))
        output = resp_data.get("output") or resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print("Model output preview:", str(output)[:200])

except urllib.error.HTTPError as e:
    elapsed = time.time() - start_time
    err_body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP Error {e.code} ({elapsed:.2f}s): {e.reason}")
    print(f"Response: {err_body[:300]}")
    if e.code in (404, 400):
        print("Note: If sam-3.1 endpoint path differs on your tenant, verify model entitlement on developer dashboard.")

except Exception as ex:
    print(f"Network / Client error: {ex}")

