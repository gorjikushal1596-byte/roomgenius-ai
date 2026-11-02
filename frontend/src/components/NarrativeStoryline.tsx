import { BeforeAfterSlider } from './BeforeAfterSlider'

interface NarrativeStorylineProps {
  onLaunchStudio: () => void
}

export function NarrativeStoryline({ onLaunchStudio }: NarrativeStorylineProps) {
  return (
    <section id="narrative" className="rg-narrative-section">
      <div className="rg-narrative-header">
        <span className="rg-section-kicker">Scroll-Controlled Narrative</span>
        <h2 className="rg-section-title">The Complete Spatial Design Journey</h2>
        <p className="rg-section-subtitle">
          Follow how RoomGenius AI seamlessly connects room photo ingestion, computer vision segmentation,
          monocular metric depth, deterministic collision validation, and generative Meta AI.
        </p>
      </div>

      <div className="rg-story-cards">
        {/* SECTION 2 — ROOM UPLOAD (cluttered-room.jpg) */}
        <article id="narrative-section-2" className="rg-story-card rg-story-card--left">
          <div className="rg-story-media">
            <img
              src="/roomgenius-assets/cluttered-room.jpg"
              alt="Real World Room Photo Ingestion"
              className="rg-story-img"
              loading="lazy"
            />
            <span className="rg-story-badge">Stage 02 · Room Upload</span>
          </div>
          <div className="rg-story-content">
            <span className="rg-step-num">02</span>
            <h3 className="rg-story-title">Room Photograph &amp; Spatial Ingestion</h3>
            <p className="rg-story-desc">
              Every design journey begins with real-world spatial constraints. Upload a single photo of your
              bedroom, living area, or studio along with verified metric room boundaries (width and length in cm).
            </p>
            <div className="rg-benefit-chip">
              <span className="rg-benefit-icon">📷</span>
              <div>
                <strong>Single Photo Ingestion</strong>
                <span>Supports everyday mobile room photos up to 5 MB with zero specialized lidar hardware required.</span>
              </div>
            </div>
            <div className="rg-story-cta">
              <button type="button" className="rg-btn rg-btn--outline" onClick={onLaunchStudio}>
                Test Room Ingestion ↓
              </button>
            </div>
          </div>
        </article>

        {/* SECTION 3 — OBJECT SEGMENTATION (sam-segmentation.jpg) */}
        <article id="narrative-section-3" className="rg-story-card rg-story-card--right">
          <div className="rg-story-content">
            <span className="rg-step-num">03</span>
            <h3 className="rg-story-title">Furniture Segmentation with Meta SAM 3.1</h3>
            <p className="rg-story-desc">
              Meta’s Segment Anything Model (SAM 3.1) identifies individual furniture items in the photograph,
              isolating beds, wardrobes, desks, chairs, and nightstands into normalized 2D bounding boxes.
            </p>
            <div className="rg-benefit-chip">
              <span className="rg-benefit-icon">👁️</span>
              <div>
                <strong>Optical Segmentation</strong>
                <span>Identifies object categories and candidate envelopes with mandatory human metric confirmation.</span>
              </div>
            </div>
            <div className="rg-story-cta">
              <button type="button" className="rg-btn rg-btn--outline" onClick={onLaunchStudio}>
                Test Vision Scanner ↓
              </button>
            </div>
          </div>
          <div className="rg-story-media">
            <img
              src="/roomgenius-assets/sam-segmentation.jpg"
              alt="Meta SAM 3.1 Furniture Segmentation"
              className="rg-story-img"
              loading="lazy"
            />
            <span className="rg-story-badge">Stage 03 · Meta SAM 3.1</span>
          </div>
        </article>

        {/* SECTION 4 — DEPTH UNDERSTANDING (depth-analysis.jpg) */}
        <article id="narrative-section-4" className="rg-story-card rg-story-card--left">
          <div className="rg-story-media">
            <img
              src="/roomgenius-assets/depth-analysis.jpg"
              alt="Depth Anything V2 Metric Depth Heatmap"
              className="rg-story-img"
              loading="lazy"
            />
            <span className="rg-story-badge">Stage 04 · Depth Anything V2</span>
          </div>
          <div className="rg-story-content">
            <span className="rg-step-num">04</span>
            <h3 className="rg-story-title">Monocular Depth &amp; Spatial Ordering</h3>
            <p className="rg-story-desc">
              Depth Anything V2 computes continuous 16-bit metric depth heatmaps (0.8m to 5.5m),
              organizing detected furniture into foreground, midground, and wall-anchored background planes.
            </p>
            <div className="rg-benefit-chip">
              <span className="rg-benefit-icon">🗺️</span>
              <div>
                <strong>Metric Depth Layering</strong>
                <span>Distinguishes wall-adjacent items from central walking corridors to preserve open sightlines.</span>
              </div>
            </div>
          </div>
        </article>

        {/* SECTION 5 — DETERMINISTIC GEOMETRY (geometry-floorplan.jpg) */}
        <article id="narrative-section-5" className="rg-story-card rg-story-card--right">
          <div className="rg-story-content">
            <span className="rg-step-num">05</span>
            <h3 className="rg-story-title">Deterministic Geometry &amp; Collision Rules</h3>
            <p className="rg-story-desc">
              AI should never calculate physics. Our deterministic Python geometry engine strictly verifies
              room boundary confinement, Axis-Aligned Bounding Box (AABB) collisions, and 75–90cm egress passageways.
            </p>
            <div className="rg-benefit-chip">
              <span className="rg-benefit-icon">🛡️</span>
              <div>
                <strong>The Golden Rule</strong>
                <span>Never claims an arrangement is physically feasible unless pure mathematical validation proves it.</span>
              </div>
            </div>
            <div className="rg-story-cta">
              <button type="button" className="rg-btn rg-btn--primary" onClick={onLaunchStudio}>
                Generate Certified Layout ↓
              </button>
            </div>
          </div>
          <div className="rg-story-media">
            <img
              src="/roomgenius-assets/geometry-floorplan.jpg"
              alt="Deterministic 2D Geometry Floorplan"
              className="rg-story-img"
              loading="lazy"
            />
            <span className="rg-story-badge">Stage 05 · Deterministic Engine</span>
          </div>
        </article>

        {/* SECTION 6 — AI REDESIGN (muse-redesign.jpg) */}
        <article id="narrative-section-6" className="rg-story-card rg-story-card--left">
          <div className="rg-story-media">
            <img
              src="/roomgenius-assets/muse-redesign.jpg"
              alt="Meta Muse Image Photorealistic Redesign"
              className="rg-story-img"
              loading="lazy"
            />
            <span className="rg-story-badge">Stage 06 · Meta Muse Image</span>
          </div>
          <div className="rg-story-content">
            <span className="rg-step-num">06</span>
            <h3 className="rg-story-title">Aesthetic Redesign with Meta Muse Image</h3>
            <p className="rg-story-desc">
              Grounded in exact validated coordinates, Meta Muse Image synthesizes photorealistic interior redesign
              concept previews in Minimalist, Modern, Cozy, Traditional, or Industrial aesthetics without hallucinating layouts.
            </p>
            <div className="rg-benefit-chip">
              <span className="rg-benefit-icon">🎨</span>
              <div>
                <strong>Grounded Prompt Synthesis</strong>
                <span>Prompts are generated directly from verified layout coordinates and physical room dimensions.</span>
              </div>
            </div>
          </div>
        </article>

        {/* SECTION 7 — BEFORE AND AFTER (before-after.jpg) */}
        <article id="narrative-section-7" className="rg-story-card rg-story-card--featured">
          <div className="rg-featured-header">
            <span className="rg-step-num">07</span>
            <h3 className="rg-story-title">Interactive Before &amp; After Transformation</h3>
            <p className="rg-story-desc">
              Drag the interactive comparison slider below to inspect the transformation from a cluttered,
              unmeasured space into an architecturally certified, aesthetically elevated layout.
            </p>
          </div>
          <BeforeAfterSlider
            beforeImage="/roomgenius-assets/cluttered-room.jpg"
            afterImage="/roomgenius-assets/before-after.jpg"
            beforeLabel="Before: Cluttered &amp; Unmeasured"
            afterLabel="After: Certified Redesign"
          />
        </article>

        {/* SECTION 8 — FINAL CTA (ai-analysis-3d.jpg) */}
        <article id="narrative-section-8" className="rg-story-card rg-story-card--cta">
          <div className="rg-cta-card-content">
            <span className="rg-step-num">08</span>
            <h3 className="rg-cta-title">Architectural Rationale with Meta Muse Spark</h3>
            <p className="rg-cta-desc">
              Meta Muse Spark analyzes the deterministic coordinates to explain design reasoning, recommend
              installation steps, optimize daylight lines, and surface spatial trade-offs for human living.
            </p>
            <div className="rg-cta-action-row">
              <button
                type="button"
                className="rg-btn rg-btn--primary rg-btn--lg"
                onClick={onLaunchStudio}
              >
                <span>Launch Interactive Studio</span>
                <span className="rg-btn-arrow" aria-hidden="true">↓</span>
              </button>
            </div>
          </div>
          <div className="rg-cta-media">
            <img
              src="/roomgenius-assets/ai-analysis-3d.jpg"
              alt="Meta Muse Spark 3D Architectural Analysis"
              className="rg-cta-img"
              loading="lazy"
            />
          </div>
        </article>
      </div>
    </section>
  )
}
