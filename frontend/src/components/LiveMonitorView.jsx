import { useEffect, useState } from 'react'
import { api } from '../api'

export default function LiveMonitorView() {
  const [weatherFeed, setWeatherFeed] = useState(null)
  const [satFeed, setSatFeed] = useState(null)
  const [liveShap, setLiveShap] = useState(null)
  const [liveAdvisory, setLiveAdvisory] = useState(null)
  const [loadingWeather, setLoadingWeather] = useState(false)
  const [loadingAdvisory, setLoadingAdvisory] = useState(false)

  const fetchLiveData = () => {
    setLoadingWeather(true)
    api.liveWeather()
      .then((w) => {
        setWeatherFeed(w)
        setLoadingWeather(false)

        api.explainLive({
          wind_speed_kt: w.max_coastal_wind_speed_kt || 45.0,
          pressure_hpa: w.min_coastal_pressure_hpa || 1002.0,
          coastal_distance_km: 80.0,
          district_population: 1250000.0,
          anomaly_error: 0.08
        }).then(setLiveShap).catch(() => {})
      })
      .catch(() => setLoadingWeather(false))

    api.liveSatellite()
      .then((s) => setSatFeed(s))
      .catch(() => { })
  }

  useEffect(() => {
    fetchLiveData()
    const interval = setInterval(fetchLiveData, 300000) // auto refresh every 5 minutes (300,000 ms)
    return () => clearInterval(interval)
  }, [])

  const generateAdvisory = () => {
    setLoadingAdvisory(true)
    api.liveAdvisory()
      .then((data) => {
        setLiveAdvisory(data)
        setLoadingAdvisory(false)
      })
      .catch(() => setLoadingAdvisory(false))
  }

  return (
    <div className="view-container">
      <header className="view-header">
        <div>
          <h2>📡 Live Monitor (Weather & Satellite Ingestion)</h2>
          <p className="subtitle">
            Real-time meteorological monitoring across Odisha coastal stations (Open-Meteo API) and live satellite feeds (NASA GIBS / MOSDAC).
          </p>
        </div>
        <button
          onClick={fetchLiveData}
          disabled={loadingWeather}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            background: loadingWeather ? '#047857' : '#059669',
            color: '#ffffff',
            fontWeight: 'bold',
            border: 'none',
            cursor: loadingWeather ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          {loadingWeather && <span className="spinner-icon" style={{ borderColor: 'rgba(255,255,255,0.3)', borderTopColor: '#ffffff' }}></span>}
          {loadingWeather ? '⚡ Syncing Live Feed...' : '🔄 Refresh Live Feed'}
        </button>
      </header>

      {/* Show initial skeleton loader only when first loading with no feed */}
      {loadingWeather && !weatherFeed && (
        <div className="card loading" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="spinner-icon"></div> Fetching live coastal station weather readings...
        </div>
      )}

      {/* Keep page ALIVE once weatherFeed is available, updating data in-place */}
      {weatherFeed && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="grid-3">
            <div className="card metric-box">
              <span className="metric-label">Peak Coastal Wind Speed</span>
              <span className="metric-value" style={{ color: weatherFeed.max_coastal_wind_speed_kt > 25 ? '#dc2626' : '#d97706' }}>
                {weatherFeed.max_coastal_wind_speed_kt} kt
              </span>
            </div>
            <div className="card metric-box">
              <span className="metric-label">Minimum Surface Pressure</span>
              <span className="metric-value" style={{ color: weatherFeed.min_coastal_pressure_hpa < 1005 ? '#d97706' : '#059669' }}>
                {weatherFeed.min_coastal_pressure_hpa} hPa
              </span>
            </div>
            <div className="card metric-box">
              <span className="metric-label">State Cyclone Alert Level</span>
              <span className="metric-value" style={{ color: weatherFeed.coastal_cyclone_alert ? '#dc2626' : '#059669', fontSize: '1.2rem' }}>
                {weatherFeed.overall_state_severity}
              </span>
            </div>
          </div>

          <div className="card">
            <h3>Odisha Coastal & Inland Stations (Open-Meteo Live API)</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '15px', marginTop: '15px' }}>
              {weatherFeed.stations?.map((st, i) => (
                <div key={i} style={{ background: '#f8faf7', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0', borderTop: '3px solid #b45309' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <strong style={{ fontSize: '1rem', color: '#0f172a' }}>{st.station}</strong>
                    <span style={{ fontSize: '0.75rem', background: 'rgba(5, 150, 105, 0.1)', color: '#059669', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>
                      {st.type}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.85rem', color: '#334155' }}>
                    <div>Wind: <strong>{st.wind_speed_kt} kt</strong></div>
                    <div>Gusts: <strong>{st.wind_gusts_kt} kt</strong></div>
                    <div>Pressure: <strong>{st.surface_pressure_hpa} hPa</strong></div>
                    <div>Temp: <strong>{st.temperature_c}°C</strong></div>
                  </div>
                  <div style={{ marginTop: '10px', fontSize: '0.75rem', color: st.is_alert ? '#dc2626' : 'var(--text-dim)', fontWeight: 'bold' }}>
                    Status: {st.severity_status}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {liveShap && (
            <div className="card" style={{ borderTop: '3px solid #059669' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <h3 style={{ margin: 0, fontSize: '1rem', color: '#0f172a' }}>📊 Real-Time Predictive Risk Drivers (SHAP)</h3>
                <span style={{ fontSize: '0.8rem', background: 'rgba(5, 150, 105, 0.1)', color: '#059669', padding: '4px 10px', borderRadius: '6px', fontWeight: 'bold' }}>
                  Live Risk Score: {(liveShap.predicted_risk_score * 100).toFixed(1)}%
                </span>
              </div>
              <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '0 0 12px' }}>
                Explains in real-time what station factors drive today's predicted cyclone risk score across coastal Odisha.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
                {liveShap.top_feature_contributions?.map((item, idx) => {
                  const isPos = item.shap_value > 0
                  return (
                    <div key={idx} style={{ background: '#f8faf7', padding: '10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 'bold', color: '#0f172a' }}>{item.feature}</span>
                        <span style={{ fontWeight: 'bold', color: isPos ? '#dc2626' : '#059669' }}>
                          {isPos ? `+${(item.shap_value * 100).toFixed(2)}%` : `${(item.shap_value * 100).toFixed(2)}%`}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                        Sensor Val: {item.feature_value != null ? Number(item.feature_value).toFixed(1) : 'N/A'}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {satFeed && (
            <div className="card">
              <h3>🛰️ Live Satellite Coverage Layer (NASA GIBS / MOSDAC)</h3>
              <div style={{ display: 'flex', gap: '20px', alignItems: 'center', marginTop: '15px' }}>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                    <strong>Provider:</strong> {satFeed.nasa_gibs?.provider}<br />
                    <strong>Layer:</strong> {satFeed.nasa_gibs?.layer}<br />
                    <strong>Pass Date:</strong> {satFeed.nasa_gibs?.date || 'Latest'} (NASA GIBS Daily Mosaic)<br />
                    <strong>Coverage Domain:</strong> Bay of Bengal (15.0°N to 22.5°N)
                  </p>
                  <a
                    href={satFeed.mosdac_isro?.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: '#059669', fontSize: '0.85rem', fontWeight: 'bold' }}
                  >
                    View Official ISRO MOSDAC INSAT-3D Sector Image &rarr;
                  </a>
                </div>
                <div style={{ width: '220px', height: '140px', background: '#e2e8f0', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border)', position: 'relative' }}>
                  {satFeed.nasa_gibs?.tile_snapshot_url && (
                    <img
                      key={satFeed.nasa_gibs.tile_snapshot_url}
                      src={satFeed.nasa_gibs.tile_snapshot_url}
                      alt="NASA GIBS Satellite Snapshot"
                      style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                      onError={(e) => {
                        e.target.style.display = 'none'
                      }}
                    />
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3>🤖 Real-Time Evidence-Grounded AI Advisory</h3>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={generateAdvisory}
                  disabled={loadingAdvisory}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    background: '#d97706',
                    color: '#ffffff',
                    border: 'none',
                    cursor: 'pointer',
                    fontWeight: 'bold'
                  }}
                >
                  {loadingAdvisory ? 'Generating...' : '⚡ Generate Live RAG Advisory'}
                </button>

                {liveAdvisory?.advisory_report && (
                  <button
                    onClick={() => {
                      const element = document.createElement('a')
                      const file = new Blob([liveAdvisory.advisory_report], { type: 'text/markdown' })
                      element.href = URL.createObjectURL(file)
                      element.download = `IDMAP_Live_Advisory_${new Date().toISOString().slice(0, 10)}.md`
                      document.body.appendChild(element)
                      element.click()
                      document.body.removeChild(element)
                    }}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '6px',
                      background: '#10b981',
                      color: '#fff',
                      border: 'none',
                      cursor: 'pointer',
                      fontWeight: 'bold'
                    }}
                  >
                    📥 Download Advisory
                  </button>
                )}
              </div>
            </div>

            {liveAdvisory && (
              <div style={{ marginTop: '15px', background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #a855f7' }}>
                <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  {liveAdvisory.advisory_report}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
