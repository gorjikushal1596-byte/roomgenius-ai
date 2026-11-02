import { useState, useRef, useEffect, useCallback } from 'react'

interface CinematicHeroProps {
  onOptimizeClick: () => void
  onExploreFeaturesClick: () => void
}

export function CinematicHero({ onOptimizeClick, onExploreFeaturesClick }: CinematicHeroProps) {
  const heroRef = useRef<HTMLElement>(null)
  const [scrollY, setScrollY] = useState(0)
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 })
  const [isLoaded, setIsLoaded] = useState(false)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  })

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  // Scroll listener for natural parallax
  useEffect(() => {
    if (prefersReducedMotion) return
    let ticking = false
    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          setScrollY(window.scrollY)
          ticking = false
        })
        ticking = true
      }
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [prefersReducedMotion])

  // Mouse move for subtle camera-like parallax
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLElement>) => {
    if (prefersReducedMotion || !heroRef.current) return
    const rect = heroRef.current.getBoundingClientRect()
    const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1
    const normY = ((e.clientY - rect.top) / rect.height) * 2 - 1

    setMouseOffset({
      x: Number((normX * 12).toFixed(1)),
      y: Number((normY * 8).toFixed(1)),
    })
  }, [prefersReducedMotion])

  const handleMouseLeave = useCallback(() => {
    setMouseOffset({ x: 0, y: 0 })
  }, [])

  // Parallax transform calculation
  const parallaxTranslateY = prefersReducedMotion ? 0 : Math.min(scrollY * 0.22, 120)
  const parallaxScale = prefersReducedMotion ? 1 : 1 + Math.min(scrollY * 0.0003, 0.05)

  return (
    <section
      ref={heroRef}
      id="hero"
      className={`rg-hero-fullwidth ${isLoaded ? 'rg-hero--loaded' : ''}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* ── Layer 1: Photorealistic Background Image with Cinematic Motion ── */}
      <div className="rg-hero-bg-canvas">
        <img
          src="/roomgenius-assets/hero-bedroom.jpg"
          alt="RoomGenius AI Architectural Bedroom"
          className="rg-hero-main-img"
          loading="eager"
          fetchPriority="high"
          onLoad={() => setIsLoaded(true)}
          style={{
            transform: prefersReducedMotion
              ? 'none'
              : `translate3d(${-mouseOffset.x}px, ${parallaxTranslateY - mouseOffset.y}px, 0) scale(${parallaxScale})`,
          }}
        />

        {/* Layer 2: Editorial Lighting & Architectural Colour Grading Overlays */}
        <div className="rg-hero-scrim-left" />
        <div className="rg-hero-scrim-bottom" />
        <div className="rg-hero-ambient-tint" />
      </div>

      {/* ── Layer 3: Foreground Content & Typography ── */}
      <div className="rg-hero-container-wide">
        <div className="rg-hero-editorial-panel">
          {/* Hackathon Badge */}
          <div className="rg-hero-badge-pill">
            <span className="rg-badge-live-pulse" />
            <span className="rg-badge-kicker">Spatial Precision &amp; Multimodal Meta AI</span>
          </div>

          {/* Headline */}
          <h1 className="rg-hero-title-cinematic">
            Your Space.<br />
            <span className="rg-title-accent-italic">Reimagined by Intelligence.</span>
          </h1>

          {/* Description */}
          <p className="rg-hero-desc-editorial">
            RoomGenius AI combines visual understanding, spatial intelligence and deterministic geometry
            to transform the way you organize your room.
          </p>

          {/* CTAs */}
          <div className="rg-hero-cta-cluster">
            <button
              type="button"
              className="rg-btn rg-btn--primary rg-btn--lg"
              onClick={onOptimizeClick}
            >
              <span>Design My Room</span>
              <span className="rg-btn-arrow" aria-hidden="true">→</span>
            </button>
            <button
              type="button"
              className="rg-btn rg-btn--secondary rg-btn--lg"
              onClick={onExploreFeaturesClick}
            >
              Explore the Experience
            </button>
          </div>

          {/* Trust Metrics Bar */}
          <div className="rg-hero-proof-bar">
            <div className="rg-proof-stat">
              <span className="rg-proof-number">100%</span>
              <span className="rg-proof-label">Certified Collision-Free</span>
            </div>
            <div className="rg-proof-divider" />
            <div className="rg-proof-stat">
              <span className="rg-proof-number">&lt; 10ms</span>
              <span className="rg-proof-label">Deterministic Geometry</span>
            </div>
            <div className="rg-proof-divider" />
            <div className="rg-proof-stat">
              <span className="rg-proof-number">Zero</span>
              <span className="rg-proof-label">Dimension Hallucinations</span>
            </div>
          </div>
        </div>

        {/* Interactive Subtle Spatial Pins on the Scene */}
        <div className="rg-hero-spatial-annotations" aria-hidden="true">
          <div className="rg-spatial-pin rg-spatial-pin--bed">
            <span className="rg-pin-radar" />
            <div className="rg-pin-card">
              <span className="rg-pin-tag">Calibrated Furniture</span>
              <strong>Queen Platform Suite</strong>
              <small>160 × 200 cm · Zero Wall Overlap</small>
            </div>
          </div>

          <div className="rg-spatial-pin rg-spatial-pin--window">
            <span className="rg-pin-radar" />
            <div className="rg-pin-card">
              <span className="rg-pin-tag">Spatial Perception</span>
              <strong>Daylight Axis &amp; Egress</strong>
              <small>Metric Depth Layering (0.8m – 5.5m)</small>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
