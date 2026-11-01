# RoomGenius AI — Complete Hackathon Demo Walkthrough Guide
> **Presenter's Playbook: Step-by-Step Demonstration, Script, and Rehearsal Manual**  
> *Prepared for the Meta Global AI Developer Hackathon*

---

## 1. Application Overview

RoomGenius AI is a spatial computing and room layout design platform built around a strict **Dual-Engine Architecture**:
1. **The Deterministic Physics Engine (Python)**: The absolute physical ground truth. Computes Axis-Aligned Bounding Box (AABB) collision boundaries, candidate-anchor corner packing, 0°/90° rotations, and egress transit corridors (minimum 75–90 cm). It **never** claims an invalid layout is feasible.
2. **Multimodal Meta AI Perception & Reasoning**:
   * **Meta Muse Spark (`muse-spark-1.3`)**: Natural-language architectural critique and placement rationale grounded in exact physical coordinates.
   * **Meta SAM 3.1 (`sam-3.1`)**: Zero-shot furniture object segmentation and 2D bounding boxes from uploaded room photos.
   * **Depth Anything V2 (`vits` Metric Indoor)**: Optical $Z$-axis depth estimation and scene structure heatmap.
   * **Meta Muse Image (`muse-image-1.0`)**: Photorealistic interior redesign concept generation with mandatory truthfulness disclaimers.

---

## 2. Complete Feature-Button Reference

| UI Section | Button / Control | When to Click | What It Actually Does | Expected Output |
| :--- | :--- | :--- | :--- | :--- |
| **Header Status** | `Check Backend Health` | Start of demo (pre-flight) | Sends `GET /health` to FastAPI backend. | Changes button to green badge: `"Healthy"`. |
| **Quick Presets** | `🛏️ Master Bedroom` | Live Walkthrough (Step 2) | Loads 450 × 550 cm room + 4 furniture pieces (Bed, Wardrobe, Desk, Nightstand) with Minimalist style. | Form auto-populates instantly with validated values. |
| **Quick Presets** | `💻 Compact Home Office` | Optional secondary demo | Loads 320 × 380 cm room + 4 office pieces with Modern style. | Form auto-populates with office workstation setup. |
| **Quick Presets** | `⚠️ Crowded Studio` | Infeasible Failure Demo (Step 6) | Loads 220 × 220 cm room with 4 oversized items (King Bed, Sofa, Dining Table, Wardrobe). | Form auto-populates; used to prove collision rejection. |
| **Quick Presets** | `🧹 Reset Form` | Between demo runs | Clears all room dimensions, resets furniture to 1 blank row, and wipes layout results. | Clean, blank input screen. |
| **Vision Scanner** | `🔍 Scan Room Photo` | Vision perception segment | Toggles the Meta SAM 3.1 & Depth Anything V2 photo upload drawer. | Expands the photo upload and calibration area. |
| **Vision Scanner** | `📁 Choose Room Photo` | When scanner is open | Opens native file picker; accepts JPEG, PNG, or WebP up to 5 MB. | Reads image via `FileReader`, calls `POST /ai/segment-furniture` and `POST /ai/estimate-depth`. |
| **Vision Scanner** | `📷 Photo` vs `🗺️ Depth Heatmap` | After photo is scanned | Switches image frame between standard photo and Depth Anything V2 Inferno colormap. | Toggles visual depth gradient with SVG bounding boxes overlaying both. |
| **Staging Drawer** | Item Checkboxes | In calibration drawer | Selects/deselects detected objects to include in the room inventory. | Checks box and highlights item card. |
| **Staging Drawer** | `📥 Add Calibrated Items` | After reviewing dimensions | Appends selected items with user-confirmed $W \times L$ (cm) into the main furniture form. | Closes scanner; items appear in the form. |
| **Furniture Form** | `+ Add Furniture Item` | Manual entry demo | Adds a new blank furniture card (`Name`, `Width`, `Length`, `Height`). | New numbered furniture card appears at the bottom. |
| **Furniture Form** | `✕ Remove` | On any furniture card | Deletes that specific furniture item from inventory. | Item card is immediately removed. |
| **Form Submit** | `✨ Generate Optimized Layout` | After inputs are ready | Validates inputs, sends `POST /layout` to deterministic Python engine. | Displays side-by-side Before/After layout visualizer. |
| **Layout Table** | `Select` button / Table Row | Inside Placed Items table | Cross-highlights the selected furniture rectangle in both the table and the 2D SVG floorplan. | Highlights corresponding item in SVG with active outline. |
| **AI Critique** | `✨ Explain Layout with Meta AI` | In AI Design Explanation card | Sends deterministic coordinates to `POST /ai/explain` (Meta Muse Spark). | Renders architectural summary, rationale, installation tips, and trade-offs. |
| **AI Critique** | `▶ Show Details` | Inside AI Critique card | Toggles internal model reasoning trace (if returned by Muse Spark). | Expands code block showing model thinking. |
| **AI Preview** | `🎨 Generate Visual Concept` | In Meta Muse Image card | Sends layout context + style to `POST /ai/generate-preview` (Meta Muse Image). | Displays generated interior redesign concept image + prompt inspector. |
| **Results Action** | `↑ Modify Room Inputs` | At bottom of results | Smoothly scrolls viewport back up to the room input form. | Screen scrolls up to form. |

---

## 3. Step-by-Step Click Walkthrough

### STEP 1: Pre-Flight Check & Application Launch
* **Page to open:** `http://localhost:5173`
* **Button to click:** `Check Backend Health` (top card)
* **Input to enter:** None
* **Expected output:** Button text switches from `"Checking…"` to a green `"Healthy"` indicator badge.
* **What I should say:**  
  > *"Before we begin, our frontend is connected to our FastAPI backend. A single click verifies the API gateway is fully operational."*

---

### STEP 2: Instant Data Ingestion (Quick Presets)
* **Page to open:** Main screen (top section)
* **Button to click:** `🛏️ Master Bedroom` preset card
* **Input to enter:** None (loads preset automatically)
* **Expected output:** Room Width fills with `450`, Length fills with `550`, Height with `270`, Style selects `Minimalist`. Four furniture cards populate:
  1. Queen Platform Bed ($160 \times 200\text{ cm}$)
  2. Double Wardrobe ($120 \times 60\text{ cm}$)
  3. Writing Desk ($120 \times 60\text{ cm}$)
  4. Bedside Nightstand ($50 \times 45\text{ cm}$)
* **What I should say:**  
  > *"To ensure a smooth, reproducible demonstration, RoomGenius AI includes curated real-world room presets. We'll select the Master Bedroom: 4.5 meters by 5.5 meters with four standard furniture pieces."*

---

### STEP 3: Multimodal Vision Perception (Meta SAM 3.1 & Depth Anything V2)
* **Page to open:** Main screen (above furniture list)
* **Button to click:** `🔍 Scan Room Photo`
* **Input to enter:** Click `📁 Choose Room Photo`, pick any room image (or use sample from `backend/` or your computer).
* **Button to click:** Click `🗺️ Depth Heatmap` toggle above the image.
* **Expected output:**  
  1. Photo renders with crisp SVG bounding boxes around detected furniture objects.
  2. Clicking `🗺️ Depth Heatmap` switches the view to Depth Anything V2's Inferno colormap, displaying depth gradients (yellow = near foreground $\rightarrow$ dark = far background).
  3. Staging drawer displays $Z$-axis depth badges (e.g. `~3.2m · midground`).
  4. Golden Rule banner confirms: *"User Confirmation Required — Monocular depth estimates provide spatial ordering and must not replace physical measurements."*
* **Button to click:** Click `✕ Close Scanner` (or click `📥 Add Calibrated Items`).
* **What I should say:**  
  > *"If a user has a photo of their room, our vision pipeline activates. Meta SAM 3.1 segments furniture boundaries, while Depth Anything V2 estimates Z-axis spatial depth layers. But notice our Golden Rule: optical perception never assumes physical metric dimensions without human confirmation in our staging drawer."*

---

### STEP 4: Deterministic Layout Generation (The Physical Truth)
* **Page to open:** Main form
* **Button to click:** `✨ Generate Optimized Layout` (blue button at bottom of form)
* **Input to enter:** None
* **Expected output:**  
  1. Green banner: `✅ Feasible Layout Generated — All 4 items successfully placed within room boundaries.`
  2. **Metrics Bar**: Room Area: `24.8 m²` · Footprint: `4.5 m²` · Utilization: `18.1%` · Placement Rate: `100%`.
  3. **Truthful Comparison**:
     * **Before**: Submitted inventory snapshot awaiting placement.
     * **After**: Interactive 2D vector SVG floorplan. Every item rendered at its exact centimetre coordinate with zero overlap, clear wall anchoring, and dimension callouts.
* **Button to click:** Click on the `Queen Platform Bed` row in the table below the floorplan.
* **Expected output:** Bed is highlighted in blue both in the table and directly inside the SVG floorplan.
* **What I should say:**  
  > *"Now we click Generate. In just 6 milliseconds, our deterministic Python geometry engine computes candidate anchors and AABB collisions. Look at the After floorplan: every piece is placed with exact coordinates and certified zero collision. When I select an item in the breakdown table, it cross-highlights on the floorplan with its exact metric dimensions."*

---

### STEP 5: Meta Muse Spark Architectural Commentary
* **Page to open:** Results section (scroll down slightly)
* **Button to click:** `✨ Explain Layout with Meta AI`
* **Input to enter:** None
* **Expected output:** Spinner shows for ~1-2 seconds, then populates:
  * **Overview**: Natural language summary of the minimalist arrangement.
  * **Architectural Rationale**: Detailed explanation of wall-anchoring and transit clearances grounded in the exact coordinates $(0, 0)$, $(160, 0)$, $(280, 0)$, and $(400, 0)$.
  * **Installation & Transit Tips**: Step-by-step physical installation guidance.
  * **Spatial Trade-offs**: Discussion of door swings and walkway margins.
* **What I should say:**  
  > *"Generative AI shouldn't calculate physics—it should explain architectural reasoning. Meta Muse Spark analyzes the deterministic coordinates and provides human-readable architectural critiques, transit corridor tips, and spatial trade-offs."*

---

### STEP 6: Meta Muse Image Visual Concept Preview
* **Page to open:** Results section (directly below Muse Spark critique)
* **Button to click:** `🎨 Generate Visual Concept`
* **Input to enter:** (Optional) Type in Design Accents: `warm white oak, large window morning light`
* **Expected output:**  
  1. Displays photorealistic concept preview rendered from the layout geometry and style.
  2. Model badge displays `muse-image-1.0`.
  3. Click `View Architectural Prompt` to show the grounded text prompt constructed from coordinates.
  4. Mandatory disclaimer is prominently displayed:  
     > *"⚠️ Aesthetic concept preview only. Refer to 2D Floorplan for precise physical dimensions and clearances."*
* **What I should say:**  
  > *"For visual inspiration, Meta Muse Image generates an interior redesign concept preview grounded in our layout geometry. And in keeping with hackathon integrity, our prompt inspector shows exactly what was generated, backed by a prominent disclaimer that visual pixels are aesthetic concepts, while our 2D floorplan remains the physical authority."*

---

### STEP 7: Demonstrating a Failure / Infeasible Case
* **Page to open:** Scroll to top (or click `↑ Modify Room Inputs`)
* **Button to click:** `⚡ Quick Demo Presets` $\rightarrow$ `⚠️ Crowded Studio (Infeasible Test)`
* **Input to enter:** None (loads $220 \times 220\text{ cm}$ room with 4 oversized items)
* **Button to click:** `✨ Generate Optimized Layout`
* **Expected output:**  
  1. Warning banner: `⚠️ Infeasible Layout (Partial Placement) — 1 of 4 items placed. 3 items could not fit safely.`
  2. Floorplan shows only the King Bed placed.
  3. An orange **Unplaced Furniture** card appears below the floorplan listing:
     * *3-Seater Sofa*: `No collision-free candidate position found within room boundaries.`
     * *4-Person Dining Table*: `No collision-free candidate position found within room boundaries.`
     * *Wardrobe Unit*: `No collision-free candidate position found within room boundaries.`
* **What I should say:**  
  > *"Now, let's see what happens when a user attempts the impossible. We load a crowded studio: a 2.2-meter micro-room with a King Bed, large Sofa, Dining Table, and Wardrobe. Generic AI tools would hallucinate floating furniture to look good. RoomGenius AI refuses: our deterministic engine places only what safely fits, flags the layout as infeasible, and tells the user exactly which pieces caused boundary collisions."*

---

## 4. Sample Input Data Matrix

### Primary Demo: Master Bedroom (Feasible)
* **Room Width:** `450` cm ($4.5\text{ m}$)
* **Room Length:** `550` cm ($5.5\text{ m}$)
* **Room Height:** `270` cm ($2.7\text{ m}$)
* **Aesthetic Style:** `minimalist`
* **Furniture Inventory:**
  1. `Queen Platform Bed` — Width: `160` cm, Length: `200` cm, Height: `100` cm
  2. `Double Wardrobe` — Width: `120` cm, Length: `60` cm, Height: `210` cm
  3. `Writing Desk` — Width: `120` cm, Length: `60` cm, Height: `75` cm
  4. `Bedside Nightstand` — Width: `50` cm, Length: `45` cm, Height: `55` cm

### Secondary Demo: Crowded Studio (Infeasible Failure Case)
* **Room Width:** `220` cm ($2.2\text{ m}$)
* **Room Length:** `220` cm ($2.2\text{ m}$)
* **Furniture Inventory:**
  1. `King Bed` — Width: `190` cm, Length: `200` cm
  2. `3-Seater Sofa` — Width: `200` cm, Length: `90` cm
  3. `4-Person Dining Table` — Width: `120` cm, Length: `80` cm
  4. `Wardrobe Unit` — Width: `140` cm, Length: `60` cm

---

## 5. Precise 3-Minute Video Demo Recording Script

*Total duration target: 2 minutes 50 seconds (leaves 10-second buffer under the 3-minute limit).*

```
[0:00–0:20] ── PROBLEM & HOOK
Screen: Webcam on speaker or title slide, switching to RoomGenius AI browser tab.
Action: Cursor hovers over header title.
Spoken: "Interior design software is broken: traditional CAD tools are intimidating and complex, while modern generative AI tools hallucinate impossible dimensions, floating furniture, and blocked walkways. What if you could combine strict mathematical truth with multimodal Meta AI reasoning? Meet RoomGenius AI."

[0:20–0:45] ── THE DUAL-ENGINE ARCHITECTURE
Screen: Quick pan over System Architecture diagram or smooth scroll past presets.
Action: Highlight "Dual-Engine Architecture".
Spoken: "RoomGenius AI introduces the Dual-Engine architecture. Our deterministic Python geometry engine strictly calculates collision boundaries, egress clearances, and physical metric positions. In parallel, Meta AI interprets preferences, segments room photos, explains design reasoning, and renders visual concepts."

[0:45–1:15] ── VISION PERCEPTION (SAM 3.1 & DEPTH ANYTHING V2)
Screen: Click "🔍 Scan Room Photo". Upload sample photo. Toggle "🗺️ Depth Heatmap".
Action: Mouse toggles between Photo and Depth Heatmap view; points to Z-depth badges.
Spoken: "Users can start by uploading a room photo. Meta SAM 3.1 segments furniture boundaries, while Depth Anything V2 estimates Z-axis depth layers. Following our Golden Rule, optical perception never assumes physical metric dimensions: users confirm exact centimetre measurements in our staging drawer."

[1:15–1:45] ── FEASIBLE LAYOUT & DETERMINISTIC ACCURACY
Screen: Click preset "🛏️ Master Bedroom", click "✨ Generate Optimized Layout".
Action: Scroll down to side-by-side Before/After comparison. Click on "Queen Platform Bed" in table.
Spoken: "With one click, our deterministic engine computes candidate anchors and AABB collisions in just 6 milliseconds. Look at the After view: every single piece is placed with exact centimetre coordinates, zero overlaps, and guaranteed clearances. Selecting any item cross-highlights its physical footprint."

[1:45–2:15] ── INFEASIBLE COLLISION REJECTION
Screen: Scroll up, click preset "⚠️ Crowded Studio", click "✨ Generate Optimized Layout".
Action: Highlight the red/orange failure banner and unplaced items list.
Spoken: "Now let's test the limits: a crowded studio with oversized furniture. Rather than hallucinating a false success, the deterministic engine strictly flags the layout as infeasible and explains exactly why the sofa, table, and wardrobe could not fit. We never claim a layout is valid unless the math proves it."

[2:15–2:40] ── META MUSE SPARK & MUSE IMAGE
Screen: Scroll to "Meta Muse Spark Critique", click "✨ Explain Layout", then click "🎨 Generate Visual Concept".
Action: Highlight the architectural critique paragraphs and the generated visual preview card.
Spoken: "Down below, Meta Muse Spark delivers an architectural critique grounded in the exact layout coordinates. And Meta Muse Image synthesizes an aesthetic redesign preview with clear truthfulness disclosures."

[2:40–3:00] ── IMPACT & CLOSING
Screen: Closing slide with GitHub repository link, QR code, and tech stack badges.
Action: Camera returns to speaker or stays on closing slide.
Spoken: "RoomGenius AI bridges the gap between spatial computing, physical reality, and generative AI. Built for the Meta Global AI Developer Hackathon. Thank you!"
```

---

## 6. Demo Startup & Rehearsal Checklist

### Terminal 1: Backend Startup
```powershell
cd "d:\PROJECTS\ROOMGENIUS AI\backend"
.venv\Scripts\Activate.ps1
uvicorn main:app --port 8000 --reload
```
*Verify output:* `Uvicorn running on http://127.0.0.1:8000`

### Terminal 2: Frontend Startup
```powershell
cd "d:\PROJECTS\ROOMGENIUS AI\frontend"
npm run dev
```
*Verify output:* `Local: http://localhost:5173/`

### Pre-Flight Verification Checklist
- [ ] Browser opened at `http://localhost:5173` (100% zoom, 1920×1080 resolution).
- [ ] Clicked `Check Backend Health` $\rightarrow$ verified green `"Healthy"`.
- [ ] Sample room photo saved to Desktop for quick upload.
- [ ] Tested clicking `🛏️ Master Bedroom` preset $\rightarrow$ verified layout generates.
- [ ] Tested clicking `⚠️ Crowded Studio` preset $\rightarrow$ verified rejection banner appears.
- [ ] Microphone tested and audio levels calibrated (no background noise).
- [ ] Recording software configured (OBS Studio / Loom / Camtasia) for 1080p 60fps recording.
- [ ] Timer running on phone/watch set to 3 minutes.

### Common Demo Mishaps & Instant Fixes
* **Accidental Form Clearing**: Just click `🛏️ Master Bedroom` preset to restore all values in 1 click.
* **Network Latency / Slow API Response**: The UI has non-blocking background semaphores and instant deterministic fallbacks. If remote Meta API times out, the fallback label is clearly attributed and the demo continues smoothly without crashing.
* **Zoom / Layout Distortion**: Press `Ctrl + 0` in Chrome/Edge to reset zoom to 100%.

---

## 7. Known Limitations (Truthful Disclosure for Judges)
1. **Top-Down 2D Packing**: Placement currently optimizes candidate corners along walls using 0° and 90° rotations; non-orthogonal angles (e.g. 45° diagonal placements) are planned for future releases.
2. **Monocular Optical Depth**: Depth Anything V2 estimates optical $Z$-axis depth from single photos, which provides scene layering cues but requires human-in-the-loop dimension confirmation for physical room boundaries.
3. **Rectangular Room Boundaries**: The current geometry engine standardizes on rectangular room boundaries; L-shaped or polygonal floorplans are mapped in future development.
