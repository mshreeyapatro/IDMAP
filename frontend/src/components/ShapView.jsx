import { useEffect, useState } from 'react'
import { api } from '../api'

export default function ShapView({ onSelectEvent }) {
  const [mode, setMode] = useState('live') // 'live' or 'historical'
  const [events, setEvents] = useState([])
  const [selectedBaseId, setSelectedBaseId] = useState(25)
  const [liveWeather, setLiveWeather] = useState(null)
  const [shapData, setShapData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.events().then((res) => {
      setEvents(res || [])
      if (res && res.length > 0) {
        setSelectedBaseId(res[0].cyclone_id)
      }
    }).catch(() => {})
  }, [])

  const fetchShapData = () => {
    setLoading(true)
    setError(null)
    if (mode === 'live') {
      api.liveWeather().then((w) => {
        setLiveWeather(w)
        const wind = w.max_coastal_wind_speed_kt || 45.0
        const pressure = w.min_coastal_pressure_hpa || 1002.0
        api.explainLive({
          wind_speed_kt: wind,
          coastal_distance_km: 80.0, // Odisha coastal station proximity
          pressure_hpa: pressure,
          district_population: 1250000.0,
          anomaly_error: 0.08
        }).then((data) => {
          setShapData(data)
          setLoading(false)
        }).catch((err) => {
          setError(err.message || 'Failed live SHAP calculation')
          setLoading(false)
        })
      }).catch(() => {
        // Fallback live calculation if weather API fails
        api.explainLive({ wind_speed_kt: 55.0, coastal_distance_km: 85.0 }).then((data) => {
          setShapData(data)
          setLoading(false)
        }).catch(() => setLoading(false))
      })
    } else {
      if (!selectedBaseId) return
      api.explain(selectedBaseId)
        .then((data) => {
          setShapData(data)
          setLoading(false)
        })
        .catch((err) => {
          setError(err.message || 'Failed to fetch historical SHAP explanation')
          setLoading(false)
        })
    }
  }

  useEffect(() => {
    fetchShapData()
  }, [mode, selectedBaseId])

  return (
    <div className="view-container">
      <header className="view-header">
        <div>
          <h2>Predictive Risk Drivers (SHAP Explainability)</h2>
          <p className="subtitle">
            Feature-level SHAP evidence explaining why the XGBoost Risk Model assigns specific risk scores to real-time telemetry or historical storms.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Mode Switcher Buttons */}
          <div style={{ display: 'flex', background: '#e2e8f0', borderRadius: '6px', padding: '3px' }}>
            <button
              onClick={() => setMode('live')}
              style={{
                padding: '6px 14px',
                borderRadius: '4px',
                border: 'none',
                background: mode === 'live' ? '#059669' : 'transparent',
                color: mode === 'live' ? '#ffffff' : '#475569',
                fontWeight: 'bold',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              🔴 Live Sensor Forecast
            </button>
            <button
              onClick={() => setMode('historical')}
              style={{
                padding: '6px 14px',
                borderRadius: '4px',
                border: 'none',
                background: mode === 'historical' ? '#059669' : 'transparent',
                color: mode === 'historical' ? '#ffffff' : '#475569',
                fontWeight: 'bold',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              ☁️ Historical Archive
            </button>
          </div>

          {mode === 'historical' && (
            <select
              value={selectedBaseId}
              onChange={(e) => setSelectedBaseId(Number(e.target.value))}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                background: '#ffffff',
                color: '#0f172a',
                border: '1px solid var(--border)',
                fontWeight: 'bold',
                fontSize: '0.85rem',
                outline: 'none'
              }}
            >
              {events.map((ev) => (
                <option key={ev.cyclone_id} value={ev.cyclone_id}>
                  {ev.matched_storm_name ? `${ev.matched_storm_name} (#${ev.cyclone_id})` : `Cyclone Event #${ev.cyclone_id}`}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={fetchShapData}
            style={{
              padding: '6px 14px',
              borderRadius: '6px',
              background: '#d97706',
              color: '#ffffff',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '0.85rem'
            }}
          >
            🔄 Recalculate SHAP
          </button>
        </div>
      </header>

      {loading && <div className="card loading">Calculating real-time SHAP feature attributions...</div>}
      {error && <div className="card" style={{ color: '#dc2626' }}>Error: {error}</div>}

      {shapData && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Mode Banner */}
          <div style={{ background: mode === 'live' ? 'rgba(5, 150, 105, 0.1)' : 'rgba(217, 119, 6, 0.1)', padding: '12px 16px', borderRadius: '8px', borderLeft: `4px solid ${mode === 'live' ? '#059669' : '#d97706'}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong style={{ color: mode === 'live' ? '#059669' : '#d97706' }}>
                {mode === 'live' ? '📡 Real-Time Open-Meteo Telemetry Prediction' : `☁️ Historical Archive (${shapData.storm_name})`}
              </strong>
              <p style={{ margin: '2px 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                {mode === 'live'
                  ? `Peak Coastal Wind: ${shapData.input_summary?.wind_speed_kt || '45'} kt | Pressure: ${shapData.input_summary?.pressure_hpa || '1002'} hPa`
                  : `Analyzed Event ID #${shapData.base_id}`}
              </p>
            </div>
            <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: shapData.predicted_risk_score > 0.6 ? '#dc2626' : '#059669' }}>
              {(shapData.predicted_risk_score * 100).toFixed(1)}% Risk Score
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
            <div className="card">
              <h3>Prediction Summary</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '15px' }}>
                <div style={{ background: '#f8faf7', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Predicted Risk Score</span>
                  <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: shapData.predicted_risk_score > 0.6 ? '#dc2626' : '#059669' }}>
                    {(shapData.predicted_risk_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ background: '#f8faf7', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Model Base Expectation</span>
                  <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#0f172a' }}>
                    {(shapData.base_value * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ background: '#f8faf7', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Execution Mode</span>
                  <span style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#059669' }}>
                    {shapData.mode === 'live_forecast' ? '🔴 Real-Time Forecast' : '☁️ Archive Record'}
                  </span>
                </div>
              </div>
            </div>

            <div className="card">
              <h3>Top Feature Impact Breakdown</h3>
              <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '4px 0 14px' }}>
                Positive SHAP values (red) increase cyclone risk; negative values (green) reduce calculated risk.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {shapData.top_feature_contributions?.map((item, idx) => {
                  const absVal = Math.abs(item.shap_value)
                  const widthPct = Math.min(100, Math.max(10, (absVal / 0.25) * 100))
                  const isPos = item.shap_value > 0

                  return (
                    <div key={idx} style={{ background: '#f8faf7', padding: '10px 14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                        <strong style={{ color: '#0f172a' }}>{item.feature}</strong>
                        <span style={{ color: isPos ? '#dc2626' : '#059669', fontWeight: 'bold' }}>
                          {isPos ? `+${(item.shap_value * 100).toFixed(2)}%` : `${(item.shap_value * 100).toFixed(2)}%`}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ flex: 1, height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${widthPct}%`,
                              height: '100%',
                              background: isPos ? '#dc2626' : '#059669',
                              borderRadius: '4px',
                              transition: 'width 0.4s ease'
                            }}
                          />
                        </div>
                        <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'bold' }}>
                          Val: {item.feature_value != null ? Number(item.feature_value).toFixed(1) : 'N/A'}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

