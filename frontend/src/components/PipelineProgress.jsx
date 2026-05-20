/**
 * PipelineProgress — Horizontal 8-stage scan pipeline progress indicator.
 * Props:
 *   currentStage: string (key or partial label of the active stage)
 *   status: 'queued' | 'running' | 'complete' | 'failed'
 */

const STAGES = [
  { key: 'subdomain_enum',  label: 'Subdomain Enum', icon: '🔍' },
  { key: 'live_host_check', label: 'Live Hosts',      icon: '💓' },
  { key: 'port_scan',       label: 'Port Scan',       icon: '🔌' },
  { key: 'js_extractor',    label: 'JS Extract',      icon: '📜' },
  { key: 'secret_detector', label: 'Secrets',         icon: '🔑' },
  { key: 'endpoint_miner',  label: 'Endpoints',       icon: '🗺️' },
  { key: 'takeover_check',  label: 'Takeover',        icon: '⚠️' },
  { key: 'ai_summary',      label: 'AI Summary',      icon: '🤖' },
]

function getActiveIndex(currentStage, status) {
  if (!currentStage) {
    if (status === 'complete' || status === 'completed') return STAGES.length
    return -1
  }
  const lower = currentStage.toLowerCase().trim()

  // Try exact key match first
  let idx = STAGES.findIndex((s) => s.key === lower)
  if (idx !== -1) return idx

  // Try partial key match
  idx = STAGES.findIndex((s) => lower.includes(s.key) || s.key.includes(lower))
  if (idx !== -1) return idx

  // Try partial label match
  idx = STAGES.findIndex((s) => lower.includes(s.label.toLowerCase()) || s.label.toLowerCase().includes(lower))
  if (idx !== -1) return idx

  // If status is complete, all done
  if (status === 'complete' || status === 'completed') return STAGES.length

  return -1
}

export default function PipelineProgress({ currentStage, status }) {
  const activeIdx = getActiveIndex(currentStage, status)
  const isFailed  = status === 'failed'
  const isComplete = status === 'complete' || status === 'completed'

  return (
    <div className="w-full py-4 px-2 animate-fade-in">
      {/* Stage row */}
      <div className="relative flex items-center">
        {/* Connector track (behind everything) */}
        <div className="absolute top-[18px] left-0 right-0 h-[2px] bg-[#222222] z-0" />

        {/* Green fill on connector */}
        <div
          className="absolute top-[18px] left-0 h-[2px] bg-[#00ff88] z-0 transition-all duration-700 ease-out"
          style={{
            width: isComplete
              ? '100%'
              : isFailed
              ? activeIdx <= 0 ? '0%' : `${((activeIdx) / (STAGES.length - 1)) * 100}%`
              : activeIdx <= 0
              ? '0%'
              : `${((activeIdx) / (STAGES.length - 1)) * 100}%`,
            boxShadow: '0 0 8px rgba(0,255,136,0.5)',
          }}
        />

        {/* Stages */}
        {STAGES.map((stage, idx) => {
          const isCompleted = isComplete || idx < activeIdx
          const isActive    = !isComplete && !isFailed && idx === activeIdx
          const isFail      = isFailed && idx === activeIdx

          return (
            <div
              key={stage.key}
              className="relative z-10 flex flex-col items-center flex-1"
            >
              {/* Circle */}
              <div
                className={`
                  w-9 h-9 rounded-full flex items-center justify-center text-sm
                  border-2 transition-all duration-300
                  ${isCompleted
                    ? 'bg-[#00ff88] border-[#00ff88] text-black shadow-[0_0_10px_rgba(0,255,136,0.5)]'
                    : isActive
                    ? 'bg-[#1a2a1a] border-[#ffcc00] text-[#ffcc00] shadow-[0_0_12px_rgba(255,204,0,0.4)] animate-pulse'
                    : isFail
                    ? 'bg-[#2a1010] border-[#ff4444] text-[#ff4444]'
                    : 'bg-[#111111] border-[#333333] text-[#555555]'
                  }
                `}
              >
                {isCompleted ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : isFail ? (
                  <span className="text-xs">✕</span>
                ) : (
                  <span className="leading-none">{stage.icon}</span>
                )}
              </div>

              {/* Label */}
              <div
                className={`
                  mt-1.5 text-center text-[0.6rem] font-medium tracking-wide leading-tight
                  ${isCompleted
                    ? 'text-[#00ff88]'
                    : isActive
                    ? 'text-[#ffcc00]'
                    : isFail
                    ? 'text-[#ff4444]'
                    : 'text-[#444444]'
                  }
                `}
                style={{ maxWidth: '4rem' }}
              >
                {stage.label}
              </div>
            </div>
          )
        })}
      </div>

      {/* Status text */}
      <div className="mt-3 text-center text-[0.7rem] font-mono">
        {isComplete && (
          <span className="text-[#00ff88]">✓ All stages complete</span>
        )}
        {isFailed && (
          <span className="text-[#ff4444]">✗ Pipeline failed at: {currentStage || 'unknown'}</span>
        )}
        {status === 'running' && currentStage && (
          <span className="text-[#ffcc00]">
            ⟳ Running: <span className="font-bold">{currentStage}</span>
          </span>
        )}
        {status === 'queued' && (
          <span className="text-[#888888]">Scan queued — waiting to start...</span>
        )}
      </div>
    </div>
  )
}
