const NAV_SECTIONS = [
  {
    header: 'OVERVIEW & MONITORING',
    items: [
      { id: 'overview', label: 'Overview', icon: '🏠' },
      { id: 'liveMonitor', label: 'Live Weather & Satellite', icon: '📡' },
      { id: 'districtGraph', label: 'District Spatial Risk Map', icon: '⚑' },
    ]
  },
  {
    header: 'CYCLONE TRACKING & IMAGERY',
    items: [
      { id: 'events', label: 'Cyclone Event Catalog', icon: '☁️' },
      { id: 'anomalies', label: 'Image Quality Control', icon: '⚠' },
    ]
  },
  {
    header: 'DISASTER MANAGEMENT & ADVISORY',
    items: [
      { id: 'advisory', label: 'AI Disaster Advisory', icon: '⚡' },
      { id: 'whatif', label: 'What-If Scenario Simulator', icon: '🧪' },
      { id: 'resources', label: 'Evacuation & Shelter Allocator', icon: '🏗️' },
    ]
  },
  {
    header: 'AI ASSISTANT & EXPLAINABILITY',
    items: [
      { id: 'shap', label: 'Risk Driver Breakdown', icon: '🔍' },
      { id: 'assistant', label: 'Disaster Knowledge Assistant', icon: '◈' },
    ]
  },
  {
    header: 'PROJECT & SYSTEM EVALUATION',
    items: [
      { id: 'evaluation', label: 'System Evaluation & Roadmap', icon: '◔' },
    ]
  }
]

export default function Sidebar({ activeTab, onNavigateTab, phasesDone, phasesTotal }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">IC</div>
        <div>
          <div className="brand-name">IDMAP-Cyclone</div>
          <div className="brand-sub">Odisha intelligence</div>
        </div>
      </div>

      <nav style={{ overflowY: 'auto', flex: 1, paddingRight: '4px' }}>
        {NAV_SECTIONS.map((sec, idx) => (
          <div className="nav-section" key={idx} style={{ marginBottom: '14px' }}>
            <div className="nav-section-label" style={{ fontSize: '0.68rem', letterSpacing: '0.05em', color: '#64748b', fontWeight: 700, marginBottom: '4px' }}>
              {sec.header}
            </div>
            {sec.items.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => onNavigateTab(item.id)}
                style={{ fontSize: '0.85rem', padding: '7px 10px' }}
              >
                <span className="nav-icon" style={{ fontSize: '1rem' }}>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="progress-label">
          Project Roadmap <strong>{phasesDone}/{phasesTotal}</strong>
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${phasesTotal ? (phasesDone / phasesTotal) * 100 : 0}%` }}
          />
        </div>
      </div>
    </aside>
  )
}


