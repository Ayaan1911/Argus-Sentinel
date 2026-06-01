/**
 * PipelineProgress — Linear-style horizontal pipeline progress.
 */

const STAGES = [
  { key: 'subdomain_enum',     label: 'Subdomains' },
  { key: 'live_host_check',    label: 'Live Hosts' },
  { key: 'screenshot_capture', label: 'Screenshots' },
  { key: 'port_scan',          label: 'Port Scan' },
  { key: 'js_extractor',       label: 'JS Extract' },
  { key: 'secret_detector',    label: 'Secrets' },
  { key: 'endpoint_miner',     label: 'Endpoints' },
  { key: 'takeover_check',     label: 'Takeover' },
  { key: 'nuclei_scan',        label: 'Nuclei Scan' },
  { key: 'ai_summary',         label: 'AI Summary' },
]

function getActiveIndex(currentStage, status) {
  if (!currentStage) {
    if (status === 'complete' || status === 'completed') return STAGES.length
    return -1
  }
  const lower = currentStage.toLowerCase().trim()

  let idx = STAGES.findIndex((s) => s.key === lower)
  if (idx !== -1) return idx

  idx = STAGES.findIndex((s) => lower.includes(s.key) || s.key.includes(lower))
  if (idx !== -1) return idx

  idx = STAGES.findIndex((s) => lower.includes(s.label.toLowerCase()) || s.label.toLowerCase().includes(lower))
  if (idx !== -1) return idx

  if (status === 'complete' || status === 'completed') return STAGES.length
  return -1
}

export default function PipelineProgress({ currentStage, status }) {
  const activeIdx  = getActiveIndex(currentStage, status)
  const isFailed   = status === 'failed'
  const isComplete = status === 'complete' || status === 'completed'

  return (
    <div className="w-full py-4 px-2">
      <div className="relative flex items-center justify-between">
        {/* Connector line background */}
        <div className="absolute top-[6px] left-[20px] right-[20px] h-[1px] bg-border z-0" />
        
        {/* Connector line active */}
        <div 
          className="absolute top-[6px] left-[20px] h-[1px] bg-green z-0 transition-all duration-500 ease-out"
          style={{
            width: isComplete
              ? 'calc(100% - 40px)'
              : isFailed
              ? activeIdx <= 0 ? '0%' : `calc(${((activeIdx) / (STAGES.length - 1)) * 100}% - 40px)`
              : activeIdx <= 0
              ? '0%'
              : `calc(${((activeIdx) / (STAGES.length - 1)) * 100}% - 40px)`
          }}
        />

        {STAGES.map((stage, idx) => {
          const isCompleted = isComplete || idx < activeIdx
          const isActive    = !isComplete && !isFailed && idx === activeIdx
          const isFail      = isFailed && idx === activeIdx

          let circleClass = 'bg-border'
          let labelClass = 'text-text-muted'

          if (isCompleted) {
            circleClass = 'bg-green'
            labelClass = 'text-text-secondary'
          } else if (isActive) {
            circleClass = 'bg-orange animate-pulse-subtle'
            labelClass = 'text-text-primary font-medium'
          } else if (isFail) {
            circleClass = 'bg-red'
            labelClass = 'text-red'
          }

          return (
            <div key={stage.key} className="relative z-10 flex flex-col items-center group w-[60px]">
              {/* Circle (12px) */}
              <div className={`w-[12px] h-[12px] rounded-full flex-shrink-0 transition-colors duration-300 ${circleClass}`} />
              
              {/* Label */}
              <div className={`mt-3 text-[11px] text-center transition-colors duration-300 ${labelClass}`}>
                {stage.label}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
