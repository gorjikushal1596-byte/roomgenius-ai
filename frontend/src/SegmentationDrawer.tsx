import { useState, useRef } from 'react'

export interface DetectedItem {
  id: string
  label: string
  category: 'sleeping' | 'seating' | 'work' | 'storage' | 'other'
  confidence: number
  box: {
    ymin: number
    xmin: number
    ymax: number
    xmax: number
  }
  suggested_width_cm?: number
  suggested_length_cm?: number
  calibrated: boolean
}

export interface CalibratedFurnitureItem {
  id: string
  name: string
  width: string
  length: string
  height: string
}

interface SegmentationDrawerProps {
  onImportItems: (items: CalibratedFurnitureItem[]) => void
}

const CATEGORY_COLORS: Record<string, string> = {
  sleeping: '#4f46e5',
  seating: '#2563eb',
  work: '#d97706',
  storage: '#059669',
  other: '#64748b',
}

export function SegmentationDrawer({ onImportItems }: SegmentationDrawerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null)
  const [depthMapUrl, setDepthMapUrl] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'photo' | 'depth'>('photo')
  const [depthProfiles, setDepthProfiles] = useState<
    Record<string, { median_depth_m: number; relative_layer: string }>
  >({})
  const [isDepthLoading, setIsDepthLoading] = useState(false)
  const [detectedItems, setDetectedItems] = useState<DetectedItem[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [editingDimensions, setEditingDimensions] = useState<
    Record<string, { name: string; width: string; length: string; height: string }>
  >({})
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const [modelUsed, setModelUsed] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setStatus('error')
      setErrorMessage('Please upload a valid image file (JPEG, PNG, or WebP).')
      return
    }

    if (file.size > 5 * 1024 * 1024) {
      setStatus('error')
      setErrorMessage('Image size exceeds 5 MB. Please select a smaller photo.')
      return
    }

    const reader = new FileReader()
    reader.onload = async () => {
      const dataUri = reader.result as string
      setImagePreviewUrl(dataUri)
      setDepthMapUrl(null)
      setViewMode('photo')
      setDepthProfiles({})
      setStatus('analyzing')
      setErrorMessage('')

      try {
        const res = await fetch('http://localhost:8000/ai/segment-furniture', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_base64: dataUri,
            filename: file.name,
            mime_type: file.type,
          }),
        })

        if (!res.ok) {
          throw new Error(`Segmentation server returned HTTP ${res.status}`)
        }

        const data = await res.json()
        if (data.status === 'error') {
          throw new Error(data.message || 'Segmentation failed')
        }

        const items: DetectedItem[] = data.objects_detected || []
        setDetectedItems(items)
        setModelUsed(data.model_used || 'sam-3.1')
        setStatus('success')

        // Initialize editable dimensions and select all by default
        const initDims: Record<string, { name: string; width: string; length: string; height: string }> = {}
        const initSelected = new Set<string>()

        items.forEach((item, idx) => {
          const defaultW = item.suggested_width_cm ? String(item.suggested_width_cm) : '100'
          const defaultL = item.suggested_length_cm ? String(item.suggested_length_cm) : '100'
          initDims[item.id] = {
            name: `${item.label} ${idx + 1}`,
            width: defaultW,
            length: defaultL,
            height: '',
          }
          initSelected.add(item.id)
        })

        setEditingDimensions(initDims)
        setSelectedIds(initSelected)

        // Request Depth Anything V2 depth estimation in parallel
        setIsDepthLoading(true)
        try {
          const depthRes = await fetch('http://localhost:8000/ai/estimate-depth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image_base64: dataUri,
              filename: file.name,
              detected_boxes: items.map(it => it.box),
            }),
          })
          if (depthRes.ok) {
            const depthData = await depthRes.json()
            if (depthData.depth_map_data) {
              setDepthMapUrl(depthData.depth_map_data)
              const profilesMap: Record<string, { median_depth_m: number; relative_layer: string }> = {}
              depthData.object_depth_profiles?.forEach(
                (p: { median_depth_m: number; relative_layer: string }, idx: number) => {
                  if (items[idx]) {
                    profilesMap[items[idx].id] = {
                      median_depth_m: p.median_depth_m,
                      relative_layer: p.relative_layer,
                    }
                  }
                }
              )
              setDepthProfiles(profilesMap)
            }
          }
        } catch {
          // Graceful non-blocking degradation if depth service is offline
        } finally {
          setIsDepthLoading(false)
        }
      } catch (err: unknown) {
        setStatus('error')
        const msg = err instanceof Error ? err.message : 'Failed to connect to segmentation service'
        setErrorMessage(msg)
      }
    }

    reader.readAsDataURL(file)
  }

  function toggleItemSelection(id: string) {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function handleDimensionChange(id: string, field: 'name' | 'width' | 'length' | 'height', val: string) {
    setEditingDimensions(prev => ({
      ...prev,
      [id]: {
        ...prev[id],
        [field]: val,
      },
    }))
  }

  function handleImport() {
    const toImport: CalibratedFurnitureItem[] = []
    selectedIds.forEach(id => {
      const dim = editingDimensions[id]
      if (dim && Number(dim.width) > 0 && Number(dim.length) > 0) {
        toImport.push({
          id: `sam-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
          name: dim.name.trim() || 'Furniture Item',
          width: dim.width,
          length: dim.length,
          height: dim.height,
        })
      }
    })

    if (toImport.length === 0) {
      alert('Please select at least one item and confirm valid width and length dimensions (in cm).')
      return
    }

    onImportItems(toImport)
    setIsOpen(false)
  }

  return (
    <div className="rg-sam-card">
      <div className="rg-sam-header">
        <div className="rg-sam-title-wrap">
          <span className="rg-sam-icon">📷</span>
          <div>
            <h3>Auto-Detect Furniture with Meta SAM 3.1</h3>
            <p className="rg-sam-subtitle">
              Upload a room photo to automatically detect furniture boundaries. (Human-in-the-loop calibration required).
            </p>
          </div>
        </div>
        <button
          type="button"
          className="rg-btn rg-btn--secondary"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? '✕ Close Scanner' : '🔍 Scan Room Photo'}
        </button>
      </div>

      {isOpen && (
        <div className="rg-sam-body">
          <div className="rg-sam-upload-area">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              style={{ display: 'none' }}
              onChange={handleFileSelect}
            />
            <button
              type="button"
              className="rg-btn rg-btn--ai"
              onClick={() => fileInputRef.current?.click()}
              disabled={status === 'analyzing'}
            >
              {status === 'analyzing' ? '⏳ Segmenting Objects with SAM 3.1…' : '📁 Choose Room Photo (Max 5MB)'}
            </button>
            <span className="rg-sam-disclaimer">
              🔒 Images are processed locally or securely via Meta Model API. No metrics are hallucinated.
            </span>
          </div>

          {status === 'error' && (
            <div className="rg-toast rg-toast--error" style={{ marginTop: '12px' }}>
              <strong>Detection Error:</strong> {errorMessage}
            </div>
          )}

          {imagePreviewUrl && (
            <div className="rg-sam-preview-grid">
              {/* Photo with Bounding Box Overlay */}
              <div className="rg-sam-image-container">
                <div className="rg-sam-view-header">
                  <h4>Spatial & Depth Perception</h4>
                  <div className="rg-view-toggle">
                    <button
                      type="button"
                      className={`rg-btn-view-toggle ${viewMode === 'photo' ? 'rg-btn-view-toggle--active' : ''}`}
                      onClick={() => setViewMode('photo')}
                    >
                      📷 Photo
                    </button>
                    <button
                      type="button"
                      className={`rg-btn-view-toggle ${viewMode === 'depth' ? 'rg-btn-view-toggle--active' : ''}`}
                      onClick={() => setViewMode('depth')}
                      disabled={!depthMapUrl && !isDepthLoading}
                      title="Toggle Depth Anything V2 monocular depth visualization"
                    >
                      {isDepthLoading ? '⏳ Depth…' : '🗺️ Depth Heatmap'}
                    </button>
                  </div>
                </div>

                <div className="rg-sam-image-relative">
                  <img
                    src={viewMode === 'depth' && depthMapUrl ? depthMapUrl : imagePreviewUrl}
                    alt={viewMode === 'depth' ? 'Estimated Depth Map' : 'Uploaded Room'}
                    className="rg-sam-img"
                  />
                  <svg className="rg-sam-svg-overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
                    {detectedItems.map(item => {
                      const color = CATEGORY_COLORS[item.category] || '#64748b'
                      const isSelected = selectedIds.has(item.id)
                      const x = item.box.xmin * 100
                      const y = item.box.ymin * 100
                      const w = (item.box.xmax - item.box.xmin) * 100
                      const h = (item.box.ymax - item.box.ymin) * 100

                      return (
                        <g key={item.id} opacity={isSelected ? 1 : 0.4}>
                          <rect
                            x={x}
                            y={y}
                            width={w}
                            height={h}
                            fill={color}
                            fillOpacity="0.18"
                            stroke={color}
                            strokeWidth="1.2"
                            strokeDasharray={isSelected ? 'none' : '2,2'}
                          />
                          <text
                            x={x + 1}
                            y={Math.max(y - 1.5, 3)}
                            fill={color}
                            fontSize="3.5"
                            fontWeight="bold"
                            style={{ textShadow: '0 0 2px #fff' }}
                          >
                            {item.label} ({(item.confidence * 100).toFixed(0)}%)
                          </text>
                        </g>
                      )
                    })}
                  </svg>
                </div>
                <small className="rg-sam-tagline">
                  {viewMode === 'depth'
                    ? 'Depth Anything V2 Metric Indoor · Near: Light/Yellow → Far: Dark'
                    : `Segmented by ${modelUsed} · Bounding boxes projected from 2D coordinates`}
                </small>
              </div>

              {/* Staging Calibration Drawer */}
              <div className="rg-sam-staging-drawer">
                <div className="rg-sam-staging-header">
                  <h4>📏 Staging Drawer: Metric Calibration</h4>
                  <span className="rg-badge rg-badge--warning">User Confirmation Required</span>
                </div>
                <p className="rg-staging-note">
                  SAM 3.1 identifies <strong>what</strong> items are in the photo. Please verify or adjust the physical metric dimensions (cm) before adding them to your room floorplan:
                </p>

                <div className="rg-staging-items-list">
                  {detectedItems.map(item => {
                    const isSelected = selectedIds.has(item.id)
                    const dims = editingDimensions[item.id] || { name: item.label, width: '100', length: '100', height: '' }

                    return (
                      <div key={item.id} className={`rg-staging-item ${isSelected ? 'rg-staging-item--selected' : ''}`}>
                        <div className="rg-staging-item-top">
                          <label className="rg-checkbox-wrap">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleItemSelection(item.id)}
                            />
                            <strong>{item.label}</strong>
                          </label>
                          <div className="rg-staging-item-badges">
                            <span
                              className="rg-category-badge"
                              style={{
                                backgroundColor: `${CATEGORY_COLORS[item.category]}15`,
                                color: CATEGORY_COLORS[item.category],
                                borderColor: `${CATEGORY_COLORS[item.category]}40`,
                              }}
                            >
                              {item.category}
                            </span>
                            {depthProfiles[item.id] && (
                              <span
                                className={`rg-depth-layer-badge rg-depth-layer-badge--${depthProfiles[item.id].relative_layer}`}
                                title={`Depth Anything V2 metric estimate: ~${depthProfiles[item.id].median_depth_m}m from camera`}
                              >
                                ~{depthProfiles[item.id].median_depth_m}m · {depthProfiles[item.id].relative_layer}
                              </span>
                            )}
                          </div>
                        </div>

                        {isSelected && (
                          <div className="rg-staging-inputs">
                            <label className="rg-staging-field">
                              <span>Label</span>
                              <input
                                type="text"
                                value={dims.name}
                                onChange={e => handleDimensionChange(item.id, 'name', e.target.value)}
                              />
                            </label>
                            <label className="rg-staging-field">
                              <span>Width (cm) *</span>
                              <input
                                type="number"
                                min="1"
                                max="2000"
                                value={dims.width}
                                onChange={e => handleDimensionChange(item.id, 'width', e.target.value)}
                              />
                            </label>
                            <label className="rg-staging-field">
                              <span>Depth (cm) *</span>
                              <input
                                type="number"
                                min="1"
                                max="2000"
                                value={dims.length}
                                onChange={e => handleDimensionChange(item.id, 'length', e.target.value)}
                              />
                            </label>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>

                <div className="rg-staging-actions">
                  <button
                    type="button"
                    className="rg-btn rg-btn--primary"
                    onClick={handleImport}
                    disabled={selectedIds.size === 0}
                  >
                    📥 Add {selectedIds.size} Calibrated Item{selectedIds.size === 1 ? '' : 's'} to Room Inventory
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

