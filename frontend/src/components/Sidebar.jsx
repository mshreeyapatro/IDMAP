const NAV_SECTIONS = [
  {
    header: 'COMMAND & FORECASTING',
    items: [
      { id: 'forecast', label: 'Cyclone Command & Forecast', icon: '🎯' },
      { id: 'liveMonitor', label: 'Live Weather & Satellite', icon: '📡' },
      { id: 'districtGraph', label: 'District Spatial Risk Map', icon: '⚑' },
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
      { id: 'assistant', label: 'Disaster Knowledge Assistant', icon: '🤖' },
      { id: 'shap', label: 'Risk Driver Breakdown', icon: '🔍' },
    ]
  }
]

export default function Sidebar({
  activeTab,
  onNavigateTab,
  phasesDone,
  phasesTotal,
  telemetryMode = 'simulated',
  onToggleTelemetryMode,
  collapsed = false,
  onToggleCollapse
}) {
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="brand">
        <div className="brand-left">
          <div className="brand-mark" title="IDMAP-Cyclone">IC</div>
          {!collapsed && (
            <div>
              <div className="brand-name">IDMAP-Cyclone</div>
              <div className="brand-sub">Odisha intelligence</div>
            </div>
          )}
        </div>
        <button
          className="sidebar-collapse-btn"
          onClick={onToggleCollapse}
          title={collapsed ? "Expand sidebar for full labels" : "Collapse sidebar to widen dashboard"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? '❯' : '❮'}
        </button>
      </div>

      {/* Operational Telemetry Mode Toggle Card */}
      {!collapsed ? (
        <div style={{
          margin: '0 0 14px 0',
          padding: '9px 10px',
          borderRadius: '8px',
          background: telemetryMode === 'simulated' ? '#fef2f2' : '#f0fdf4',
          border: `1px solid ${telemetryMode === 'simulated' ? '#fecaca' : '#bbf7d0'}`,
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <span style={{
              fontSize: '0.64rem',
              fontWeight: 800,
              letterSpacing: '0.04em',
              color: telemetryMode === 'simulated' ? '#b91c1c' : '#15803d'
            }}>
              {telemetryMode === 'simulated' ? '🔴 CYCLONE DRILL' : '🟢 LIVE REAL-TIME'}
            </span>
            <span style={{ fontSize: '0.60rem', color: '#64748b', fontWeight: 700 }}>TELEMETRY</span>
          </div>
          <p style={{ margin: '0 0 6px', fontSize: '0.70rem', color: telemetryMode === 'simulated' ? '#991b1b' : '#166534', lineHeight: 1.25 }}>
            {telemetryMode === 'simulated' ? 'VSCS Ganjam strike scenario active for disaster drills.' : 'Live IMD / Open-Meteo feed (Bay of Bengal is calm).'}
          </p>
          <button
            onClick={onToggleTelemetryMode}
            style={{
              width: '100%',
              padding: '5px 8px',
              borderRadius: '5px',
              border: 'none',
              background: telemetryMode === 'simulated' ? '#dc2626' : '#16a34a',
              color: '#ffffff',
              fontSize: '0.70rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
              transition: 'background 0.15s'
            }}
            title={telemetryMode === 'simulated' ? 'Switch to live real-time ambient weather' : 'Switch to Category VSCS cyclone simulation drill'}
          >
            <span>🔄</span>
            <span>{telemetryMode === 'simulated' ? 'Switch to Live Ingest' : 'Switch to Cyclone Drill'}</span>
          </button>
        </div>
      ) : (
        <button
          onClick={onToggleTelemetryMode}
          style={{
            margin: '0 auto 12px',
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            border: `1px solid ${telemetryMode === 'simulated' ? '#fecaca' : '#bbf7d0'}`,
            background: telemetryMode === 'simulated' ? '#fef2f2' : '#f0fdf4',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1rem',
            transition: 'transform 0.15s ease'
          }}
          title={telemetryMode === 'simulated' ? '🔴 Cyclone Drill Active (Click to switch to Live Real-Time)' : '🟢 Live Real-Time Ingest Active (Click to switch to Cyclone Drill)'}
        >
          {telemetryMode === 'simulated' ? '🔴' : '🟢'}
        </button>
      )}

      <nav style={{ overflowY: 'auto', flex: 1, paddingRight: collapsed ? '0' : '4px' }}>
        {NAV_SECTIONS.map((sec, idx) => (
          <div className="nav-section" key={idx}>
            {!collapsed && (
              <div className="nav-section-label">
                {sec.header}
              </div>
            )}
            {sec.items.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => onNavigateTab(item.id)}
                title={collapsed ? item.label : undefined}
              >
                <span className="nav-icon">{item.icon}</span>
                {!collapsed && <span className="nav-label">{item.label}</span>}
              </button>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        {!collapsed ? (
          phasesTotal > 0 ? (
            <>
              <div className="progress-label">
                Operational Systems <strong>{phasesDone}/{phasesTotal}</strong>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${(phasesDone / phasesTotal) * 100}%` }}
                />
              </div>
            </>
          ) : (
            <div style={{ fontSize: '0.74rem', color: '#16a34a', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e', display: 'inline-block' }}></span>
              OSDMA Live AI Command Active
            </div>
          )
        ) : (
          <div
            style={{
              textAlign: 'center',
              fontSize: '0.65rem',
              fontWeight: 800,
              color: 'var(--text-dim)',
              padding: '6px 0',
              borderTop: '1px solid var(--border)'
            }}
            title={phasesTotal > 0 ? `Systems Active: ${phasesDone}/${phasesTotal}` : 'OSDMA Active'}
          >
            {phasesTotal > 0 ? `${phasesDone}/${phasesTotal}` : '●'}
          </div>
        )}
      </div>
    </aside>
  )
}


