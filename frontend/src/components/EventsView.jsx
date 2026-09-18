import { useEffect, useState } from 'react'
import { api } from '../api'

const SPLITS = ['all', 'train', 'val', 'test']

export default function EventsView({ onSelectEvent }) {
  const [events, setEvents] = useState(null)
  const [split, setSplit] = useState('all')
  const [odishaOnly, setOdishaOnly] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)

  useEffect(() => {
    api.events(split === 'all' ? undefined : split).then(setEvents).catch(() => setEvents([]))
  }, [split])

  const handleAnalyzeLiveSatellite = async () => {
    setUploading(true)
    setAnalysisResult(null)
    try {
      const res = await api.analyzeLiveSatellite()
      setAnalysisResult(res)
    } catch (err) {
      setAnalysisResult({ error: err.message || 'Live satellite analysis failed' })
    } finally {
      setUploading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setAnalysisResult(null)
    try {
      const res = await api.analyzeImage(file)
      setAnalysisResult(res)
    } catch (err) {
      setAnalysisResult({ error: err.message || 'Upload failed' })
    } finally {
      setUploading(false)
    }
  }

  const visible = events && (odishaOnly ? events.filter((e) => e.is_odisha_relevant) : events)

  return (
    <div>
      <div className="view-header">
        <h1>Events & Live Satellite Analysis</h1>
        <p className="view-subtitle">
          Browse dataset image-groups, analyze live NASA GIBS satellite passes in 1-click, or upload custom satellite crops for TCIR feature extraction, anomaly detection, and risk scoring.
        </p>
      </div>

      <div className="card" style={{ marginBottom: '20px', padding: '18px' }}>
        <h3>🛰️ Live Satellite Ingestion & Custom Crop Inference</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginBottom: '14px' }}>
          Instantly ingest active NASA GIBS Bay of Bengal satellite passes or upload custom INSAT-3D crops to run real-time TCIR ResNet feature extraction, Autoencoder reconstruction error analysis, and XGBoost risk prediction.
        </p>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <button
            onClick={handleAnalyzeLiveSatellite}
            disabled={uploading}
            style={{
              padding: '10px 18px',
              borderRadius: '6px',
              background: '#059669',
              color: '#ffffff',
              fontWeight: 'bold',
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.88rem'
            }}
          >
            {uploading ? '⚡ Processing Satellite Pass...' : '⚡ 1-Click Analyze Live NASA GIBS Satellite Snapshot'}
          </button>

          <label
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '9px 16px',
              background: '#f1f5f9',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '0.88rem',
              color: '#334155'
            }}
          >
            📁 Upload Custom Satellite File
            <input type="file" accept="image/*" onChange={handleFileUpload} disabled={uploading} style={{ display: 'none' }} />
          </label>
        </div>

        {uploading && <div style={{ marginTop: '12px', color: '#059669', fontWeight: 'bold' }}>Running TCIR ResNet + Autoencoder + XGBoost pipeline on satellite feed...</div>}

        {analysisResult && (
          <div style={{ marginTop: '16px', background: '#f8faf7', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            {analysisResult.error ? (
              <div style={{ color: '#dc2626', fontWeight: 'bold' }}>Error: {analysisResult.error}</div>
            ) : (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0, color: '#059669', fontSize: '1rem' }}>
                    {analysisResult.source_url ? '📡 Live NASA GIBS Satellite Snapshot Analysis' : '📁 Custom Image Crop Analysis Results'}
                  </h4>
                  {analysisResult.pass_date && (
                    <span style={{ fontSize: '0.78rem', background: '#e2e8f0', padding: '2px 8px', borderRadius: '4px', color: '#475569', fontWeight: 'bold' }}>
                      Pass Date: {analysisResult.pass_date}
                    </span>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '14px' }}>
                  <div className="metric-box">
                    <span className="metric-label">Predicted Vmax Proxy</span>
                    <span className="metric-value">{analysisResult.vmax_proxy_kt} kt</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-label">Intensity Category</span>
                    <span className="metric-value" style={{ fontSize: '1.1rem' }}>{analysisResult.intensity_category}</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-label">Anomaly Reconstruction Error</span>
                    <span className="metric-value" style={{ color: analysisResult.is_anomaly ? '#dc2626' : '#059669' }}>
                      {analysisResult.reconstruction_error} {analysisResult.is_anomaly ? '⚠️' : '✓'}
                    </span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-label">Predicted Risk Score</span>
                    <span className="metric-value" style={{ color: analysisResult.predicted_risk_score > 0.5 ? '#dc2626' : '#059669' }}>
                      {(analysisResult.predicted_risk_score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div style={{ fontSize: '0.85rem', background: 'rgba(5, 150, 105, 0.08)', padding: '12px', borderRadius: '6px', borderLeft: '4px solid #059669' }}>
                  <strong style={{ color: '#059669', display: 'block', marginBottom: '2px' }}>AI Advisory Directive</strong>
                  <span style={{ color: '#334155' }}>{analysisResult.advisory_recommendation}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="filter-row">
        {SPLITS.map((s) => (
          <button
            key={s}
            className={`chip ${split === s ? 'chip-active' : ''}`}
            onClick={() => setSplit(s)}
          >
            {s}
          </button>
        ))}
        <button
          className={`chip ${odishaOnly ? 'chip-active' : ''}`}
          onClick={() => setOdishaOnly((v) => !v)}
        >
          Odisha only
        </button>
      </div>

      {!visible ? (
        <p className="loading">Loading events…</p>
      ) : (
        <div className="card-grid">
          {visible.map((e) => (
            <div key={e.cyclone_id} className="event-card clickable" onClick={() => onSelectEvent(e.cyclone_id)}>
              {e.thumbnail_url ? (
                <img src={api.imageUrl(e.thumbnail_url)} alt={`event ${e.cyclone_id}`} className="event-thumb" />
              ) : (
                <div className="event-thumb event-thumb-empty">no image</div>
              )}
              <div className="event-card-body">
                <div className="event-card-title">
                  {e.matched_storm_name ? `Cyclone ${e.matched_storm_name}` : `Event ${e.cyclone_id}`}
                  {e.is_odisha_relevant && <span className="odisha-badge" title="Storm track came within 150km of Odisha">Odisha</span>}
                </div>
                <div className="event-card-meta">
                  <span className={`split-tag split-${e.split}`}>{e.split}</span>
                  <span>{e.raw_image_count + e.infrared_image_count} images</span>
                  {e.wind_speed_kt != null && <span>{e.wind_speed_kt.toFixed(0)} kt</span>}
                </div>
                {e.timestamp && <div className="event-card-date">{e.timestamp.slice(0, 10)}</div>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
