import { useState, useRef, useCallback, useEffect } from 'react'

interface BeforeAfterSliderProps {
  beforeImage?: string
  afterImage?: string
  beforeLabel?: string
  afterLabel?: string
}

export function BeforeAfterSlider({
  beforeImage = '/roomgenius-assets/cluttered-room.png',
  afterImage = '/roomgenius-assets/before-after.png',
  beforeLabel = 'Before: Spatial Guesswork',
  afterLabel = 'After: Deterministic Feasibility',
}: BeforeAfterSliderProps) {
  const [sliderPosition, setSliderPosition] = useState(50)
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = clientX - rect.left
    const percent = Math.max(0, Math.min(100, (x / rect.width) * 100))
    setSliderPosition(Number(percent.toFixed(1)))
  }, [])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length > 0) {
      handleMove(e.touches[0].clientX)
    }
  }, [handleMove])

  useEffect(() => {
    function handleGlobalMouseUp() {
      setIsDragging(false)
    }
    function handleGlobalMouseMove(e: MouseEvent) {
      if (isDragging) {
        handleMove(e.clientX)
      }
    }

    if (isDragging) {
      window.addEventListener('mousemove', handleGlobalMouseMove)
      window.addEventListener('mouseup', handleGlobalMouseUp)
    }
    return () => {
      window.removeEventListener('mousemove', handleGlobalMouseMove)
      window.removeEventListener('mouseup', handleGlobalMouseUp)
    }
  }, [isDragging, handleMove])

  return (
    <div className="rg-ba-wrapper">
      <div
        ref={containerRef}
        className="rg-ba-container"
        onMouseDown={(e) => {
          setIsDragging(true)
          handleMove(e.clientX)
        }}
        onTouchMove={handleTouchMove}
      >
        {/* Underneath: Before Image */}
        <div className="rg-ba-layer rg-ba-layer--before">
          <img
            src={beforeImage}
            alt={beforeLabel}
            className="rg-ba-img"
            loading="lazy"
          />
          <span className="rg-ba-tag rg-ba-tag--left">{beforeLabel}</span>
        </div>

        {/* Top: After Image clipped by slider position */}
        <div
          className="rg-ba-layer rg-ba-layer--after"
          style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
        >
          <img
            src={afterImage}
            alt={afterLabel}
            className="rg-ba-img"
            loading="lazy"
          />
          <span className="rg-ba-tag rg-ba-tag--right">{afterLabel}</span>
        </div>

        {/* Divider Handle */}
        <div
          className="rg-ba-handle"
          style={{ left: `${sliderPosition}%` }}
        >
          <div className="rg-ba-handle-line" />
          <div className="rg-ba-handle-circle">
            <span className="rg-ba-arrows">⇄</span>
          </div>
        </div>
      </div>
      <p className="rg-ba-hint">Drag slider or tap across the image to compare Before & After</p>
    </div>
  )
}

