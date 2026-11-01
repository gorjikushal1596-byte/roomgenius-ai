"""
backend/verify_demo_journey.py
------------------------------
End-to-End smoke test verifying all 10 user journey steps for Day 8 demo.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("=" * 60)
print("ROOMGENIUS AI — FULL USER JOURNEY SMOKE VERIFICATION")
print("=" * 60)

# Step 1: Health & Multi-Model Status Probe
h = client.get("/health").json()
m = client.get("/ai/models-status").json()
print("[1] Health Probe:", h)
print("    Multi-Model Status:", m)
assert h["status"] == "healthy"
assert "muse_spark" in m and "sam_3_1" in m and "depth_anything_v2" in m and "muse_image" in m

# Step 2-5: Feasible Room Layout (Master Bedroom Preset: 450x550 cm)
payload_feasible = {
    "width": 450.0,
    "length": 550.0,
    "height": 270.0,
    "unit": "cm",
    "furniture": [
        {"id": "bed-1", "name": "Queen Platform Bed", "width": 160.0, "length": 200.0},
        {"id": "wardrobe-1", "name": "Double Wardrobe", "width": 120.0, "length": 60.0},
        {"id": "desk-1", "name": "Writing Desk", "width": 120.0, "length": 60.0},
        {"id": "nightstand-1", "name": "Bedside Nightstand", "width": 50.0, "length": 45.0},
    ],
    "preferences": {"style": "minimalist"},
}
res_feasible = client.post("/layout", json=payload_feasible).json()
print("[2-7] Feasible Room Layout Generation:")
print(f"    Feasible: {res_feasible['feasible']}")
print(f"    Placed Items ({len(res_feasible['placed_items'])}):")
for item in res_feasible["placed_items"]:
    print(f"      - {item['name']}: pos=({item['x']}, {item['y']}) cm, rot={item['rotation']}°, within_bounds={item['within_bounds']}")
assert res_feasible["feasible"] is True
assert len(res_feasible["placed_items"]) == 4
assert len(res_feasible["unplaced_items"]) == 0

# Step 8: Meta Muse Spark Architectural Layout Critique
ai_req = {
    "room_width_cm": 450.0,
    "room_length_cm": 550.0,
    "preferences": {"style": "minimalist"},
    "placed_items": res_feasible["placed_items"],
    "unplaced_items": res_feasible["unplaced_items"],
}
res_ai = client.post("/ai/explain", json=ai_req).json()
print("[8] Meta Muse Spark Layout Critique:")
print(f"    Status: {res_ai['status']}")
print(f"    Model Used: {res_ai['model_used']}")
print(f"    Summary: {res_ai['summary'][:75]}...")
print(f"    Design Reasoning: {res_ai['design_reasoning'][:80]}...")
print(f"    Arrangement Tips: {len(res_ai['arrangement_tips'])} tips provided")
assert res_ai["status"] in ("success", "fallback")
assert len(res_ai["summary"]) > 0

# Step 9a: Meta SAM 3.1 Object Segmentation
tiny_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
sam_req = {
    "image_base64": tiny_b64,
    "filename": "master_bedroom.png",
}
res_sam = client.post("/ai/segment-furniture", json=sam_req).json()
print("[9a] Meta SAM 3.1 Object Segmentation:")
print(f"    Status: {res_sam['status']}")
print(f"    Total Detected: {res_sam['total_detected']}")
print(f"    Requires Calibration (Golden Rule): {res_sam['requires_user_calibration']}")
assert res_sam["status"] in ("success", "fallback")
assert res_sam["requires_user_calibration"] is True

# Step 9b: Depth Anything V2 Monocular Depth & Layering
depth_req = {
    "image_base64": tiny_b64,
    "filename": "master_bedroom.png",
    "calibrated_room_length_cm": 550.0,
    "detected_boxes": [o["box"] for o in res_sam["objects_detected"]],
}
res_depth = client.post("/ai/estimate-depth", json=depth_req).json()
print("[9b] Depth Anything V2 Depth Estimation:")
print(f"    Status: {res_depth['status']}")
print(f"    Range: {res_depth['min_depth_m']}m -> {res_depth['max_depth_m']}m")
print(f"    Object Depth Profiles: {len(res_depth['object_depth_profiles'])}")
for p in res_depth["object_depth_profiles"][:2]:
    print(f"      - {p['label']}: ~{p['median_depth_m']}m ({p['relative_layer']})")
assert res_depth["status"] in ("success", "fallback")
assert res_depth["max_depth_m"] == 5.5  # 550 cm / 100

# Step 9c: Meta Muse Image Photorealistic Visual Redesign
preview_req = {
    "room_width_cm": 450.0,
    "room_length_cm": 550.0,
    "style": "minimalist",
    "placed_items": res_feasible["placed_items"],
    "custom_prompt_additions": "warm white oak textures, large window morning light",
}
res_preview = client.post("/ai/generate-preview", json=preview_req).json()
print("[9c] Meta Muse Image Redesign Preview:")
print(f"    Status: {res_preview['status']}")
print(f"    Format: {res_preview['format']}")
print(f"    Model Used: {res_preview['model_used']}")
print(f"    Truthful Disclaimer: {res_preview['disclaimer'][:75]}...")
assert res_preview["status"] in ("success", "fallback")
assert "Aesthetic concept preview only" in res_preview["disclaimer"]

# Step 10: Infeasible Failure Case (Crowded Studio: 220x220 cm with 4 oversized items)
payload_infeasible = {
    "width": 220.0,
    "length": 220.0,
    "furniture": [
        {"id": "king-bed", "name": "King Bed", "width": 190.0, "length": 200.0},
        {"id": "sofa", "name": "3-Seater Sofa", "width": 200.0, "length": 90.0},
        {"id": "dining", "name": "4-Person Dining Table", "width": 120.0, "length": 80.0},
        {"id": "wardrobe", "name": "Wardrobe Unit", "width": 140.0, "length": 60.0},
    ],
}
res_infeasible = client.post("/layout", json=payload_infeasible).json()
print("[10] Infeasible / Overcrowded Case Validation:")
print(f"    Feasible: {res_infeasible['feasible']} (Correctly Rejected)")
print(f"    Placed: {len(res_infeasible['placed_items'])} items")
print(f"    Unplaced / Rejected ({len(res_infeasible['unplaced_items'])} items):")
for item in res_infeasible["unplaced_items"]:
    print(f"      - {item['name']}: {item['rejection_reason']}")
assert res_infeasible["feasible"] is False
assert len(res_infeasible["unplaced_items"]) >= 2

print("\n" + "=" * 60)
print("ALL 10 USER JOURNEY STEPS VERIFIED 100% SUCCESSFUL!")
print("=" * 60)
