import { useEffect, useState } from 'react'
import { api } from '../api'

function getStormCategory(windKt) {
  if (!windKt) return { label: 'Tropical Depression', color: '#059669', bg: '#d1fae5' }
  if (windKt >= 120) return { label: 'Category 5 Super Cyclonic Storm', color: '#991b1b', bg: '#fee2e2' }
  if (windKt >= 90) return { label: 'Category 4 Extremely Severe Cyclonic Storm', color: '#dc2626', bg: '#fee2e2' }
  if (windKt >= 64) return { label: 'Category 3 Very Severe Cyclonic Storm', color: '#ea580c', bg: '#ffedd5' }
  if (windKt >= 48) return { label: 'Severe Cyclonic Storm', color: '#d97706', bg: '#fef3c7' }
  if (windKt >= 34) return { label: 'Cyclonic Storm', color: '#ca8a04', bg: '#fef9c3' }
  return { label: 'Deep Depression', color: '#059669', bg: '#d1fae5' }
}

const formatIST = (timestamp) => {
  if (!timestamp) return ''
  try {
    const d = new Date(timestamp)
    if (isNaN(d.getTime())) return timestamp
    return d.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    }) + ' IST'
  } catch (e) {
    return timestamp
  }
}

export default function EventDrawer({ baseId, onClose }) {
  const [detail, setDetail] = useState(null)
  const [activeTab, setActiveTab] = useState('summary')

  useEffect(() => {
    if (baseId == null) return
    setDetail(null)
    setActiveTab('summary')
    api.event(baseId).then(setDetail).catch(() => setDetail({ error: 'failed to load' }))
  }, [baseId])

  if (baseId == null) return null

  const cat = getStormCategory(detail?.wind_speed_kt)
  const isHighRisk = (detail?.wind_speed_kt || 0) > 64 || (detail?.coastal_distance_km || 999) < 100

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#0f172a' }}>
                {detail?.matched_storm_name ? `Cyclone ${detail.matched_storm_name}` : `Event #${baseId}`}
              </h2>
              {detail?.is_odisha_relevant && (
                <span style={{ background: '#059669', color: '#fff', fontSize: '0.75rem', fontWeight: 'bold', padding: '2px 8px', borderRadius: '12px' }}>
                  Odisha Coast Alert
                </span>
              )}
            </div>
            <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: '#64748b' }}>
              {detail?.timestamp ? formatIST(detail.timestamp) : 'Historical Sensor Record'}
            </p>
          </div>
          <button className="drawer-close-btn" onClick={onClose} title="Close Panel">✕</button>
        </div>

        {/* Storm Category Banner */}
        {detail && !detail.error && (
          <div style={{ background: cat.bg, borderLeft: `4px solid ${cat.color}`, padding: '10px 14px', borderRadius: '6px', margin: '14px 16px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: cat.color, fontWeight: 'bold', fontSize: '0.85rem' }}>
              {cat.label}
            </span>
            <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: isHighRisk ? '#dc2626' : '#059669', background: '#fff', padding: '2px 8px', borderRadius: '4px' }}>
              {isHighRisk ? '🔴 HIGH EVACUATION RISK' : '🟢 MONITORED'}
            </span>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="drawer-tabs">
          <button className={`drawer-tab ${activeTab === 'summary' ? 'active' : ''}`} onClick={() => setActiveTab('summary')}>
            📋 Summary
          </button>
          <button className={`drawer-tab ${activeTab === 'satellite' ? 'active' : ''}`} onClick={() => setActiveTab('satellite')}>
            🛰️ Satellite ({detail?.images?.length || 0})
          </button>
          <button className={`drawer-tab ${activeTab === 'directives' ? 'active' : ''}`} onClick={() => setActiveTab('directives')}>
            🚨 Action Directives
          </button>
        </div>

        {/* Body Content */}
        <div className="drawer-body">
          {!detail ? (
            <div className="card loading" style={{ textAlign: 'center', padding: '40px' }}>
              Loading event intelligence...
            </div>
          ) : detail.error ? (
            <div className="card" style={{ color: '#dc2626' }}>{detail.error}</div>
          ) : (
            <>
              {activeTab === 'summary' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="card">
                    <h3 style={{ margin: '0 0 12px', fontSize: '0.95rem', color: '#0f172a' }}>📍 Key Impact Parameters</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      <div style={{ background: '#f8faf7', padding: '10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Peak Wind Speed</span>
                        <strong style={{ fontSize: '1.1rem', color: '#0f172a' }}>
                          {detail.wind_speed_kt ? `${detail.wind_speed_kt.toFixed(0)} kt (${Math.round(detail.wind_speed_kt * 1.852)} km/h)` : 'N/A'}
                        </strong>
                      </div>
                      <div style={{ background: '#f8faf7', padding: '10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Distance to Odisha Coast</span>
                        <strong style={{ fontSize: '1.1rem', color: detail.coastal_distance_km < 100 ? '#dc2626' : '#0f172a' }}>
                          {detail.coastal_distance_km != null ? `${detail.coastal_distance_km.toFixed(0)} km` : 'N/A'}
                        </strong>
                      </div>
                      <div style={{ background: '#f8faf7', padding: '10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Central Pressure</span>
                        <strong style={{ fontSize: '1.1rem', color: '#0f172a' }}>
                          {detail.pressure_hpa ? `${detail.pressure_hpa.toFixed(0)} hPa` : 'N/A'}
                        </strong>
                      </div>
                      <div style={{ background: '#f8faf7', padding: '10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Closest Target District</span>
                        <strong style={{ fontSize: '1rem', color: '#0f172a' }}>
                          {detail.nearest_odisha_district || 'Coastal Domain'}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h3 style={{ margin: '0 0 10px', fontSize: '0.95rem', color: '#0f172a' }}>📊 Risk Factors Breakdown</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                          <span>Wind Intensity Severity</span>
                          <strong>{Math.min(100, Math.round(((detail.wind_speed_kt || 30) / 130) * 100))}%</strong>
                        </div>
                        <div style={{ background: '#e2e8f0', borderRadius: '4px', height: '6px', overflow: 'hidden' }}>
                          <div style={{ width: `${Math.min(100, Math.round(((detail.wind_speed_kt || 30) / 130) * 100))}%`, background: '#dc2626', height: '100%' }} />
                        </div>
                      </div>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                          <span>Coastal Exposure Risk</span>
                          <strong>{Math.max(10, 100 - Math.round(((detail.coastal_distance_km || 300) / 400) * 100))}%</strong>
                        </div>
                        <div style={{ background: '#e2e8f0', borderRadius: '4px', height: '6px', overflow: 'hidden' }}>
                          <div style={{ width: `${Math.max(10, 100 - Math.round(((detail.coastal_distance_km || 300) / 400) * 100))}%`, background: '#d97706', height: '100%' }} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'satellite' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="card">
                    <h3 style={{ margin: '0 0 10px', fontSize: '0.95rem', color: '#0f172a' }}>🛰️ TCIR Satellite Imagery Frames</h3>
                    {detail.images && detail.images.length > 0 ? (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
                        {detail.images.map((im, idx) => (
                          <div key={idx} style={{ background: '#f8faf7', borderRadius: '6px', padding: '8px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                            <img
                              src={api.imageUrl(im.url)}
                              alt={im.filename}
                              style={{ width: '100%', height: '110px', objectFit: 'cover', borderRadius: '4px' }}
                            />
                            <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#334155', display: 'block', marginTop: '4px' }}>
                              {im.modality}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p style={{ color: '#64748b', fontSize: '0.85rem' }}>No raw imagery tiles attached for this record.</p>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'directives' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div className="card" style={{ borderLeft: '4px solid #059669' }}>
                    <h3 style={{ margin: '0 0 8px', fontSize: '0.95rem', color: '#0f172a' }}>📜 Official Odisha SOP Guidelines</h3>
                    <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.85rem', color: '#334155', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <li><strong>Evacuation Directive:</strong> {isHighRisk ? 'Immediate mandatory evacuation for coastal 10km zone.' : 'Standby alert for coastal shelter managers.'}</li>
                      <li><strong>Shelter Readiness:</strong> {isHighRisk ? 'Activate all Multipurpose Cyclone Shelters (MCS) with DG power & drinking water.' : 'Ensure backup power generators are fueled.'}</li>
                      <li><strong>Maritime Warning:</strong> Red alert banner — suspension of all fishing and trawling operations.</li>
                      <li><strong>NDRF Pre-positioning:</strong> Deploy 2 teams to target district ({detail.nearest_odisha_district || 'Coastal Zone'}).</li>
                    </ul>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </aside>
    </div>
  )
}
