import { useEffect, useState } from 'react'
import { api } from '../api'

export default function WhatIfView() {
  const [events, setEvents] = useState([])
  const [selectedBaseId, setSelectedBaseId] = useState(25)
  const [deltaWind, setDeltaWind] = useState(15)
  const [coastalDist, setCoastalDist] = useState(80)
  const [simulation, setSimulation] = useState(null)
  const [shapShifts, setShapShifts] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.events().then((res) => {
      setEvents(res || [])
      if (res && res.length > 0) {
        setSelectedBaseId(res[0].cyclone_id)
      }
    }).catch(() => {})
  }, [])

  const runSimulation = () => {
    if (!selectedBaseId) return
    setLoading(true)
    api.whatif(selectedBaseId, deltaWind, coastalDist)
      .then((data) => {
        setSimulation(data)
        setLoading(false)

        const simWind = data.simulation?.simulated_wind_speed_kt || 60.0
        api.explainLive({
          wind_speed_kt: simWind,
          coastal_distance_km: coastalDist,
          pressure_hpa: 995.0,
          district_population: 1250000.0
        }).then(setShapShifts).catch(() => {})
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    runSimulation()
  }, [selectedBaseId, deltaWind, coastalDist])

  return (
    <div className="view-container">
      <header className="view-header">
        <div>
          <h2>What-If Scenario Simulation</h2>
          <p className="subtitle">
            Interactively adjust cyclone parameters (wind intensity shift, coastal proximity) to forecast risk dynamics.
          </p>
        </div>
      </header>

      <div className="grid-2">
        <div className="card">
          <h3>Simulation Controls</h3>
          
          <div style={{ marginTop: '15px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-dim)', display: 'block', marginBottom: '6px' }}>
                Select Baseline Cyclone Event:
              </label>
              <select
                value={selectedBaseId}
                onChange={(e) => setSelectedBaseId(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: 'var(--bg-card)',
                  color: 'var(--text-main)',
                  border: '1px solid var(--border-color)'
                }}
              >
                {events.map((ev) => (
                  <option key={ev.cyclone_id} value={ev.cyclone_id}>
                    {ev.matched_storm_name ? `${ev.matched_storm_name} (#${ev.cyclone_id})` : `Cyclone Event #${ev.cyclone_id}`}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                <label>Wind Speed Adjustment (&Delta; kt):</label>
                <strong>{deltaWind > 0 ? `+${deltaWind}` : deltaWind} kt</strong>
              </div>
              <input
                type="range"
                min="-30"
                max="50"
                step="5"
                value={deltaWind}
                onChange={(e) => setDeltaWind(Number(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                <label>Simulated Coastal Distance:</label>
                <strong>{coastalDist} km</strong>
              </div>
              <input
                type="range"
                min="10"
                max="600"
                step="10"
                value={coastalDist}
                onChange={(e) => setCoastalDist(Number(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        <div className="card">
          <h3>Simulated Risk Shift</h3>
          {loading && <div style={{ marginTop: '20px' }}>Simulating scenario...</div>}

          {simulation && !loading && (
            <div style={{ marginTop: '15px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>BASELINE VS SIMULATED RISK</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginTop: '8px' }}>
                  <div>
                    <span style={{ fontSize: '0.8rem', display: 'block' }}>Baseline Risk</span>
                    <strong style={{ fontSize: '1.2rem' }}>{(simulation.baseline.risk_score * 100).toFixed(1)}%</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{simulation.baseline.intensity_category}</div>
                  </div>
                  <div style={{ fontSize: '1.4rem' }}>&rarr;</div>
                  <div>
                    <span style={{ fontSize: '0.8rem', display: 'block' }}>Simulated Risk</span>
                    <strong
                      style={{
                        fontSize: '1.2rem',
                        color: simulation.simulation.risk_score_delta > 0 ? '#f87171' : '#34d399'
                      }}
                    >
                      {(simulation.simulation.simulated_risk_score * 100).toFixed(1)}%
                    </strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{simulation.simulation.simulated_intensity_category}</div>
                  </div>
                </div>
              </div>

              <div className="metric-box">
                <span className="metric-label">Risk Shift Trend</span>
                <span
                  className="metric-value"
                  style={{ color: simulation.simulation.risk_score_delta > 0 ? '#f87171' : '#34d399' }}
                >
                  {simulation.risk_trend} ({simulation.simulation.risk_score_delta > 0 ? '+' : ''}
                  {(simulation.simulation.risk_score_delta * 100).toFixed(1)}%)
                </span>
              </div>

              <div style={{ background: 'rgba(56, 189, 248, 0.1)', padding: '12px', borderRadius: '8px', borderLeft: '3px solid #38bdf8' }}>
                <strong style={{ fontSize: '0.85rem', color: '#0284c7', display: 'block', marginBottom: '4px' }}>AI SOP Action Directive</strong>
                <p style={{ fontSize: '0.85rem', margin: 0, color: '#334155' }}>
                  {simulation.advisory_summary}
                </p>
              </div>

              {shapShifts && (
                <div style={{ background: '#f8faf7', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <strong style={{ fontSize: '0.85rem', color: '#0f172a', display: 'block', marginBottom: '8px' }}>
                    📊 Simulated Risk Drivers (Live SHAP Impact)
                  </strong>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {shapShifts.top_feature_contributions?.map((item, idx) => (
                      <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                        <span style={{ color: '#334155' }}>{item.feature}</span>
                        <strong style={{ color: item.shap_value > 0 ? '#dc2626' : '#059669' }}>
                          {item.shap_value > 0 ? `+${(item.shap_value * 100).toFixed(2)}%` : `${(item.shap_value * 100).toFixed(2)}%`}
                        </strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
