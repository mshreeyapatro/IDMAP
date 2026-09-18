import { useEffect, useState } from 'react'
import { api } from '../api'

export default function ResourcePlanningView() {
  const [severity, setSeverity] = useState('High')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedDistrict, setSelectedDistrict] = useState('')

  useEffect(() => {
    setLoading(true)
    api.resources(selectedDistrict, severity)
      .then((res) => {
        setData(res)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [severity, selectedDistrict])

  return (
    <div className="view-container">
      <header className="view-header">
        <div>
          <h2>Emergency Resource & Shelter Planning</h2>
          <p className="subtitle">
            Evacuation target allocation, shelter requirements, and NDRF deployment planning powered by Census 2011 metadata.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginRight: '6px' }}>Cyclone Severity:</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                background: 'var(--bg-card)',
                color: 'var(--text-main)',
                border: '1px solid var(--border-color)'
              }}
            >
              <option value="Low">Low (Depression)</option>
              <option value="Moderate">Moderate (Cyclonic Storm)</option>
              <option value="High">High (Severe CS)</option>
              <option value="Extreme">Extreme (Super CS)</option>
            </select>
          </div>
        </div>
      </header>

      {loading && <div className="card loading">Calculating evacuation and shelter requirements...</div>}

      {data && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="grid-3">
            <div className="card metric-box">
              <span className="metric-label">Target Evacuation Population</span>
              <span className="metric-value" style={{ color: '#38bdf8' }}>
                {data.total_state_evacuation_target?.toLocaleString() || 'N/A'}
              </span>
            </div>
            <div className="card metric-box">
              <span className="metric-label">Multipurpose Shelters Needed</span>
              <span className="metric-value" style={{ color: '#f59e0b' }}>
                {data.total_multipurpose_shelters_required?.toLocaleString() || 'N/A'}
              </span>
            </div>
            <div className="card metric-box">
              <span className="metric-label">NDRF Teams Required</span>
              <span className="metric-value" style={{ color: '#a855f7' }}>
                {data.total_ndrf_teams_required?.toLocaleString() || 'N/A'}
              </span>
            </div>
          </div>

          <div className="card">
            <h3>Odisha District Resource Allocation Breakdown</h3>
            <div style={{ overflowX: 'auto', marginTop: '15px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-dim)' }}>
                    <th style={{ padding: '10px' }}>District</th>
                    <th style={{ padding: '10px' }}>Priority Tier</th>
                    <th style={{ padding: '10px' }}>Coastal Dist</th>
                    <th style={{ padding: '10px' }}>Total Pop</th>
                    <th style={{ padding: '10px' }}>Evac Target</th>
                    <th style={{ padding: '10px' }}>Shelters Needed</th>
                    <th style={{ padding: '10px' }}>NDRF Teams</th>
                  </tr>
                </thead>
                <tbody>
                  {data.district_breakdown?.map((d, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: '10px', fontWeight: 'bold' }}>{d.district}</td>
                      <td style={{ padding: '10px' }}>
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            background: d.priority_tier.includes('Critical')
                              ? 'rgba(239, 68, 68, 0.2)'
                              : (d.priority_tier.includes('High') ? 'rgba(245, 158, 11, 0.2)' : 'rgba(52, 211, 153, 0.2)'),
                            color: d.priority_tier.includes('Critical')
                              ? '#f87171'
                              : (d.priority_tier.includes('High') ? '#f59e0b' : '#34d399')
                          }}
                        >
                          {d.priority_tier}
                        </span>
                      </td>
                      <td style={{ padding: '10px' }}>{d.coastal_distance_km} km</td>
                      <td style={{ padding: '10px' }}>{d.total_population.toLocaleString()}</td>
                      <td style={{ padding: '10px', color: '#38bdf8', fontWeight: 'bold' }}>
                        {d.people_to_evacuate.toLocaleString()} ({d.evacuation_target_pct}%)
                      </td>
                      <td style={{ padding: '10px' }}>{d.multipurpose_shelters_required}</td>
                      <td style={{ padding: '10px' }}>{d.ndrf_teams_required}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
