const STATUS_COLORS = {
  done: 'var(--ok)',
  partial: 'var(--warn)',
  blocked: 'var(--danger)',
  'in progress': 'var(--accent)',
  'not started': 'var(--text-dim)',
}

export default function StatusBadge({ status }) {
  const color = STATUS_COLORS[status] ?? 'var(--text-dim)'
  return (
    <span className="badge" style={{ '--badge-color': color }}>
      {status}
    </span>
  )
}
