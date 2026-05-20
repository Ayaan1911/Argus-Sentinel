import { useEffect, useRef, useState } from 'react'

/**
 * MetricCard — Dashboard metric display card.
 * Props:
 *   icon: string (emoji or text symbol)
 *   label: string
 *   value: number | string
 *   variant: 'default' | 'danger' | 'warning'
 *   subtitle: optional string below value
 */
export default function MetricCard({ icon, label, value = 0, variant = 'default', subtitle }) {
  const [displayValue, setDisplayValue] = useState(0)
  const animRef = useRef(null)
  const numericValue = typeof value === 'number' ? value : parseInt(value, 10) || 0
  const isNumeric = typeof value === 'number' || !isNaN(parseInt(value, 10))

  // Animate number on mount / value change
  useEffect(() => {
    if (!isNumeric) {
      setDisplayValue(value)
      return
    }
    if (animRef.current) cancelAnimationFrame(animRef.current)

    const duration = 800
    const start = performance.now()
    const startVal = 0

    const step = (now) => {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplayValue(Math.round(startVal + (numericValue - startVal) * eased))
      if (progress < 1) {
        animRef.current = requestAnimationFrame(step)
      }
    }
    animRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(animRef.current)
  }, [numericValue, isNumeric, value])

  const isDanger  = variant === 'danger'
  const isWarning = variant === 'warning'
  const hasDangerGlow = isDanger && numericValue > 0

  const containerClasses = [
    'relative rounded-xl border p-5 transition-all duration-200 cursor-default group animate-slide-up',
    isDanger
      ? 'bg-[#150a0a] border-[rgba(255,68,68,0.25)] hover:border-[rgba(255,68,68,0.5)]'
      : isWarning
      ? 'bg-[#14120a] border-[rgba(255,204,0,0.2)] hover:border-[rgba(255,204,0,0.45)]'
      : 'bg-[#111111] border-[#222222] hover:border-[#333333]',
    hasDangerGlow ? 'shadow-[0_0_20px_rgba(255,68,68,0.15)]' : 'shadow-card',
    'hover:scale-[1.02] hover:shadow-lg',
  ].join(' ')

  const valueClasses = [
    'text-4xl font-bold font-mono transition-colors duration-200',
    isDanger  ? 'text-[#ff4444]' : '',
    isWarning ? 'text-[#ffcc00]' : '',
    !isDanger && !isWarning ? 'text-[#00ff88]' : '',
  ].join(' ')

  return (
    <div className={containerClasses}>
      {/* Top row: icon + label */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-2xl select-none" role="img" aria-hidden="true">
          {icon}
        </span>
        <span
          className={`text-[0.65rem] font-semibold tracking-widest uppercase ${
            isDanger ? 'text-[#ff4444]' : isWarning ? 'text-[#ffcc00]' : 'text-[#888888]'
          }`}
        >
          {label}
        </span>
      </div>

      {/* Value */}
      <div className={valueClasses}>
        {isNumeric ? displayValue.toLocaleString() : value}
      </div>

      {/* Optional subtitle */}
      {subtitle && (
        <div className="mt-1 text-xs text-[#555555]">{subtitle}</div>
      )}

      {/* Danger glow bar at bottom */}
      {hasDangerGlow && (
        <div className="absolute bottom-0 left-0 right-0 h-[2px] rounded-b-xl bg-gradient-to-r from-transparent via-[#ff4444] to-transparent opacity-60" />
      )}

      {/* Accent bar for default */}
      {!isDanger && !isWarning && (
        <div className="absolute bottom-0 left-0 right-0 h-[2px] rounded-b-xl bg-gradient-to-r from-transparent via-[#00ff88] to-transparent opacity-0 group-hover:opacity-40 transition-opacity duration-300" />
      )}
    </div>
  )
}
