export default function BlockedView({ title, description, needed, phase }) {
  return (
    <div>
      <div className="view-header">
        <h1>{title}</h1>
        <p className="view-subtitle">{description}</p>
      </div>
      <div className="blocked-card">
        <span className="badge" style={{ '--badge-color': 'var(--danger)' }}>blocked</span>
        <p className="blocked-text">
          {phase && <>Phase {phase} in the SRS roadmap. </>}
          Not available yet -- needs: <strong>{needed}</strong>.
        </p>
        <p className="blocked-text muted">
          This module is part of the intended IDMAP-Cyclone dashboard (SRS §16) but is shown
          here honestly as unavailable rather than filled with placeholder numbers, per the
          project's rule against presenting synthetic data as real.
        </p>
      </div>
    </div>
  )
}
