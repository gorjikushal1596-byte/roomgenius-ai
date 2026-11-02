export function FooterSection() {
  return (
    <footer className="rg-footer">
      <div className="rg-footer-container">
        <div className="rg-footer-top">
          <div className="rg-footer-brand">
            <div className="rg-brand">
              <span className="rg-brand-mark">RG</span>
              <div className="rg-brand-text">
                <span className="rg-brand-title">RoomGenius<span className="rg-brand-accent">.ai</span></span>
                <span className="rg-brand-subtitle">Deterministic Spatial Architecture</span>
              </div>
            </div>
            <p className="rg-footer-tagline">
              Deterministic geometry guarantees physical feasibility; multimodal Meta AI elevates architectural reasoning and aesthetic redesign.
            </p>
          </div>

          <div className="rg-footer-links-col">
            <h4>Technology Stack</h4>
            <ul>
              <li><span>Meta Model API (Muse Spark 1.3)</span></li>
              <li><span>Meta SAM 3.1 Object Detection</span></li>
              <li><span>Depth Anything V2 Metric Depth</span></li>
              <li><span>Meta Muse Image 1.0</span></li>
              <li><span>Python AABB Geometry Engine</span></li>
            </ul>
          </div>

          <div className="rg-footer-links-col">
            <h4>Hackathon Links</h4>
            <ul>
              <li>
                <a
                  href="https://github.com/gorjikushal1596-byte/roomgenius-ai"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  GitHub Repository ↗
                </a>
              </li>
              <li>
                <a href="#hero">Back to Top ↑</a>
              </li>
              <li>
                <a href="#studio">Interactive Studio ↓</a>
              </li>
            </ul>
          </div>
        </div>

        <div className="rg-footer-bottom">
          <p>© 2026 RoomGenius AI · Built for the Meta Global AI Developer Hackathon.</p>
          <p className="rg-footer-disclaimer">
            <strong>Truthful Integrity:</strong> AI concept previews and optical depth estimates do not replace certified physical measurements. Refer to the 2D Floorplan for definitive centimetre coordinates.
          </p>
        </div>
      </div>
    </footer>
  )
}

