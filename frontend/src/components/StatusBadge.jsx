/**
 * StatusBadge — Colored status indicator pill.
 * Props:
 *   status: 'queued' | 'running' | 'complete' | 'failed'
 *   dot: boolean — show pulsing dot before text
 *   className: optional extra classes
 */
export default function StatusBadge({ status = 'queued', dot = false, className = '' }) {
  const normalized = (status || 'queued').toLowerCase()

  const config = {
    queued: {
      bg: 'bg-gray-800',
      text: 'text-gray-400',
      border: 'border-gray-700',
      dotColor: 'bg-gray-500',
      pulse: false,
      label: 'QUEUED',
    },
    running: {
      bg: 'bg-yellow-950',
      text: 'text-yellow-400',
      border: 'border-yellow-900',
      dotColor: 'bg-yellow-400',
      pulse: true,
      label: 'RUNNING',
    },
    complete: {
      bg: 'bg-emerald-950',
      text: 'text-emerald-400',
      border: 'border-emerald-900',
      dotColor: 'bg-emerald-400',
      pulse: false,
      label: 'COMPLETE',
    },
    completed: {
      bg: 'bg-emerald-950',
      text: 'text-emerald-400',
      border: 'border-emerald-900',
      dotColor: 'bg-emerald-400',
      pulse: false,
      label: 'COMPLETE',
    },
    failed: {
      bg: 'bg-red-950',
      text: 'text-red-400',
      border: 'border-red-900',
      dotColor: 'bg-red-400',
      pulse: false,
      label: 'FAILED',
    },
  }

  const style = config[normalized] ?? config.queued

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
        text-[0.65rem] font-bold tracking-widest uppercase
        border ${style.bg} ${style.text} ${style.border} ${className}
      `}
    >
      {dot && (
        <span
          className={`
            inline-block w-1.5 h-1.5 rounded-full flex-shrink-0
            ${style.dotColor}
            ${style.pulse ? 'animate-pulse' : ''}
          `}
        />
      )}
      {style.label}
    </span>
  )
}
