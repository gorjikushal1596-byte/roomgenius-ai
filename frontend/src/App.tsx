import { useState } from 'react'
import './App.css'

/* ── Types ───────────────────────────────────────────────────────── */

interface FurnitureItem {
  id: string
  name: string
  width: string   // kept as string in the form for easier editing
  length: string
  height: string
}

interface PlacedItem {
  id: string
  name: string
  placed: boolean
  x?: number
  y?: number
  width?: number
  length?: number
  height?: number
  rotation: number
  within_bounds: boolean
  rejection_reason?: string
}

interface LayoutResponseData {
  status: string
  feasible: boolean
  summary: {
    room_width_cm: number
    room_length_cm: number
    room_height_cm?: number
    unit: string
    furniture_count: number
    placed_count: number
    unplaced_count: number
    has_preferences: boolean
  }
  placed_items: PlacedItem[]
  unplaced_items: PlacedItem[]
}

type HealthStatus = 'idle' | 'checking' | 'healthy' | 'error'
type SubmitStatus = 'idle' | 'submitting' | 'accepted' | 'error'

const STYLE_OPTIONS = ['minimalist', 'modern', 'traditional', 'cozy', 'industrial'] as const

/* ── Helpers ─────────────────────────────────────────────────────── */

let idCounter = 0
function nextId(): string {
  idCounter += 1
  return `furniture-${idCounter}`
}

function emptyItem(): FurnitureItem {
  return { id: nextId(), name: '', width: '', length: '', height: '' }
}

/** Returns an error string or null if valid. */
function validateDimension(value: string, label: string, required: boolean, max = 2000): string | null {
  if (value.trim() === '') return required ? `${label} is required` : null
  const n = Number(value)
  if (!Number.isFinite(n)) return `${label} must be a valid number`
  if (n <= 0) return `${label} must be greater than 0`
  if (n > max) return `${label} must be ≤ ${max} cm`
  return null
}

/* ── Component ───────────────────────────────────────────────────── */

export default function App() {
  // Health check state
  const [healthStatus, setHealthStatus] = useState<HealthStatus>('idle')
  const [healthError, setHealthError] = useState('')

  // Room dimensions
  const [roomWidth, setRoomWidth] = useState('')
  const [roomLength, setRoomLength] = useState('')
  const [roomHeight, setRoomHeight] = useState('')

  // Furniture
  const [furniture, setFurniture] = useState<FurnitureItem[]>([emptyItem()])

  // Preferences
  const [style, setStyle] = useState('')

  // Submission
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>('idle')
  const [submitMessage, setSubmitMessage] = useState('')
  const [layoutResult, setLayoutResult] = useState<LayoutResponseData | null>(null)

  /* ── Health check ──────────────────────────────────────────────── */

  async function checkHealth() {
    setHealthStatus('checking')
    setHealthError('')
    try {
      const res = await fetch('/api/health')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setHealthStatus(data.status === 'healthy' ? 'healthy' : 'error')
    } catch (err) {
      setHealthStatus('error')
      setHealthError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  /* ── Furniture CRUD ────────────────────────────────────────────── */

  function addFurniture() {
    setFurniture(prev => [...prev, emptyItem()])
  }

  function updateFurniture(id: string, field: keyof FurnitureItem, value: string) {
    setFurniture(prev =>
      prev.map(item => (item.id === id ? { ...item, [field]: value } : item)),
    )
  }

  function removeFurniture(id: string) {
    setFurniture(prev => prev.filter(item => item.id !== id))
  }

  /* ── Validation ────────────────────────────────────────────────── */

  function getFormErrors(): string[] {
    const errors: string[] = []
    const wErr = validateDimension(roomWidth, 'Room width', true)
    if (wErr) errors.push(wErr)
    const lErr = validateDimension(roomLength, 'Room length', true)
    if (lErr) errors.push(lErr)
    const hErr = validateDimension(roomHeight, 'Room height', false, 500)
    if (hErr) errors.push(hErr)

    furniture.forEach((item, i) => {
      const label = `Furniture #${i + 1}`
      if (!item.name.trim()) errors.push(`${label}: name is required`)
      const fw = validateDimension(item.width, `${label} width`, true)
      if (fw) errors.push(fw)
      const fl = validateDimension(item.length, `${label} depth`, true)
      if (fl) errors.push(fl)
      const fh = validateDimension(item.height, `${label} height`, false, 500)
      if (fh) errors.push(fh)
    })

    return errors
  }

  const formErrors = getFormErrors()
  const isValid = formErrors.length === 0

  /* ── Submit ────────────────────────────────────────────────────── */

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!isValid) return

    const payload = {
      width: Number(roomWidth),
      length: Number(roomLength),
      height: roomHeight.trim() ? Number(roomHeight) : undefined,
      unit: 'cm',
      furniture: furniture.map(f => ({
        id: f.id,
        name: f.name.trim(),
        width: Number(f.width),
        length: Number(f.length),
        height: f.height.trim() ? Number(f.height) : undefined,
      })),
      preferences: style ? { style } : undefined,
    }

    setSubmitStatus('submitting')
    setSubmitMessage('')
    setLayoutResult(null)
    try {
      const res = await fetch('/api/layout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok) {
        // FastAPI returns { detail: [...] } for 422
        const detail =
          Array.isArray(data?.detail)
            ? data.detail.map((d: { msg?: string }) => d?.msg ?? JSON.stringify(d)).join('; ')
            : (typeof data?.detail === 'string' && data.detail) || `HTTP ${res.status}`
        throw new Error(detail)
      }
      setLayoutResult(data)
      setSubmitStatus('accepted')
      const placedCnt = data?.summary?.placed_count ?? 0
      const totalCnt = data?.summary?.furniture_count ?? 0
      const unplacedCnt = data?.summary?.unplaced_count ?? 0
      if (unplacedCnt > 0) {
        setSubmitMessage(`Partial layout generated: ${placedCnt}/${totalCnt} items placed. ${unplacedCnt} item(s) could not fit.`)
      } else {
        setSubmitMessage(`Feasible layout generated! All ${placedCnt} furniture item(s) placed without overlap.`)
      }
    } catch (err) {
      setSubmitStatus('error')
      setSubmitMessage(err instanceof Error ? err.message : 'Submission failed')
    }
  }

  /* ── Render helpers ────────────────────────────────────────────── */

  const statusColour: Record<HealthStatus, string> = {
    idle: '#888',
    checking: '#d4a017',
    healthy: '#22c55e',
    error: '#ef4444',
  }

  const healthLabel: Record<HealthStatus, string> = {
    idle: 'Not checked yet',
    checking: 'Checking…',
    healthy: '✅ Backend is healthy',
    error: `❌ Error${healthError ? ': ' + healthError : ''}`,
  }

  /* ── JSX ───────────────────────────────────────────────────────── */

  return (
    <main className="rg-main">
      <h1 className="rg-title">🏠 RoomGenius AI</h1>
      <p className="rg-subtitle">AI-powered room layout assistant — Day 2</p>

      {/* Health check */}
      <section className="rg-card">
        <h2>Backend Connection</h2>
        <p style={{ color: statusColour[healthStatus], fontWeight: 600, minHeight: 24 }}>
          {healthLabel[healthStatus]}
        </p>
        <button
          id="health-check-btn"
          className="rg-btn rg-btn--secondary"
          onClick={checkHealth}
          disabled={healthStatus === 'checking'}
        >
          {healthStatus === 'checking' ? 'Checking…' : 'Check Backend Health'}
        </button>
      </section>

      {/* Room input form */}
      <form className="rg-card" onSubmit={handleSubmit}>
        <h2>Room Dimensions</h2>
        <p className="rg-unit-note">All measurements in centimetres (cm)</p>

        <div className="rg-row">
          <label className="rg-field">
            <span>Width (cm) *</span>
            <input
              type="number"
              step="any"
              min="1"
              max="2000"
              placeholder="e.g. 400"
              value={roomWidth}
              onChange={e => setRoomWidth(e.target.value)}
              required
            />
          </label>
          <label className="rg-field">
            <span>Length (cm) *</span>
            <input
              type="number"
              step="any"
              min="1"
              max="2000"
              placeholder="e.g. 500"
              value={roomLength}
              onChange={e => setRoomLength(e.target.value)}
              required
            />
          </label>
          <label className="rg-field">
            <span>Height (cm)</span>
            <input
              type="number"
              step="any"
              min="1"
              max="500"
              placeholder="optional"
              value={roomHeight}
              onChange={e => setRoomHeight(e.target.value)}
            />
          </label>
        </div>

        {/* Furniture list */}
        <h2 style={{ marginTop: 32 }}>Furniture Items</h2>

        {furniture.length === 0 && (
          <p className="rg-empty">No furniture added yet. Click "Add Furniture" below.</p>
        )}

        {furniture.map((item, i) => (
          <fieldset key={item.id} className="rg-furniture-card">
            <legend>#{i + 1}</legend>
            <div className="rg-row">
              <label className="rg-field rg-field--wide">
                <span>Name *</span>
                <input
                  type="text"
                  placeholder="e.g. Sofa"
                  value={item.name}
                  onChange={e => updateFurniture(item.id, 'name', e.target.value)}
                  required
                />
              </label>
              <label className="rg-field">
                <span>Width (cm) *</span>
                <input
                  type="number"
                  step="any"
                  min="1"
                  max="2000"
                  placeholder="e.g. 200"
                  value={item.width}
                  onChange={e => updateFurniture(item.id, 'width', e.target.value)}
                  required
                />
              </label>
              <label className="rg-field">
                <span>Depth (cm) *</span>
                <input
                  type="number"
                  step="any"
                  min="1"
                  max="2000"
                  placeholder="e.g. 90"
                  value={item.length}
                  onChange={e => updateFurniture(item.id, 'length', e.target.value)}
                  required
                />
              </label>
              <label className="rg-field">
                <span>Height (cm)</span>
                <input
                  type="number"
                  step="any"
                  min="1"
                  max="500"
                  placeholder="optional"
                  value={item.height}
                  onChange={e => updateFurniture(item.id, 'height', e.target.value)}
                />
              </label>
            </div>
            <button
              type="button"
              className="rg-btn rg-btn--danger rg-btn--sm"
              onClick={() => removeFurniture(item.id)}
            >
              Remove
            </button>
          </fieldset>
        ))}

        <button type="button" className="rg-btn rg-btn--secondary" onClick={addFurniture}>
          + Add Furniture
        </button>

        {/* Preferences */}
        <h2 style={{ marginTop: 32 }}>Preferences</h2>
        <label className="rg-field">
          <span>Room style</span>
          <select value={style} onChange={e => setStyle(e.target.value)}>
            <option value="">— none —</option>
            {STYLE_OPTIONS.map(s => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </label>

        {/* Validation messages */}
        {formErrors.length > 0 && (
          <ul className="rg-errors">
            {formErrors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        )}

        {/* Submit */}
        <button
          type="submit"
          className="rg-btn rg-btn--primary"
          disabled={!isValid || submitStatus === 'submitting'}
        >
          {submitStatus === 'submitting' ? 'Submitting…' : 'Submit Room Layout'}
        </button>

        {/* Submission feedback */}
        {submitStatus === 'accepted' && (
          <p className="rg-toast rg-toast--success">{submitMessage}</p>
        )}
        {submitStatus === 'error' && (
          <p className="rg-toast rg-toast--error">{submitMessage}</p>
        )}
      </form>

      {/* Deterministic Layout Results (Day 3) */}
      {layoutResult && (
        <section className="rg-card rg-results-card">
          <div className="rg-results-header">
            <h2>Generated Layout Arrangement</h2>
            <span
              className={`rg-badge ${
                layoutResult.feasible ? 'rg-badge--success' : 'rg-badge--warning'
              }`}
            >
              {layoutResult.feasible ? 'Feasible Layout' : 'Partial Layout'}
            </span>
          </div>

          <p className="rg-results-summary">
            Placed <strong>{layoutResult.summary.placed_count}</strong> of{' '}
            <strong>{layoutResult.summary.furniture_count}</strong> item(s) in a{' '}
            {layoutResult.summary.room_width_cm} × {layoutResult.summary.room_length_cm} cm room.
          </p>

          {/* Placed Items Table */}
          {layoutResult.placed_items.length > 0 && (
            <div className="rg-items-table-wrapper">
              <table className="rg-items-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Position (X, Y)</th>
                    <th>Placed Size (W × D)</th>
                    <th>Rotation</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {layoutResult.placed_items.map(item => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.name}</strong> <span className="rg-item-id">({item.id})</span>
                      </td>
                      <td>
                        ({item.x} cm, {item.y} cm)
                      </td>
                      <td>
                        {item.width} × {item.length} cm
                      </td>
                      <td>{item.rotation}°</td>
                      <td>
                        <span className="rg-tag rg-tag--success">Valid</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Unplaced Items Section */}
          {layoutResult.unplaced_items.length > 0 && (
            <div className="rg-unplaced-section">
              <h3 className="rg-unplaced-title">⚠️ Unplaced Furniture ({layoutResult.unplaced_items.length})</h3>
              <ul className="rg-unplaced-list">
                {layoutResult.unplaced_items.map(item => (
                  <li key={item.id}>
                    <strong>{item.name}</strong> ({item.width} × {item.length} cm):{' '}
                    <span className="rg-rejection-reason">{item.rejection_reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </main>
  )
}
