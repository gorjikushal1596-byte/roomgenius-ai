interface StudioWorkflowProgressProps {
  hasValidDimensions: boolean
  hasValidFurniture: boolean
  hasPhotoAnalysis: boolean
  hasStyleSelected: boolean
  hasLayoutResult: boolean
  hasAiResults: boolean
  onStepClick: (stepId: string) => void
}

interface StepItem {
  id: string
  number: number
  label: string
  shortLabel: string
  isComplete: boolean
  isActive: boolean
  targetAnchor: string
}

export function StudioWorkflowProgress({
  hasValidDimensions,
  hasValidFurniture,
  hasPhotoAnalysis,
  hasStyleSelected,
  hasLayoutResult,
  hasAiResults,
  onStepClick,
}: StudioWorkflowProgressProps) {
  // Determine current active step (first non-complete step, or last step if all complete)
  let activeStepNum = 1
  if (!hasValidDimensions) activeStepNum = 1
  else if (!hasValidFurniture) activeStepNum = 2
  else if (!hasLayoutResult) activeStepNum = 5 // Ready to optimize
  else if (!hasAiResults) activeStepNum = 6 // Results ready, AI exploration next
  else activeStepNum = 6

  const steps: StepItem[] = [
    {
      id: 'step-dimensions',
      number: 1,
      label: 'Room Dimensions',
      shortLabel: 'Dimensions',
      isComplete: hasValidDimensions,
      isActive: activeStepNum === 1,
      targetAnchor: 'room-dimensions-card',
    },
    {
      id: 'step-furniture',
      number: 2,
      label: 'Furniture Items',
      shortLabel: 'Furniture',
      isComplete: hasValidFurniture,
      isActive: activeStepNum === 2,
      targetAnchor: 'furniture-list-heading',
    },
    {
      id: 'step-photo',
      number: 3,
      label: 'Photo Perception',
      shortLabel: 'Vision (Optional)',
      isComplete: hasPhotoAnalysis,
      isActive: activeStepNum === 3,
      targetAnchor: 'vision-scanner-card',
    },
    {
      id: 'step-style',
      number: 4,
      label: 'Aesthetic Style',
      shortLabel: 'Preferences',
      isComplete: hasStyleSelected,
      isActive: activeStepNum === 4,
      targetAnchor: 'preferences-heading',
    },
    {
      id: 'step-optimize',
      number: 5,
      label: 'Layout Optimization',
      shortLabel: 'Optimization',
      isComplete: hasLayoutResult,
      isActive: activeStepNum === 5,
      targetAnchor: 'submit-layout-btn',
    },
    {
      id: 'step-results',
      number: 6,
      label: 'AI & Geometry Results',
      shortLabel: 'Results',
      isComplete: hasAiResults,
      isActive: activeStepNum === 6,
      targetAnchor: 'deterministic-results-area',
    },
  ]

  return (
    <div className="rg-progress-container" aria-label="Studio Workflow Progress">
      <div className="rg-progress-track">
        {steps.map((step, idx) => {
          const statusClass = step.isComplete
            ? 'rg-step--complete'
            : step.isActive
            ? 'rg-step--active'
            : 'rg-step--pending'

          return (
            <div key={step.id} className={`rg-progress-step ${statusClass}`}>
              <button
                type="button"
                className="rg-step-button"
                onClick={() => onStepClick(step.targetAnchor)}
                title={`Go to ${step.label}`}
                aria-current={step.isActive ? 'step' : undefined}
              >
                <span className="rg-step-bubble">
                  {step.isComplete ? '✓' : step.number}
                </span>
                <span className="rg-step-name">
                  <span className="rg-step-name-full">{step.label}</span>
                  <span className="rg-step-name-short">{step.shortLabel}</span>
                </span>
              </button>
              {idx < steps.length - 1 && <span className="rg-step-connector" />}
            </div>
          )
        })}
      </div>
    </div>
  )
}

