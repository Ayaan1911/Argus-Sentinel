/**
 * StatusBadge - Simple dot and text status indicator
 */
export default function StatusBadge({ status, dot = true }) {
  const norm = (status || 'queued').toLowerCase()
  
  let colorClass = 'text-muted'
  if (norm === 'complete' || norm === 'completed') colorClass = 'text-green'
  else if (norm === 'running') colorClass = 'text-orange'
  else if (norm === 'failed') colorClass = 'text-red'

  return (
    <div className={`inline-flex items-center gap-1.5 text-[13px] font-medium capitalize ${colorClass}`}>
      {dot && <span className="text-[10px]">●</span>}
      {norm}
    </div>
  )
}
