import { useState, useRef } from 'react'
import { RoomVisualizer } from './RoomVisualizer'
import { SegmentationDrawer, type CalibratedFurnitureItem } from './SegmentationDrawer'
import { ImagePreviewModal } from './ImagePreviewModal'
import { NavigationBar } from './components/NavigationBar'
import { CinematicHero } from './components/CinematicHero'
import { NarrativeStoryline } from './components/NarrativeStoryline'
import { FooterSection } from './components/FooterSection'
import { StudioWorkflowProgress } from './components/StudioWorkflowProgress'
import './App.css'
import './ArchitecturalExperience.css'

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

interface LayoutExplanationData {
  status: 'success' | 'fallback'
  summary: string
  design_reasoning: string
  arrangement_tips: string[]
  trade_offs: string[]
  model_used: string
  reasoning_content?: string
}

type HealthStatus = 'idle' | 'checking' | 'healthy' | 'error'
type SubmitStatus = 'idle' | 'submitting' | 'accepted' | 'error'
type AiStatus = 'idle' | 'loading' | 'success' | 'error'

const STYLE_OPTIONS = ['minimalist', 'modern', 'traditional', 'cozy', 'industrial'] as const

interface PresetData {
  name: string
  description: string
  icon: string
  tag: string
  dimensionsText: string
  furnitureCountText: string
  variantClass: string
  width: string
  length: string
  height: string
  style: string
  furniture: Array<{ name: string; width: string; length: string; height?: string }>
}

const DEMO_PRESETS: Record<string, PresetData> = {
  'master-bedroom': {
    name: 'Master Bedroom',
    description: 'Minimalist suite · 100% Feasible layout',
    tag: '100% Feasible',
    dimensionsText: '450 × 550 cm · 24.8 m²',
    furnitureCountText: '4 standard pieces',
    variantClass: 'rg-preset-card--sage',
    icon: '🛏️',
    width: '450',
    length: '550',
    height: '270',
    style: 'minimalist',
    furniture: [
      { name: 'Queen Platform Bed', width: '160', length: '200', height: '100' },
      { name: 'Double Wardrobe', width: '120', length: '60', height: '210' },
      { name: 'Writing Desk', width: '120', length: '60', height: '75' },
      { name: 'Bedside Nightstand', width: '50', length: '45', height: '55' },
    ],
  },
  'home-office': {
    name: 'Compact Home Office',
    description: 'Modern workspace · 100% Feasible layout',
    tag: '100% Feasible',
    dimensionsText: '320 × 380 cm · 12.2 m²',
    furnitureCountText: '4 office pieces',
    variantClass: 'rg-preset-card--teal',
    icon: '💻',
    width: '320',
    length: '380',
    height: '260',
    style: 'modern',
    furniture: [
      { name: 'Executive Workstation', width: '140', length: '70', height: '75' },
      { name: 'Ergonomic Office Chair', width: '65', length: '65', height: '110' },
      { name: 'Tall Bookcase', width: '90', length: '35', height: '190' },
      { name: 'Storage Credenza', width: '110', length: '45', height: '80' },
    ],
  },
  'crowded-studio': {
    name: 'Crowded Studio (Infeasible Test)',
    description: 'Overcrowded micro-room · Rejection test',
    tag: '⚠️ Infeasible Test',
    dimensionsText: '220 × 220 cm · 4.8 m²',
    furnitureCountText: '4 oversized pieces',
    variantClass: 'rg-preset-card--amber',
    icon: '⚠️',
    width: '220',
    length: '220',
    height: '250',
    style: 'cozy',
    furniture: [
      { name: 'King Bed', width: '190', length: '200', height: '110' },
      { name: '3-Seater Sofa', width: '200', length: '90', height: '85' },
      { name: '4-Person Dining Table', width: '120', length: '80', height: '75' },
      { name: 'Wardrobe Unit', width: '140', length: '60', height: '200' },
    ],
  },
}

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
  const [furniture, setFurniture] = useState<FurnitureItem[]>(() => [emptyItem()])

  // Preferences
  const [style, setStyle] = useState('')

  // Submission
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>('idle')
  const [submitMessage, setSubmitMessage] = useState('')
  const [layoutResult, setLayoutResult] = useState<LayoutResponseData | null>(null)
  const [submittedInventory, setSubmittedInventory] = useState<FurnitureItem[]>([])
  const [submittedStyle, setSubmittedStyle] = useState<string>('')
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null)
  const [hoveredItemId, setHoveredItemId] = useState<string | null>(null)

  // AI Explanation (Day 5)
  const [aiStatus, setAiStatus] = useState<AiStatus>('idle')
  const [aiExplanation, setAiExplanation] = useState<LayoutExplanationData | null>(null)
  const [aiError, setAiError] = useState<string>('')
  const [showReasoningTrace, setShowReasoningTrace] = useState<boolean>(false)
  const aiRequestRef = useRef<number>(0)

  // Active Preset & Vision Tracking
  const [activePreset, setActivePreset] = useState<string | null>('master-bedroom')
  const [hasPhotoAnalysis, setHasPhotoAnalysis] = useState<boolean>(false)

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

  /* ── Presets & Reset (Day 7) ───────────────────────────────────── */

  function loadPreset(key: string) {
    const preset = DEMO_PRESETS[key]
    if (!preset) return

    setActivePreset(key)
    setRoomWidth(preset.width)
    setRoomLength(preset.length)
    setRoomHeight(preset.height)
    setStyle(preset.style)
    setFurniture(
      preset.furniture.map(f => ({
        id: nextId(),
        name: f.name,
        width: f.width,
        length: f.length,
        height: f.height || '',
      }))
    )
    setLayoutResult(null)
    setSubmitStatus('idle')
    setSubmitMessage('')
    setAiExplanation(null)
    setAiStatus('idle')
    setAiError('')
  }

  function clearAll() {
    setActivePreset(null)
    setHasPhotoAnalysis(false)
    setRoomWidth('')
    setRoomLength('')
    setRoomHeight('')
    setStyle('')
    setFurniture([emptyItem()])
    setLayoutResult(null)
    setSubmitStatus('idle')
    setSubmitMessage('')
    setAiExplanation(null)
    setAiStatus('idle')
    setAiError('')
  }

  /* ── Furniture CRUD ────────────────────────────────────────────── */

  function addFurniture() {
    setActivePreset(null)
    setFurniture(prev => [...prev, emptyItem()])
  }

  function updateFurniture(id: string, field: keyof FurnitureItem, value: string) {
    setActivePreset(null)
    setFurniture(prev =>
      prev.map(item => (item.id === id ? { ...item, [field]: value } : item)),
    )
  }

  function removeFurniture(id: string) {
    setActivePreset(null)
    setFurniture(prev => prev.filter(item => item.id !== id))
  }

  function handleImportCalibratedFurniture(items: CalibratedFurnitureItem[]) {
    setActivePreset(null)
    setHasPhotoAnalysis(true)
    setFurniture(prev => {
      const existing = prev.filter(f => f.name.trim() !== '' || f.width.trim() !== '')
      const newItems = items.map(it => ({
        id: nextId(),
        name: it.name,
        width: it.width,
        length: it.length,
        height: it.height || '',
      }))
      return [...existing, ...newItems]
    })
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
    setSelectedItemId(null)
    setAiExplanation(null)
    setAiStatus('idle')
    setAiError('')
    aiRequestRef.current += 1
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
      setSubmittedInventory([...furniture])
      setSubmittedStyle(style)
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

  /* ── AI Explanation (Day 5) ─────────────────────────────────────── */

  async function handleExplainLayout() {
    if (!layoutResult || aiStatus === 'loading') return
    const requestId = ++aiRequestRef.current

    const payload = {
      room_width_cm: layoutResult.summary.room_width_cm,
      room_length_cm: layoutResult.summary.room_length_cm,
      room_height_cm: layoutResult.summary.room_height_cm,
      preferences: submittedStyle ? { style: submittedStyle } : undefined,
      placed_items: layoutResult.placed_items,
      unplaced_items: layoutResult.unplaced_items,
    }

    setAiStatus('loading')
    setAiError('')
    try {
      const res = await fetch('/api/ai/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => null)
      if (requestId !== aiRequestRef.current) return

      if (!res.ok) {
        const detail =
          Array.isArray(data?.detail)
            ? data.detail.map((d: { msg?: string }) => d?.msg ?? JSON.stringify(d)).join('; ')
            : (typeof data?.detail === 'string' && data.detail) || `HTTP ${res.status}`
        throw new Error(detail)
      }
      setAiExplanation(data)
      setAiStatus('success')
    } catch (err) {
      if (requestId !== aiRequestRef.current) return
      setAiStatus('error')
      setAiError(err instanceof Error ? err.message : 'Failed to generate AI layout explanation')
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

  function scrollToStudio() {
    const el = document.getElementById('studio')
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  function scrollToNarrative() {
    const el = document.getElementById('narrative')
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  function handleWorkflowStepClick(targetAnchor: string) {
    const el = document.getElementById(targetAnchor)
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  /* ── JSX ───────────────────────────────────────────────────────── */

  return (
    <div className="rg-app-shell">
      <NavigationBar onScrollToStudio={scrollToStudio} onScrollToNarrative={scrollToNarrative} />
      <CinematicHero onOptimizeClick={scrollToStudio} onExploreFeaturesClick={scrollToNarrative} />
      <NarrativeStoryline onLaunchStudio={scrollToStudio} />

      <main id="studio" className="rg-main">
        <div className="rg-studio-header">
          <span className="rg-studio-kicker">Interactive Studio</span>
          <h2 className="rg-title">Deterministic Studio &amp; Multi-Model AI</h2>
          <p className="rg-subtitle">
            Configure room dimensions, scan photos, and generate certified 2D layouts with Meta AI critiques.
          </p>
        </div>

        {/* Workflow Progress Indicator */}
        <StudioWorkflowProgress
          hasValidDimensions={Boolean(roomWidth && roomLength && Number(roomWidth) > 0 && Number(roomLength) > 0)}
          hasValidFurniture={furniture.length > 0 && furniture.every(f => f.name.trim() !== '' && Number(f.width) > 0 && Number(f.length) > 0)}
          hasPhotoAnalysis={hasPhotoAnalysis}
          hasStyleSelected={Boolean(style)}
          hasLayoutResult={Boolean(layoutResult)}
          hasAiResults={Boolean(aiExplanation)}
          onStepClick={handleWorkflowStepClick}
        />

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

      {/* Quick Demo Presets (Day 7) */}
      <section className="rg-card rg-presets-card">
        <div className="rg-presets-header">
          <div>
            <h2>⚡ Quick Demo Presets</h2>
            <p className="rg-presets-subtitle">
              Click a curated preset below to instantly load room dimensions and furniture:
            </p>
          </div>
          <button
            type="button"
            className="rg-btn rg-btn--ghost"
            style={{ fontSize: '0.85rem', padding: '6px 14px' }}
            onClick={clearAll}
          >
            🧹 Reset Form
          </button>
        </div>
        <div className="rg-presets-grid-redesign" role="radiogroup" aria-label="Quick Demo Presets">
          {Object.entries(DEMO_PRESETS).map(([key, preset]) => {
            const isSelected = activePreset === key
            return (
              <button
                key={key}
                type="button"
                role="radio"
                aria-checked={isSelected}
                className={`rg-preset-card ${preset.variantClass} ${isSelected ? 'rg-preset-card--active' : ''}`}
                onClick={() => loadPreset(key)}
              >
                <div className="rg-preset-card-top">
                  <span className="rg-preset-card-icon">{preset.icon}</span>
                  <span className="rg-preset-card-tag">{preset.tag}</span>
                </div>
                <h3 className="rg-preset-card-title">{preset.name}</h3>
                <p className="rg-preset-card-desc">{preset.description}</p>
                <div className="rg-preset-card-meta">
                  <span className="rg-preset-meta-pill">{preset.dimensionsText}</span>
                  <span className="rg-preset-meta-pill">{preset.furnitureCountText}</span>
                </div>
              </button>
            )
          })}
        </div>
      </section>

      {/* Room input form */}
      <form className="rg-card" id="room-dimensions-card" onSubmit={handleSubmit}>
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

        {/* Meta SAM 3.1 Object Segmentation (Phase 3) */}
        <div id="vision-scanner-card">
          <SegmentationDrawer onImportItems={handleImportCalibratedFurniture} />
        </div>

        {/* Furniture list */}
        <h2 id="furniture-list-heading" style={{ marginTop: 32 }}>Furniture Items</h2>

        {furniture.length === 0 && (
          <p className="rg-empty">No furniture added yet. Click "+ Add Furniture Item" below.</p>
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
              🗑️ Remove
            </button>
          </fieldset>
        ))}

        <button type="button" className="rg-btn--add-dashed" onClick={addFurniture}>
          <span aria-hidden="true" style={{ fontSize: '1.2rem', fontWeight: 700 }}>+</span> Add Furniture Item
        </button>

        {/* Preferences */}
        <h2 id="preferences-heading" style={{ marginTop: 32 }}>Preferences</h2>
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
          id="submit-layout-btn"
          type="submit"
          className="rg-btn rg-btn--primary rg-btn--lg"
          disabled={!isValid || submitStatus === 'submitting'}
          style={{ width: '100%', marginTop: '24px' }}
        >
          {submitStatus === 'submitting' ? '📐 Computing Deterministic Layout…' : '📐 Optimize Room Layout'}
        </button>

        {/* Submission feedback */}
        {submitStatus === 'accepted' && (
          <p className="rg-toast rg-toast--success">{submitMessage}</p>
        )}
        {submitStatus === 'error' && (
          <p className="rg-toast rg-toast--error">{submitMessage}</p>
        )}
      </form>

      {/* Deterministic Layout & AI Results (Area A, B, C) */}
      {layoutResult && (() => {
        const roomAreaM2 = (layoutResult.summary.room_width_cm * layoutResult.summary.room_length_cm) / 10000
        const furnitureAreaM2 = layoutResult.placed_items.reduce((sum, item) => sum + (item.width || 0) * (item.length || 0), 0) / 10000
        const utilizationPercent = roomAreaM2 > 0 ? ((furnitureAreaM2 / roomAreaM2) * 100).toFixed(1) : '0'

        return (
          <section className="rg-card rg-results-card" id="deterministic-results-area">
            {/* ── AREA A: Deterministic Layout Ground Truth ──────────────── */}
            <div className="rg-result-block" id="area-a-geometry">
              <div className="rg-result-block-header">
                <div className="rg-result-badge-row">
                  <span className="rg-area-tag rg-area-tag--engine">Area A · Deterministic Ground Truth</span>
                  <span
                    className={`rg-feasibility-pill ${
                      layoutResult.feasible ? 'rg-feasibility-pill--success' : 'rg-feasibility-pill--warning'
                    }`}
                  >
                    {layoutResult.feasible ? '✓ 100% Feasible Layout' : '⚠️ Partial Layout (Collisions Detected)'}
                  </span>
                  <span className="rg-model-tag">Python Shapely Engine</span>
                </div>
                <h3 className="rg-result-title">Certified 2D Floorplan &amp; Spatial Clearance</h3>
                <p className="rg-result-desc">
                  Strictly validated boundaries, positive-area overlap prevention, and egress clearance corridors.
                </p>
              </div>

              {/* Metrics Bar */}
              <div className="rg-metrics-bar">
                <div className="rg-metric">
                  <span className="rg-metric-label">Room Area</span>
                  <span className="rg-metric-value">{roomAreaM2.toFixed(1)} m²</span>
                  <span className="rg-metric-sub">{layoutResult.summary.room_width_cm} × {layoutResult.summary.room_length_cm} cm</span>
                </div>
                <div className="rg-metric">
                  <span className="rg-metric-label">Furniture Footprint</span>
                  <span className="rg-metric-value">{furnitureAreaM2.toFixed(1)} m²</span>
                  <span className="rg-metric-sub">{layoutResult.summary.placed_count} item(s) placed</span>
                </div>
                <div className="rg-metric">
                  <span className="rg-metric-label">Floor Utilization</span>
                  <span className="rg-metric-value">{utilizationPercent}%</span>
                  <span className="rg-metric-sub">{(roomAreaM2 - furnitureAreaM2).toFixed(1)} m² free space</span>
                </div>
                <div className="rg-metric">
                  <span className="rg-metric-label">Placement Rate</span>
                  <span className="rg-metric-value">
                    {layoutResult.summary.placed_count} / {layoutResult.summary.furniture_count}
                  </span>
                  <span className="rg-metric-sub">
                    {layoutResult.summary.unplaced_count === 0 ? 'All placed' : `${layoutResult.summary.unplaced_count} unplaced`}
                  </span>
                </div>
              </div>

              {/* Before / After Comparison Grid */}
              <div className="rg-comparison-container">
                <div className="rg-comparison-col">
                  <div className="rg-col-header">
                    <span className="rg-col-tag rg-col-tag--before">Before</span>
                    <h3>Unarranged Inventory</h3>
                  </div>
                  <p className="rg-truthful-note">
                    Initial spatial positions were not supplied. Showing inventory awaiting layout optimization:
                  </p>
                  <div className="rg-inventory-list">
                    {submittedInventory.length === 0 && (
                      <p className="rg-empty">No furniture items were submitted for this room.</p>
                    )}
                    {submittedInventory.map((item, idx) => {
                      const isPlaced = layoutResult.placed_items.some(p => p.id === item.id)
                      const isSelected = selectedItemId === item.id
                      const isHovered = hoveredItemId === item.id
                      const isActive = isSelected || isHovered

                      return (
                        <div
                          key={item.id}
                          className={`rg-inventory-card ${isActive ? 'rg-inventory-card--selected' : ''} ${
                            !isPlaced ? 'rg-inventory-card--unplaced' : ''
                          }`}
                          role="button"
                          tabIndex={0}
                          aria-pressed={isSelected}
                          onClick={() => setSelectedItemId(isSelected ? null : item.id)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault()
                              setSelectedItemId(isSelected ? null : item.id)
                            }
                          }}
                          onFocus={() => setHoveredItemId(item.id)}
                          onBlur={() => setHoveredItemId(null)}
                          onMouseEnter={() => setHoveredItemId(item.id)}
                          onMouseLeave={() => setHoveredItemId(null)}
                        >
                          <div className="rg-inventory-top">
                            <strong>#{idx + 1} {item.name || '(Unnamed)'}</strong>
                            <span className={`rg-tag ${isPlaced ? 'rg-tag--success' : 'rg-tag--warning'}`}>
                              {isPlaced ? 'Placed' : 'Rejected'}
                            </span>
                          </div>
                          <div className="rg-inventory-meta">
                            <span>{item.width || '0'} × {item.length || '0'} cm</span>
                            {item.height && <span> · H: {item.height} cm</span>}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <div className="rg-comparison-col">
                  <div className="rg-col-header">
                    <span className="rg-col-tag rg-col-tag--after">After</span>
                    <h3>Proposed 2D Floorplan</h3>
                  </div>
                  <p className="rg-truthful-note">
                    Interactive vector floorplan rendered using coordinates from deterministic engine:
                  </p>
                  <RoomVisualizer
                    roomWidth={layoutResult.summary.room_width_cm}
                    roomLength={layoutResult.summary.room_length_cm}
                    items={layoutResult.placed_items}
                    selectedId={selectedItemId}
                    hoveredId={hoveredItemId}
                    onSelectItem={setSelectedItemId}
                    onHoverItem={setHoveredItemId}
                  />
                </div>
              </div>

              {/* Placed Items Table */}
              {layoutResult.placed_items.length > 0 && (
                <div className="rg-table-section">
                  <h3>Placed Furniture Breakdown</h3>
                  <div className="rg-items-table-wrapper">
                    <table className="rg-items-table">
                      <thead>
                        <tr>
                          <th>Item</th>
                          <th>Position (X, Y)</th>
                          <th>Placed Footprint (W × D)</th>
                          <th>Orientation</th>
                          <th>Bounds Check</th>
                          <th>Select</th>
                        </tr>
                      </thead>
                      <tbody>
                        {layoutResult.placed_items.map(item => {
                          const isSelected = selectedItemId === item.id
                          const isHovered = hoveredItemId === item.id
                          const isActive = isSelected || isHovered

                          return (
                            <tr
                              key={item.id}
                              className={isActive ? 'rg-table-row--selected' : ''}
                              onClick={() => setSelectedItemId(isSelected ? null : item.id)}
                              onMouseEnter={() => setHoveredItemId(item.id)}
                              onMouseLeave={() => setHoveredItemId(null)}
                              style={{ cursor: 'pointer' }}
                            >
                              <td>
                                <strong>{item.name}</strong> <span className="rg-item-id">({item.id})</span>
                              </td>
                              <td>
                                ({item.x} cm, {item.y} cm)
                              </td>
                              <td>
                                {item.width} × {item.length} cm
                              </td>
                              <td>
                                <span className="rg-badge-rotation">
                                  {item.rotation === 90 ? '↻ 90° (Rotated)' : '0° (Standard)'}
                                </span>
                              </td>
                              <td>
                                <span className="rg-tag rg-tag--success">Inside room</span>
                              </td>
                              <td>
                                <button
                                  type="button"
                                  className={`rg-btn-select ${isSelected ? 'rg-btn-select--active' : ''}`}
                                  aria-pressed={isSelected}
                                  aria-label={`Select ${item.name}`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setSelectedItemId(isSelected ? null : item.id)
                                  }}
                                  onFocus={() => setHoveredItemId(item.id)}
                                  onBlur={() => setHoveredItemId(null)}
                                >
                                  {isSelected ? '✓ Selected' : 'Select'}
                                </button>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Unplaced Items Section */}
              {layoutResult.unplaced_items.length > 0 && (
                <div className="rg-unplaced-section">
                  <h3 className="rg-unplaced-title">⚠️ Infeasible Furniture Items ({layoutResult.unplaced_items.length})</h3>
                  <p className="rg-unplaced-desc">
                    The following items could not be placed due to boundary constraints or positive-area collisions:
                  </p>
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

              {/* Truthful Deterministic Guarantee Callout */}
              <div className="rg-guarantee-callout">
                <span className="rg-guarantee-icon">🛡️</span>
                <div>
                  <strong>Deterministic Ground Truth Guarantee:</strong> All placement coordinates, bounding boxes, collision boundaries, and egress clearances are strictly verified by the deterministic Python geometry engine. No layout geometry or spatial dimensions are hallucinated.
                </div>
              </div>
            </div>

            {/* ── AREA B: Meta Muse Spark 1.3 Design Critique ─────────────── */}
            <div
              className="rg-result-block"
              id="area-b-spark"
              style={{ marginTop: '48px', paddingTop: '36px', borderTop: '1px solid var(--rg-sand)' }}
            >
              <div className="rg-result-block-header">
                <div className="rg-result-badge-row">
                  <span className="rg-area-tag rg-area-tag--ai">Area B · AI Architecture Analysis</span>
                  <span className="rg-model-tag">Meta Muse Spark 1.3</span>
                </div>
                <div className="rg-ai-header" style={{ marginBottom: 0 }}>
                  <div>
                    <h3 className="rg-result-title">Meta AI Architectural Design Critique</h3>
                    <p className="rg-result-desc">
                      Personalized spatial reasoning and ergonomic transit critique grounded in your deterministic layout.
                    </p>
                  </div>
                  <button
                    type="button"
                    className="rg-btn rg-btn--ai"
                    disabled={aiStatus === 'loading'}
                    onClick={handleExplainLayout}
                  >
                    {aiStatus === 'loading'
                      ? '✨ Analyzing Layout…'
                      : aiExplanation
                      ? '🔄 Refresh AI Critique'
                      : '✨ Explain Layout with Meta AI'}
                  </button>
                </div>
              </div>

              {aiStatus === 'loading' && (
                <div className="rg-ai-loading">
                  <div className="rg-spinner" />
                  <span>Consulting Meta Muse Spark architectural reasoning model…</span>
                </div>
              )}

              {aiStatus === 'error' && (
                <div className="rg-toast rg-toast--error">
                  <strong>AI Critique Error:</strong> {aiError}
                  <button type="button" className="rg-btn-retry" onClick={handleExplainLayout}>
                    Retry
                  </button>
                </div>
              )}

              {aiExplanation && (
                <div className="rg-ai-content">
                  {aiExplanation.status === 'fallback' && (
                    <div className="rg-badge rg-badge--warning" style={{ marginBottom: '14px', display: 'inline-block' }}>
                      Deterministic Fallback Mode ({aiExplanation.model_used})
                    </div>
                  )}

                  {/* Summary */}
                  <div className="rg-ai-summary-box">
                    <strong>Overview:</strong> {aiExplanation.summary}
                  </div>

                  {/* Design Reasoning */}
                  <div className="rg-ai-block">
                    <h4>Architectural Rationale &amp; Space Optimization</h4>
                    <p>{aiExplanation.design_reasoning}</p>
                  </div>

                  {/* Arrangement Tips */}
                  {aiExplanation.arrangement_tips.length > 0 && (
                    <div className="rg-ai-block">
                      <h4>Physical Installation &amp; Transit Tips</h4>
                      <ul className="rg-ai-list">
                        {aiExplanation.arrangement_tips.map((tip, idx) => (
                          <li key={idx}>{tip}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Trade-offs & Clearance */}
                  {aiExplanation.trade_offs.length > 0 && (
                    <div className="rg-ai-block">
                      <h4>Spatial Considerations &amp; Trade-offs</h4>
                      <ul className="rg-ai-list">
                        {aiExplanation.trade_offs.map((to, idx) => (
                          <li key={idx}>{to}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Meta Muse Spark Reasoning Trace Accordion */}
                  {aiExplanation.reasoning_content && (
                    <div className="rg-reasoning-trace">
                      <button
                        type="button"
                        className="rg-btn-text"
                        onClick={() => setShowReasoningTrace(!showReasoningTrace)}
                      >
                        {showReasoningTrace
                          ? '▼ Hide Reasoning Trace'
                          : '▶ View Meta AI Reasoning Trace'}
                      </button>
                      {showReasoningTrace && (
                        <pre className="rg-reasoning-pre">
                          {aiExplanation.reasoning_content}
                        </pre>
                      )}
                    </div>
                  )}

                  <div className="rg-ai-footer">
                    <small>
                      Model: <code>{aiExplanation.model_used}</code> · Deterministic geometry locked
                    </small>
                  </div>
                </div>
              )}
            </div>

            {/* ── AREA C: Meta Muse Image 1.0 Interior Redesign ──────────── */}
            <div
              className="rg-result-block"
              id="area-c-muse-image"
              style={{ marginTop: '48px', paddingTop: '36px', borderTop: '1px solid var(--rg-sand)' }}
            >
              <div className="rg-result-badge-row">
                <span className="rg-area-tag rg-area-tag--image">Area C · Visual Redesign Preview</span>
                <span className="rg-model-tag">Meta Muse Image 1.0</span>
              </div>
              <ImagePreviewModal
                roomWidth={layoutResult.summary.room_width_cm}
                roomLength={layoutResult.summary.room_length_cm}
                style={style}
                placedItems={layoutResult.placed_items}
              />
            </div>

            {/* Action Bar */}
            <div className="rg-results-actions" style={{ marginTop: '36px', display: 'flex', justifyContent: 'center' }}>
              <button
                type="button"
                className="rg-btn rg-btn--secondary"
                onClick={() => {
                  const el = document.getElementById('studio')
                  if (el) el.scrollIntoView({ behavior: 'smooth' })
                }}
              >
                ↑ Back to Studio Controls
              </button>
            </div>
          </section>
        )
      })()}
      </main>

      <FooterSection />
    </div>
  )
}
