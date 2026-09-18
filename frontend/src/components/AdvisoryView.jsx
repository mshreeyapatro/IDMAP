import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function AdvisoryView() {
  const [baseId, setBaseId] = useState(46)
  const [loading, setLoading] = useState(false)
  const [advisoryData, setAdvisoryData] = useState(null)
  const [error, setError] = useState(null)
  
  // RAG Search State
  const [searchQuery, setSearchQuery] = useState('Puri Fani evacuation guidelines')
  const [searchResults, setSearchResults] = useState(null)
  const [searchLoading, setSearchLoading] = useState(false)

  useEffect(() => {
    fetchAdvisory(baseId)
  }, [])

  const fetchAdvisory = async (id) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.advisory(id)
      setAdvisoryData(data)
    } catch (err) {
      setError(err.message || 'Failed to fetch advisory')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setSearchLoading(true)
    try {
      const res = await api.retrieve(searchQuery, 4)
      setSearchResults(res.results)
    } catch (err) {
      console.error(err)
    } finally {
      setSearchLoading(false)
    }
  }

  const cv = advisoryData?.cv_summary

  return (
    <div className="view-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <header className="view-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '15px' }}>
        <div>
          <h2>⚡ Multimodal AI Advisory & RAG Engine</h2>
          <p className="view-subtitle">
            Fusing satellite Computer Vision feature predictions with Odisha knowledge base semantic retrieval.
          </p>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontWeight: 'bold' }}>Event ID:</label>
          <input
            type="number"
            value={baseId}
            onChange={(e) => setBaseId(Number(e.target.value))}
            style={{
              width: '80px',
              padding: '6px 10px',
              borderRadius: '6px',
              background: '#ffffff',
              color: '#0f172a',
              border: '1px solid #e2e8f0',
              fontWeight: 'bold'
            }}
          />
          <button
            onClick={() => fetchAdvisory(baseId)}
            disabled={loading}
            style={{
              padding: '7px 14px',
              background: '#059669',
              color: '#ffffff',
              borderRadius: '6px',
              border: 'none',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            {loading ? 'Analyzing...' : 'Generate Advisory'}
          </button>

          {advisoryData?.advisory_report && (
            <button
              onClick={() => {
                const element = document.createElement('a')
                const file = new Blob([advisoryData.advisory_report], { type: 'text/markdown' })
                element.href = URL.createObjectURL(file)
                element.download = `IDMAP_Advisory_Event_${baseId}.md`
                document.body.appendChild(element)
                element.click()
                document.body.removeChild(element)
              }}
              style={{
                padding: '7px 14px',
                background: '#d97706',
                color: '#ffffff',
                borderRadius: '6px',
                border: 'none',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              📥 Download Report
            </button>
          )}
        </div>
      </header>

      {error && (
        <div className="card" style={{ background: '#fef2f2', border: '1px solid #fca5a5', color: '#dc2626', padding: '14px', borderRadius: '8px' }}>
          ⚠️ {error}
        </div>
      )}

      {cv && (
        <div className="stat-grid">
          <div className="card stat-card">
            <span className="stat-label">IMD Classification</span>
            <div className="stat-value" style={{ color: '#059669', fontSize: '1.4rem' }}>{cv.intensity_category}</div>
            <div className="stat-hint">Severity: <strong>{cv.severity}</strong></div>
          </div>

          <div className="card stat-card">
            <span className="stat-label">Est. Wind Speed (TCIR Proxy)</span>
            <div className="stat-value" style={{ color: '#d97706', fontSize: '1.4rem' }}>{cv.vmax_proxy_kt?.toFixed(1)} kt</div>
            <div className="stat-hint">≈ {cv.vmax_proxy_kmh?.toFixed(1)} km/h</div>
          </div>

          <div className="card stat-card">
            <span className="stat-label">Autoencoder Anomaly Error</span>
            <div className="stat-value" style={{ color: cv.is_flagged_anomaly ? '#dc2626' : '#059669', fontSize: '1.4rem' }}>
              {cv.max_reconstruction_anomaly_score?.toFixed(4)}
            </div>
            <div className="stat-hint">
              {cv.is_flagged_anomaly ? (
                <span style={{ color: '#dc2626', fontWeight: 'bold' }}>⚠️ ANOMALOUS PATTERN</span>
              ) : (
                <span style={{ color: '#059669' }}>Normal Variance</span>
              )}
            </div>
          </div>

          <div className="card stat-card">
            <span className="stat-label">Satellite Crops</span>
            <div className="stat-value" style={{ color: '#0f172a', fontSize: '1.4rem' }}>
              {cv.raw_image_count + cv.infrared_image_count} images
            </div>
            <div className="stat-hint">{cv.raw_image_count} Visible, {cv.infrared_image_count} Infrared</div>
          </div>
        </div>
      )}

      {/* Main Content Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Left Col: Fused Advisory Report */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '10px' }}>
            <h3 style={{ margin: 0, color: '#0f172a' }}>📋 Grounded Multimodal Advisory Report</h3>
            <span style={{ fontSize: '0.75rem', background: 'rgba(217, 119, 6, 0.12)', color: '#d97706', border: '1px solid #b45309', padding: '3px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
              Event #{baseId}
            </span>
          </div>

          {loading ? (
            <div className="loading">Running Computer Vision feature extraction & RAG semantic search...</div>
          ) : advisoryData ? (
            <div style={{ background: '#f8faf7', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0', lineHeight: 1.7, fontSize: '0.9rem', color: '#334155', whiteSpace: 'pre-wrap' }}>
              {advisoryData.advisory_report}
            </div>
          ) : null}
        </div>

        {/* Right Col: Knowledge Base Retrieval & Citations */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ margin: 0, fontSize: '0.95rem', color: '#0f172a' }}>📚 RAG Knowledge Base Search</h3>
            
            <form onSubmit={handleSearch} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search Odisha cyclone guidelines..."
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: '6px',
                  background: '#f8faf7',
                  border: '1px solid #e2e8f0',
                  fontSize: '0.85rem',
                  color: '#0f172a'
                }}
              />
              <button
                type="submit"
                disabled={searchLoading}
                style={{
                  padding: '8px',
                  background: '#059669',
                  color: '#ffffff',
                  borderRadius: '6px',
                  border: 'none',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                {searchLoading ? 'Searching Vector Store...' : 'Search Knowledge Store'}
              </button>
            </form>

            {searchResults && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
                <strong style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Search Results</strong>
                {searchResults.map((res, idx) => (
                  <div key={idx} style={{ background: '#f8faf7', border: '1px solid #e2e8f0', padding: '10px', borderRadius: '6px', fontSize: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', color: '#059669', marginBottom: '4px' }}>
                      <span>{res.metadata?.section}</span>
                      <span style={{ fontSize: '0.7rem', background: 'rgba(5, 150, 105, 0.1)', padding: '2px 5px', borderRadius: '4px' }}>
                        Score: {res.score?.toFixed(3)}
                      </span>
                    </div>
                    <p style={{ margin: '4px 0', color: '#334155', lineHeight: 1.4 }}>{res.text?.slice(0, 180)}...</p>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Source: {res.metadata?.source}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Citations Card */}
          {advisoryData?.citations && advisoryData.citations.length > 0 && (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <h3 style={{ margin: 0, fontSize: '0.95rem', color: '#0f172a' }}>🔗 Source References & Citations</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {advisoryData.citations.map((cit, idx) => (
                  <div key={idx} style={{ background: '#f8faf7', border: '1px solid #e2e8f0', padding: '10px', borderRadius: '6px', fontSize: '0.8rem' }}>
                    <div style={{ fontWeight: 'bold', color: '#d97706', marginBottom: '2px' }}>
                      {cit.citation_id}: {cit.section}
                    </div>
                    <p style={{ margin: '2px 0', fontStyle: 'italic', color: '#475569', fontSize: '0.75rem' }}>"{cit.snippet}"</p>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Document: {cit.source}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
