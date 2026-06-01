import { useEffect, useRef, useState } from 'react'

/**
 * MetricCard — Dashboard metric display card.
 */
export default function MetricCard({ icon, label, value = 0, variant = 'default', subtitle }) {
  const [displayValue, setDisplayValue] = useState(0)
  const animRef = useRef(null)
  const numericValue = typeof value === 'number' ? value : parseInt(value, 10) || 0
  const isNumeric = typeof value === 'number' || !isNaN(parseInt(value, 10))

  useEffect(() => {
    if (!isNumeric) {
      setDisplayValue(value)
      return
    }
    if (animRef.current) cancelAnimationFrame(animRef.current)

    const duration = 600
    const start = performance.now()
    const startVal = 0

    const step = (now) => {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplayValue(Math.round(startVal + (numericValue - startVal) * eased))
      if (progress < 1) {
        animRef.current = requestAnimationFrame(step)
      }
    }
    animRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(animRef.current)
  }, [numericValue, isNumeric, value])

  const isDanger = variant === 'danger'
  
  const containerClasses = [
    'flex flex-col justify-between bg-bg-surface border p-[20px] rounded-[6px] transition-colors',
    isDanger ? 'border-red' : 'border-border hover:border-border-active'
  ].join(' ')

  return (
    <div className={containerClasses}>
      {/* Top row: icon + label */}
      <div className="flex items-center gap-2 mb-3">
        {icon && (
          <span className="text-sm opacity-70 select-none" role="img" aria-hidden="true">
            {icon}
          </span>
        )}
        <span className="text-[11px] uppercase tracking-[0.08em] font-medium text-text-secondary">
          {label}
        </span>
      </div>

      {/* Value */}
      <div className="text-[32px] font-bold leading-tight text-text-primary">
        {isNumeric ? displayValue.toLocaleString() : value}
      </div>

      {/* Optional subtitle */}
      {subtitle && (
        <div className="mt-2 text-xs text-text-secondary">{subtitle}</div>
      )}
    </div>
  )
}
