interface NavigationBarProps {
  onScrollToStudio: () => void
  onScrollToNarrative: () => void
}

export function NavigationBar({ onScrollToStudio, onScrollToNarrative }: NavigationBarProps) {
  return (
    <header className="rg-navbar">
      <div className="rg-navbar-inner">
        <a href="#hero" className="rg-brand">
          <span className="rg-brand-mark">RG</span>
          <div className="rg-brand-text">
            <span className="rg-brand-title">RoomGenius<span className="rg-brand-accent">.ai</span></span>
            <span className="rg-brand-subtitle">Spatial Precision & Meta AI</span>
          </div>
        </a>

        <nav className="rg-nav-links">
          <button type="button" className="rg-nav-link" onClick={onScrollToNarrative}>
            Story &amp; Features
          </button>
          <a href="#narrative-section-3" className="rg-nav-link">
            Vision Pipeline
          </a>
          <a href="#narrative-section-5" className="rg-nav-link">
            Physical Truth
          </a>
          <a href="#narrative-section-7" className="rg-nav-link">
            Before &amp; After
          </a>
        </nav>

        <div className="rg-nav-actions">
          <button
            type="button"
            className="rg-btn rg-btn--primary rg-btn--nav"
            onClick={onScrollToStudio}
          >
            Launch Studio ↓
          </button>
        </div>
      </div>
    </header>
  )
}

