import React from 'react'

export interface PlacedFurniture {
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

interface RoomVisualizerProps {
  roomWidth: number
  roomLength: number
  items: PlacedFurniture[]
  selectedId: string | null
  hoveredId?: string | null
  onSelectItem: (id: string | null) => void
  onHoverItem?: (id: string | null) => void
}

/** Assign a consistent visual theme based on furniture type keyword. */
function getCategoryTheme(name: string): { stroke: string; fill: string; text: string; label: string } {
  const lower = name.toLowerCase()
  if (lower.includes('bed') || lower.includes('cot') || lower.includes('mattress')) {
    return { stroke: '#4f46e5', fill: '#e0e7ff', text: '#312e81', label: 'Sleeping' }
  }
  if (lower.includes('sofa') || lower.includes('chair') || lower.includes('couch') || lower.includes('bench')) {
    return { stroke: '#2563eb', fill: '#dbeafe', text: '#1e3a8a', label: 'Seating' }
  }
  if (lower.includes('desk') || lower.includes('table') || lower.includes('stand')) {
    return { stroke: '#d97706', fill: '#fef3c7', text: '#78350f', label: 'Work/Dining' }
  }
  if (lower.includes('wardrobe') || lower.includes('closet') || lower.includes('shelf') || lower.includes('cabinet') || lower.includes('drawer')) {
    return { stroke: '#059669', fill: '#d1fae5', text: '#064e3b', label: 'Storage' }
  }
  return { stroke: '#475569', fill: '#f1f5f9', text: '#1e293b', label: 'General' }
}

export const RoomVisualizer: React.FC<RoomVisualizerProps> = ({
  roomWidth,
  roomLength,
  items,
  selectedId,
  hoveredId = null,
  onSelectItem,
  onHoverItem,
}) => {
  // Defensive fallbacks (use actual room dimensions; fallback to 100 only if missing/non-positive)
  const W = roomWidth > 0 ? roomWidth : 100
  const L = roomLength > 0 ? roomLength : 100

  // Dynamic scale factor relative to a standard 500 cm reference room
  // Ensures labels, arrows, and padding remain readable on large rooms up to 2000 cm
  const S = Math.max(1, Math.max(W, L) / 500)

  // Margin around the room boundary for dimension callouts & labels
  const PADDING = 45 * S
  const viewBoxWidth = W + PADDING * 2
  const viewBoxHeight = L + PADDING * 2

  return (
    <div className="rg-visualizer-container">
      <svg
        className="rg-visualizer-svg"
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        preserveAspectRatio="xMidYMid meet"
        role="group"
        aria-label={`2D Floorplan showing a ${W} by ${L} cm room with ${items.length} placed furniture items`}
      >
        <defs>
          {/* Subtle grid pattern for floor interior */}
          <pattern id="floor-grid" width={20 * S} height={20 * S} patternUnits="userSpaceOnUse">
            <path d={`M ${20 * S} 0 L 0 0 0 ${20 * S}`} fill="none" stroke="#f1f5f9" strokeWidth={0.8 * S} />
          </pattern>
          {/* Dimension arrow markers */}
          <marker id="arrow-start" viewBox="0 0 10 10" refX="5" refY="5" markerWidth={6 * S} markerHeight={6 * S} orient="auto-start-reverse">
            <path d="M 10 2 L 0 5 L 10 8 z" fill="#64748b" />
          </marker>
          <marker id="arrow-end" viewBox="0 0 10 10" refX="5" refY="5" markerWidth={6 * S} markerHeight={6 * S} orient="auto">
            <path d="M 0 2 L 10 5 L 0 8 z" fill="#64748b" />
          </marker>
        </defs>

        {/* ── Dimension Lines & Labels ──────────────────────────────── */}
        {/* Top dimension: Room Width */}
        <g className="rg-dim-top">
          <line
            x1={PADDING}
            y1={PADDING - 18 * S}
            x2={PADDING + W}
            y2={PADDING - 18 * S}
            stroke="#64748b"
            strokeWidth={1.2 * S}
            markerStart="url(#arrow-start)"
            markerEnd="url(#arrow-end)"
          />
          <text
            x={PADDING + W / 2}
            y={PADDING - 24 * S}
            textAnchor="middle"
            fill="#334155"
            fontSize={12 * S}
            fontWeight="600"
          >
            {W} cm
          </text>
        </g>

        {/* Left dimension: Room Length */}
        <g className="rg-dim-left">
          <line
            x1={PADDING - 18 * S}
            y1={PADDING}
            x2={PADDING - 18 * S}
            y2={PADDING + L}
            stroke="#64748b"
            strokeWidth={1.2 * S}
            markerStart="url(#arrow-start)"
            markerEnd="url(#arrow-end)"
          />
          <text
            x={PADDING - 24 * S}
            y={PADDING + L / 2}
            textAnchor="middle"
            fill="#334155"
            fontSize={12 * S}
            fontWeight="600"
            transform={`rotate(-90, ${PADDING - 24 * S}, ${PADDING + L / 2})`}
          >
            {L} cm
          </text>
        </g>

        {/* ── Room Boundary ─────────────────────────────────────────── */}
        {/* Floor interior with light grid */}
        <rect
          x={PADDING}
          y={PADDING}
          width={W}
          height={L}
          fill="#fafafa"
        />
        <rect
          x={PADDING}
          y={PADDING}
          width={W}
          height={L}
          fill="url(#floor-grid)"
        />

        {/* Outer wall boundary */}
        <rect
          x={PADDING}
          y={PADDING}
          width={W}
          height={L}
          fill="none"
          stroke="#1e293b"
          strokeWidth={3 * S}
          strokeLinejoin="round"
        />

        {/* Top-Left Origin Indicator */}
        <text
          x={PADDING + 6 * S}
          y={PADDING + 14 * S}
          fill="#94a3b8"
          fontSize={9 * S}
          fontFamily="monospace"
        >
          (0,0)
        </text>

        {/* ── Placed Furniture Items ─────────────────────────────────── */}
        {items.map(item => {
          if (item.x === undefined || item.y === undefined || item.width === undefined || item.length === undefined) {
            return null
          }

          const itemX = PADDING + item.x
          const itemY = PADDING + item.y
          const isSelected = selectedId === item.id
          const isHovered = hoveredId === item.id
          const isActive = isSelected || isHovered
          const theme = getCategoryTheme(item.name)

          // Thresholds scale with room dimension factor S for consistent legibility
          const showDetailedText = item.length >= 35 * S && item.width >= 45 * S
          const showMinimalText = item.length >= 20 * S && item.width >= 30 * S

          return (
            <g
              key={item.id}
              className={`rg-furniture-group ${isActive ? 'rg-furniture-selected' : ''}`}
              role="button"
              tabIndex={0}
              aria-pressed={isSelected}
              aria-label={`${item.name}, ${item.width} by ${item.length} cm at position ${item.x}, ${item.y}`}
              onClick={(e) => {
                e.stopPropagation()
                onSelectItem(isSelected ? null : item.id)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSelectItem(isSelected ? null : item.id)
                }
              }}
              onFocus={() => onHoverItem?.(item.id)}
              onBlur={() => onHoverItem?.(null)}
              onMouseEnter={() => onHoverItem?.(item.id)}
              onMouseLeave={() => onHoverItem?.(null)}
              style={{ cursor: 'pointer' }}
            >
              <title>{`${item.name} (${item.id})\nPosition: (${item.x}, ${item.y}) cm\nPlaced Size: ${item.width} × ${item.length} cm\nRotation: ${item.rotation}°`}</title>

              {/* Selection Halo */}
              {isActive && (
                <rect
                  x={itemX - 3 * S}
                  y={itemY - 3 * S}
                  width={item.width + 6 * S}
                  height={item.length + 6 * S}
                  fill="none"
                  stroke={isSelected ? '#2563eb' : '#3b82f6'}
                  strokeWidth={2.5 * S}
                  strokeDasharray={isSelected ? undefined : `${4 * S} ${2 * S}`}
                  rx={4 * S}
                />
              )}

              {/* Furniture Rectangle */}
              <rect
                x={itemX}
                y={itemY}
                width={item.width}
                height={item.length}
                fill={theme.fill}
                stroke={isActive ? '#2563eb' : theme.stroke}
                strokeWidth={isActive ? 2 * S : 1.5 * S}
                rx={2 * S}
              />

              {/* Rotation Indicator Badge (if rotated 90°) */}
              {item.rotation === 90 && (
                <g transform={`translate(${itemX + item.width - 18 * S}, ${itemY + 3 * S})`}>
                  <circle cx={7 * S} cy={7 * S} r={7 * S} fill="#3b82f6" />
                  <text x={7 * S} y={10.5 * S} textAnchor="middle" fill="#fff" fontSize={9 * S} fontWeight="bold">
                    ↻
                  </text>
                </g>
              )}

              {/* Text Label */}
              {showDetailedText ? (
                <>
                  <text
                    x={itemX + item.width / 2}
                    y={itemY + item.length / 2 - 3 * S}
                    textAnchor="middle"
                    fill={theme.text}
                    fontSize={11 * S}
                    fontWeight="600"
                    style={{ pointerEvents: 'none' }}
                  >
                    {item.name.length > 14 ? item.name.substring(0, 12) + '…' : item.name}
                  </text>
                  <text
                    x={itemX + item.width / 2}
                    y={itemY + item.length / 2 + 11 * S}
                    textAnchor="middle"
                    fill={theme.text}
                    fontSize={9 * S}
                    opacity="0.85"
                    style={{ pointerEvents: 'none' }}
                  >
                    {item.width}×{item.length}
                  </text>
                </>
              ) : showMinimalText ? (
                <text
                  x={itemX + item.width / 2}
                  y={itemY + item.length / 2 + 4 * S}
                  textAnchor="middle"
                  fill={theme.text}
                  fontSize={10 * S}
                  fontWeight="600"
                  style={{ pointerEvents: 'none' }}
                >
                  {item.name.length > 8 ? item.name.substring(0, 7) + '…' : item.name}
                </text>
              ) : null}
            </g>
          )
        })}
      </svg>

      {/* Legend & Category Key */}
      <div className="rg-visualizer-legend">
        <span className="rg-legend-item">
          <span className="rg-legend-color" style={{ background: '#e0e7ff', borderColor: '#4f46e5' }} />
          Sleeping
        </span>
        <span className="rg-legend-item">
          <span className="rg-legend-color" style={{ background: '#dbeafe', borderColor: '#2563eb' }} />
          Seating
        </span>
        <span className="rg-legend-item">
          <span className="rg-legend-color" style={{ background: '#fef3c7', borderColor: '#d97706' }} />
          Table/Desk
        </span>
        <span className="rg-legend-item">
          <span className="rg-legend-color" style={{ background: '#d1fae5', borderColor: '#059669' }} />
          Storage
        </span>
        <span className="rg-legend-item">
          <span className="rg-legend-color" style={{ background: '#f1f5f9', borderColor: '#475569' }} />
          General
        </span>
        <span className="rg-legend-item">
          <span className="rg-legend-badge">↻</span> 90° Rotated
        </span>
      </div>
    </div>
  )
}

