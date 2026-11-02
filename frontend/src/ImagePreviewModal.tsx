import { useState } from 'react'

export interface PlacedItemSummary {
  id: string
  name: string
  x?: number
  y?: number
  width?: number
  length?: number
  rotation: number
  within_bounds: boolean
}

interface ImagePreviewModalProps {
  roomWidth: number
  roomLength: number
  style: string
  placedItems: PlacedItemSummary[]
}

interface PreviewResult {
  status: 'success' | 'fallback'
  image_data: string
  format: 'url' | 'b64_json' | 'svg_data_uri'
  prompt_used: string
  model_used: string
  disclaimer: string
}

export function ImagePreviewModal({ roomWidth, roomLength, style, placedItems }: ImagePreviewModalProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<PreviewResult | null>(null)
  const [error, setError] = useState('')
  const [customNotes, setCustomNotes] = useState('')
  const [showPrompt, setShowPrompt] = useState(false)

  async function handleGeneratePreview() {
    setLoading(true)
    setError('')

    try {
      const res = await fetch('http://localhost:8000/ai/generate-preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_width_cm: roomWidth,
          room_length_cm: roomLength,
          style: style || 'modern',
          placed_items: placedItems.map(item => ({
            id: item.id,
            name: item.name,
            placed: true,
            x: item.x,
            y: item.y,
            width: item.width,
            length: item.length,
            rotation: item.rotation,
            within_bounds: item.within_bounds,
          })),
          custom_prompt_additions: customNotes.trim() || undefined,
        }),
      })

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`)
      }

      const data: PreviewResult = await res.json()
      setPreview(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to generate visual preview'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rg-muse-image-section">
      <div className="rg-muse-header">
        <div className="rg-muse-title-wrap">
          <span className="rg-muse-icon">🎨</span>
          <div>
            <h3>Meta Muse Image Interior Redesign</h3>
            <p className="rg-muse-subtitle">
              Photorealistic visual concept preview grounded in your deterministic layout geometry.
            </p>
          </div>
        </div>
        <button
          type="button"
          className={isOpen ? "rg-btn rg-btn--ghost" : "rg-btn rg-btn--ai"}
          disabled={loading}
          onClick={() => {
            if (isOpen) {
              setIsOpen(false)
            } else {
              setIsOpen(true)
              if (!preview) {
                handleGeneratePreview()
              }
            }
          }}
        >
          {loading
            ? '✨ Generating Concept…'
            : isOpen
            ? '✕ Close Preview'
            : preview
            ? '🖼️ View Redesign Concept'
            : '✨ Generate Visual Concept'}
        </button>
      </div>

      {isOpen && (
        <div className="rg-muse-body">
          <div className="rg-muse-controls">
            <label className="rg-field" style={{ flex: 1, minWidth: '220px' }}>
              <span>Design Accents (Optional)</span>
              <input
                type="text"
                placeholder="e.g. natural oak textures, morning sunlight, linen fabrics"
                value={customNotes}
                onChange={e => setCustomNotes(e.target.value)}
              />
            </label>
            <button
              type="button"
              className="rg-btn rg-btn--secondary"
              onClick={handleGeneratePreview}
              disabled={loading}
              style={{ alignSelf: 'flex-end', height: '42px' }}
            >
              {loading ? 'Generating Concept…' : '🔄 Regenerate Concept'}
            </button>
          </div>

          {loading && (
            <div className="rg-ai-loading">
              <div className="rg-spinner" />
              <span>Synthesizing visual interior preview with Meta Muse Image…</span>
            </div>
          )}

          {error && (
            <div className="rg-toast rg-toast--error">
              <strong>Preview Generation Error:</strong> {error}
              <button type="button" className="rg-btn-retry" onClick={handleGeneratePreview}>
                Retry
              </button>
            </div>
          )}

          {preview && (
            <div className="rg-muse-preview-card">
              <div className="rg-muse-image-frame">
                <img src={preview.image_data} alt="Interior Design Concept" className="rg-muse-img" />
              </div>

              <div className="rg-muse-meta">
                <div className="rg-muse-status-row">
                  <span className="rg-badge rg-badge--success">
                    Model: {preview.model_used.startsWith('fallback') ? 'muse-image-1.0 (offline concept)' : preview.model_used}
                  </span>
                  <button
                    type="button"
                    className="rg-btn-link"
                    onClick={() => setShowPrompt(!showPrompt)}
                  >
                    {showPrompt ? 'Hide Prompt' : 'View Architectural Prompt'}
                  </button>
                </div>

                {showPrompt && (
                  <div className="rg-prompt-box">
                    <strong>Prompt Sent to Model:</strong>
                    <p>{preview.prompt_used}</p>
                  </div>
                )}

                <div className="rg-disclaimer-box">
                  <strong>⚠️ Truthful Guarantee:</strong> {preview.disclaimer}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

