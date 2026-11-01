"""
backend/smoke_test_muse_image.py
--------------------------------
Opt-in live smoke test for Meta Muse Image generation API.
Verifies connectivity and image generation with minimal credit footprint.

Usage:
    cd backend
    .venv\\Scripts\\python.exe smoke_test_muse_image.py
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

API_KEY = os.getenv("META_API_KEY", "").strip()
BASE_URL = os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
MODEL = "meta/muse-image"

if not API_KEY:
    print("INFO: META_API_KEY not found in backend/.env — skipping live Muse Image test.")
    sys.exit(0)

payload = {
    "model": MODEL,
    "prompt": "Minimalist Scandinavian bedroom with oak platform bed, soft morning light, 8k architectural photo",
    "n": 1,
    "size": "1024x1024",
    "response_format": "b64_json",
}

print("=" * 60)
print("Meta Muse Image Live Smoke Test")
print("=" * 60)
print(f"Endpoint : {BASE_URL}/images/generations")
print(f"Model    : {MODEL}")
print(f"Key      : set ({len(API_KEY)} chars, redacted)")
print("Sending test generation request...")

start_time = time.time()
req = urllib.request.Request(
    url=f"{BASE_URL}/images/generations",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "RoomGenius-AI-SmokeTest/1.0",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=25) as response:
        elapsed = time.time() - start_time
        resp_data = json.loads(response.read().decode("utf-8"))
        print(f"SUCCESS ({elapsed:.2f}s) — HTTP {response.status}")
        data_arr = resp_data.get("data", [])
        if data_arr and isinstance(data_arr[0], dict):
            item = data_arr[0]
            if "b64_json" in item:
                print(f"Received b64_json image data ({len(item['b64_json'])} chars)")
            elif "url" in item:
                print(f"Received image URL: {item['url'][:80]}...")
        else:
            print("Response:", str(resp_data)[:200])

except urllib.error.HTTPError as e:
    elapsed = time.time() - start_time
    err_body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP Error {e.code} ({elapsed:.2f}s): {e.reason}")
    print(f"Response: {err_body[:300]}")
    if e.code in (404, 400):
        print("Note: If meta/muse-image model identifier differs on your tenant, verify model entitlement on developer dashboard.")

except Exception as ex:
    print(f"Network / Client error: {ex}")

