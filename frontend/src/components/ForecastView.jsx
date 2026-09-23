import { useEffect, useState } from 'react'
import { api } from '../api'

const formatToIST = (timeStr) => {
  if (!timeStr) return ''
  if (typeof timeStr !== 'string') return String(timeStr)

  if (timeStr.includes('IST')) return timeStr

  const utcMatch = timeStr.match(/^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{1,2}):(\d{2})\s*UTC$/i)
  if (utcMatch) {
    const day = parseInt(utcMatch[1], 10)
    const monthStr = utcMatch[2]
    const hour = parseInt(utcMatch[3], 10)
    const minute = parseInt(utcMatch[4], 10)

    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    const mIdx = months.findIndex(m => m.toLowerCase() === monthStr.toLowerCase())

    if (mIdx !== -1) {
      const year = new Date().getFullYear()
      const utcDate = new Date(Date.UTC(year, mIdx, day, hour, minute))
      return utcDate.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }) + ' IST'
    }
  }

  try {
    const d = new Date(timeStr.replace(' UTC', 'Z'))
    if (!isNaN(d.getTime())) {
      return d.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }) + ' IST'
    }
  } catch (e) { }

  return timeStr.replace(/UTC/g, 'IST')
}

// Dynamic Layman Date Formatter (e.g. "Today, 06:06 PM (23 Sep)")
function formatLaymanTime(timeStr, horizonHours = 0) {
  if (!timeStr) return { relativeDay: horizonHours === 0 ? 'Live Now' : `+${horizonHours}h Ahead`, timeOnly: '', dateOnly: '', fullLabel: horizonHours === 0 ? 'Live Now' : `+${horizonHours} Hours Ahead` }
  const raw = formatToIST(timeStr)
  const parts = raw.split(' ')
  let timeOnly = ''
  let dateOnly = ''
  if (parts.length >= 3) {
    dateOnly = `${parts[0]} ${parts[1]}`.replace(',', '')
    timeOnly = parts.slice(2).join(' ').replace('IST', '').trim()
  } else {
    timeOnly = raw
    dateOnly = horizonHours === 0 ? 'Live Now' : `+${horizonHours} Hours Ahead`
  }

  let relativeDay = ''
  if (horizonHours === 0) relativeDay = 'Live Now'
  else if (horizonHours < 6) relativeDay = 'Today'
  else if (horizonHours <= 14) relativeDay = 'Tonight'
  else if (horizonHours <= 26) relativeDay = 'Tomorrow Morning'
  else if (horizonHours <= 36) relativeDay = 'Tomorrow Evening'
  else relativeDay = 'Day 3 Outlook'

  return {
    relativeDay,
    timeOnly,
    dateOnly,
    fullLabel: `${relativeDay} • ${timeOnly} IST (${dateOnly})`
  }
}

// Dynamic Wind Severity & Physical Hazard Descriptor for Citizens & Responders
function getLaymanWindDescriptor(windKmh) {
  const kmh = Number(windKmh) || 0
  if (kmh >= 165) {
    return {
      severity: 'Extremely Severe Cyclone',
      impact: 'Catastrophic: Extensive structural damage, roofs blown off, grid collapse',
      badgeColor: '#dc2626',
      badgeBg: '#fee2e2',
      border: '#f87171',
      icon: '🚨'
    }
  }
  if (kmh >= 120) {
    return {
      severity: 'Very Severe Cyclone',
      impact: 'Destructive: Uproots large trees, breaks power poles, severe storm surge',
      badgeColor: '#ea580c',
      badgeBg: '#ffedd5',
      border: '#fb923c',
      icon: '🌪️'
    }
  }
  if (kmh >= 90) {
    return {
      severity: 'Severe Cyclonic Storm',
      impact: 'Dangerous: Flying debris, kutcha house damage, heavy coastal flooding',
      badgeColor: '#d97706',
      badgeBg: '#fef3c7',
      border: '#fcd34d',
      icon: '💨'
    }
  }
  if (kmh >= 62) {
    return {
      severity: 'Cyclonic Gale Winds',
      impact: 'Hazardous: Walking outdoors dangerous, small trees/branches broken',
      badgeColor: '#ca8a04',
      badgeBg: '#fef9c3',
      border: '#fde047',
      icon: '⚠️'
    }
  }
  if (kmh >= 45) {
    return {
      severity: 'Strong Squally Breeze',
      impact: 'Choppy seas, rough surf, fishing trawlers must return to port',
      badgeColor: '#0284c7',
      badgeBg: '#e0f2fe',
      border: '#7dd3fc',
      icon: '🌊'
    }
  }
  return {
    severity: 'Moderate / Calming Winds',
    impact: 'Post-storm dissipation, residual rain, safe for movement',
    badgeColor: '#15803d',
    badgeBg: '#dcfce7',
    border: '#86efac',
    icon: '🍃'
  }
}

// Dynamically generate slider gradient based on prediction lifecycle codes
function generateDynamicTrackGradient(timelineSteps) {
  if (!timelineSteps || timelineSteps.length === 0) {
    return 'linear-gradient(to right, #0284c7 0%, #059669 100%)'
  }
  const total = timelineSteps.length - 1 || 1
  const stops = []
  
  // Color map for prediction lifecycle codes
  const codeColorMap = {
    APPROACHING: '#0284c7',       // Sky blue
    FORWARD_EYEWALL: '#f59e0b',   // Amber
    CORE_LANDFALL: '#dc2626',     // Crimson
    INLAND_WEAKENING: '#7c3aed',  // Purple
    DISSIPATING: '#059669'        // Green
  }

  timelineSteps.forEach((step, idx) => {
    const pct = ((idx / total) * 100).toFixed(1)
    const color = codeColorMap[step.lifecycle_code] || '#0284c7'
    stops.push(`${color} ${pct}%`)
  })

  return `linear-gradient(to right, ${stops.join(', ')})`
}

// Dynamic Plain-Language Situational Summary Generator
function getLaymanSituationalSummary(currentHorizon, shortRange) {
  if (!currentHorizon) return "Loading active cyclone trajectory data..."
  const lCode = currentHorizon.lifecycle_code
  const windKmh = currentHorizon.projected_peak_wind_kmh || Math.round((currentHorizon.projected_peak_wind_kt || 35) * 1.852)
  const targetDist = shortRange?.predicted_landfall_target_district || "Ganjam"
  const etlHours = Math.round(shortRange?.estimated_time_to_landfall_hours || 7)
  const h = currentHorizon.horizon_hours || 0

  if (lCode === 'CORE_LANDFALL' || h === etlHours) {
    return `🚨 PEAK LANDFALL IMPACT IN PROGRESS: Cyclone eye is making direct coastal landfall over ${targetDist} sector. Severe gale winds (${windKmh} km/h), storm surge (>2.5m), and torrential rains are actively hitting coastal belts. Evacuees must remain in shelters.`
  }
  if (lCode === 'FORWARD_EYEWALL' || (h < etlHours && h >= etlHours - 3)) {
    return `🌪️ LEADING EYEWALL REACHING SHORE: Outer spiral rainbands and hurricane-force winds (${windKmh} km/h) are battering the coastline with rising storm surge. Final zero-casualty evacuations are underway before eye crossing.`
  }
  if (lCode === 'INLAND_WEAKENING' || h > etlHours) {
    return `📉 POST-LANDFALL INLAND DECAY: Storm eye has moved inland across Western Odisha (Koraput/Malkangiri/Chhattisgarh) and is weakening (${windKmh} km/h). Coastal districts have transitioned to safe post-storm recovery.`
  }
  return `🌊 ADVANCING OVER BAY OF BENGAL: Cyclonic storm is tracking northwestward across the ocean at ${currentHorizon.projected_translation_speed_kmh || 14.8} km/h, organizing convective eyewall strength (${windKmh} km/h) prior to coastal approach.`
}

export default function ForecastView() {
  const [activeMode, setActiveMode] = useState('unified') // 'unified', '48h', or '60day'
  const [unifiedSurvey, setUnifiedSurvey] = useState(null)
  const [shortRange, setShortRange] = useState(null)
  const [seasonal, setSeasonal] = useState(null)
  const [loadingSurvey, setLoadingSurvey] = useState(false)
  const [loadingShort, setLoadingShort] = useState(false)
  const [loadingSeasonal, setLoadingSeasonal] = useState(false)
  const [selectedHorizonIdx, setSelectedHorizonIdx] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [showJsonModal, setShowJsonModal] = useState(false)

  // Interactive Table Controls: Search, Risk Filtering, and Column Auto-Sorting
  const [searchTerm, setSearchTerm] = useState('')
  const [filterCategory, setFilterCategory] = useState('all') // 'all', 'high_risk', 'coastal'
  const [sortBy, setSortBy] = useState('risk') // 'risk', 'dist', 'wind', 'evac', 'name'
  const [sortAsc, setSortAsc] = useState(false) // Default descending: highest risk first!

  const handleSort = (colKey) => {
    if (sortBy === colKey) {
      setSortAsc(!sortAsc)
    } else {
      setSortBy(colKey)
      setSortAsc(colKey === 'dist' || colKey === 'name')
    }
  }

  const fetchUnifiedSurvey = (forceRefresh = false) => {
    setLoadingSurvey(true)
    api.unifiedLiveSurvey(forceRefresh)
      .then((data) => {
        setUnifiedSurvey(data)
        setLoadingSurvey(false)
      })
      .catch(() => setLoadingSurvey(false))
  }

  const fetchShortRange = (forceRefresh = false) => {
    setLoadingShort(true)
    api.shortRangeForecast(forceRefresh)
      .then((data) => {
        setShortRange(data)
        setLoadingShort(false)
      })
      .catch(() => setLoadingShort(false))
  }

  const fetchSeasonal = (forceRefresh = false) => {
    setLoadingSeasonal(true)
    api.seasonalOutlook(forceRefresh)
      .then((data) => {
        setSeasonal(data)
        setLoadingSeasonal(false)
      })
      .catch(() => setLoadingSeasonal(false))
  }

  useEffect(() => {
    fetchUnifiedSurvey(false)
    fetchShortRange(false)
    fetchSeasonal(false)
  }, [])

  const timelineSteps = shortRange?.timeline_matrix || []

  // Auto-play timeline animation playback
  useEffect(() => {
    let interval = null
    if (isPlaying && timelineSteps.length > 0) {
      interval = setInterval(() => {
        setSelectedHorizonIdx((prev) => (prev + 1) % timelineSteps.length)
      }, 1000)
    } else {
      clearInterval(interval)
    }
    return () => clearInterval(interval)
  }, [isPlaying, timelineSteps.length])
  const currentHorizon = timelineSteps[selectedHorizonIdx] || null
  const peakEvacTarget = Math.max(...timelineSteps.map(t => t.total_state_evacuation_target || 0), 0)
  const peakShelters = Math.max(...timelineSteps.map(t => t.total_shelters_activated || 0), 0)
  const peakNDRF = Math.max(...timelineSteps.map(t => t.total_ndrf_teams_deployed || 0), 0)

  const summaryData = unifiedSurvey?.unified_survey_summary || {
    satellite_pass: "INSAT-3D / VIIRS",
    eye_coordinates: { lat: 17.8, lon: 86.1 },
    heading_vector: "315° NW",
    translation_speed_kmh: 14.8,
    translation_speed_knots: 8.0,
    convective_density_score: 0.88,
    storm_radius_km: 280,
    primary_landfall_target: "Ganjam",
    landfall_sector: "Gopalpur Coast",
    estimated_landfall_ist: "23 Sep, 11:20 AM IST",
    total_evacuation_target: 1204059,
    total_mcs_activated: 1212,
    total_ndrf_teams: 29
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* <div className="view-header" style={{ marginBottom: 0 }}>
        <h1>🔮 OSDMA Unified Disaster Risk Survey & Predictive Forecast Generator</h1>
        <p className="view-subtitle">
          Multimodal AI Intelligence Engine for Odisha: Real-time Satellite Vision Extraction, 0-48h Trajectory Steering, Dynamic Wind Decay, 10-District Evacuation & MCS Allocations.
        </p>
      </div> */}

      {/* Mode Selector Tabs */}
      <div style={{ display: 'flex', gap: '10px', background: '#f8faf7', padding: '6px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
        <button
          onClick={() => setActiveMode('unified')}
          style={{
            flex: 1,
            padding: '10px 16px',
            borderRadius: '8px',
            border: 'none',
            background: activeMode === 'unified' ? '#dc2626' : 'transparent',
            color: activeMode === 'unified' ? '#ffffff' : '#475569',
            fontWeight: 'bold',
            fontSize: '0.88rem',
            cursor: 'pointer',
            boxShadow: activeMode === 'unified' ? '0 2px 6px rgba(220,38,38,0.25)' : 'none',
            transition: 'all 0.15s'
          }}
        >
          🚨 Unified Live Disaster Risk Survey & 48h Dynamic Track
        </button>
        <button
          onClick={() => setActiveMode('60day')}
          style={{
            flex: 1,
            padding: '10px 16px',
            borderRadius: '8px',
            border: 'none',
            background: activeMode === '60day' ? '#ffffff' : 'transparent',
            color: activeMode === '60day' ? '#059669' : '#64748b',
            fontWeight: 'bold',
            fontSize: '0.88rem',
            cursor: 'pointer',
            boxShadow: activeMode === '60day' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none',
            transition: 'all 0.15s'
          }}
        >
          🗓️ 60-Day Seasonal Cyclone Outlook
        </button>
      </div>

      {/* Merged View: Unified Live Disaster Risk Survey & 48h Dynamic Track Scrubber */}
      {activeMode === 'unified' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {loadingSurvey && !unifiedSurvey ? (
            <div className="card loading" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="spinner-icon"></div> Generating Unified Disaster Risk Survey & Vision Extraction...
            </div>
          ) : (
            <>
              {/* Executive Summary Banner with Meaningful KPIs */}
              <div className="card" style={{ borderTop: '4px solid #dc2626', background: 'linear-gradient(135deg, #ffffff 0%, #fef2f2 100%)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#991b1b' }}>🏛️ OSDMA State Command Executive Survey Summary</span>
                      <span style={{ background: '#fee2e2', color: '#dc2626', padding: '3px 12px', borderRadius: '12px', fontWeight: 'bold', fontSize: '0.8rem', border: '1px solid #fca5a5' }}>
                        🔴 VERY SEVERE CYCLONE LANDFALL WARNING
                      </span>
                    </div>
                    <p style={{ margin: '4px 0 0', fontSize: '0.84rem', color: '#7f1d1d' }}>
                      Multimodal AI Fusion: INSAT-3D IR Satellite, GNN Spatial Graph (10-District Odisha Belt), Open-Meteo Telemetry & 48h Scrubber.
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      onClick={() => { fetchUnifiedSurvey(true); fetchShortRange(true); }}
                      disabled={loadingSurvey || loadingShort}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '6px',
                        background: '#dc2626',
                        color: '#ffffff',
                        fontWeight: 'bold',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '0.82rem'
                      }}
                    >
                      {loadingSurvey || loadingShort ? '⚡ Syncing...' : '🔄 Refresh Live Survey'}
                    </button>
                    <button
                      onClick={() => setShowJsonModal(true)}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '6px',
                        background: '#0f172a',
                        color: '#ffffff',
                        fontWeight: 'bold',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '0.82rem'
                      }}
                    >
                      {'{ }'} Export JSON Payload
                    </button>
                  </div>
                </div>

                {/* 5 Meaningful Executive KPIs */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginTop: '12px' }}>
                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid #fecaca', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                    <span style={{ fontSize: '0.75rem', color: '#991b1b', display: 'block', fontWeight: 'bold' }}>🎯 Primary Landfall Target</span>
                    <strong style={{ fontSize: '1.35rem', color: '#dc2626', display: 'block', marginTop: '2px' }}>
                      {(summaryData.primary_landfall_target || shortRange?.predicted_landfall_target_district || 'Puri')} Coast
                    </strong>
                    <span style={{ fontSize: '0.73rem', color: '#64748b' }}>
                      {(summaryData.landfall_sector || shortRange?.landfall_sector || 'Puri / Astranga Sector')}
                      {shortRange?.probabilistic_ensemble?.ensemble_confidence_score_pct ? ` • ${shortRange.probabilistic_ensemble.ensemble_confidence_score_pct}% Ensemble Consensus` : ''}
                    </span>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid #fed7aa', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                    <span style={{ fontSize: '0.75rem', color: '#9a3412', display: 'block', fontWeight: 'bold' }}>Landfall Operational Window & ETA</span>
                    <strong style={{ fontSize: '1.08rem', color: '#c2410c', display: 'block', marginTop: '2px' }}>
                      {summaryData.landfall_impact_window_ist || shortRange?.landfall_impact_window_ist || summaryData.estimated_landfall_ist}
                    </strong>
                    <div style={{ fontSize: '0.75rem', color: '#0f172a', fontWeight: '600', marginTop: '3px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span> Eye Centroid Crossing:</span>
                      <span style={{ color: '#d97706' }}>{summaryData.estimated_landfall_ist || shortRange?.estimated_landfall_timestamp_ist}</span>
                    </div>
                    <span style={{ fontSize: '0.72rem', color: '#64748b', display: 'block', marginTop: '3px' }}>
                      Peak: {summaryData.landfall_intensity_knots || shortRange?.projected_peak_landfall_wind_kt || 85} kt (~{Math.round((summaryData.landfall_intensity_knots || shortRange?.projected_peak_landfall_wind_kt || 85) * 1.852)} km/h) | {summaryData.landfall_pressure_hpa || shortRange?.projected_min_landfall_pressure_hpa || 966} hPa
                    </span>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid #fed7aa', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                    <span style={{ fontSize: '0.75rem', color: '#c2410c', display: 'block', fontWeight: 'bold' }}>⚡ Rapid Intensification (RI)</span>
                    <strong style={{ fontSize: '1.2rem', color: (shortRange?.rapid_intensification_watch?.is_rapid_intensification_active || summaryData?.rapid_intensification_watch?.is_rapid_intensification_active) ? '#dc2626' : '#059669', display: 'block', marginTop: '2px' }}>
                      {(shortRange?.rapid_intensification_watch?.ri_probability_pct || summaryData?.rapid_intensification_watch?.ri_probability_pct || 82)}% Probability
                    </strong>
                    <span style={{ fontSize: '0.73rem', color: '#64748b' }}>WMO Surge: ≥30 kt / 24h</span>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid #fecaca', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                    <span style={{ fontSize: '0.75rem', color: '#991b1b', display: 'block', fontWeight: 'bold' }}>🚨 Peak Evacuation Target</span>
                    <strong style={{ fontSize: '1.35rem', color: '#b91c1c', display: 'block', marginTop: '2px' }}>
                      {(peakEvacTarget || currentHorizon?.total_state_evacuation_target || summaryData.total_evacuation_target)?.toLocaleString()}
                    </strong>
                    <span style={{ fontSize: '0.73rem', color: '#64748b' }}>
                      {currentHorizon ? `Peak Target (Step evac: ${currentHorizon.total_state_evacuation_target?.toLocaleString()})` : 'State Total Target (Zero-Casualty SOP)'}
                    </span>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid #bbf7d0', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                    <span style={{ fontSize: '0.75rem', color: '#166534', display: 'block', fontWeight: 'bold' }}>🏠 Activated MCS & NDRF</span>
                    <strong style={{ fontSize: '1.35rem', color: '#15803d', display: 'block', marginTop: '2px' }}>
                      {(peakShelters || currentHorizon?.total_shelters_activated || summaryData.total_mcs_activated)?.toLocaleString()} MCS / {peakNDRF || currentHorizon?.total_ndrf_teams_deployed || summaryData.total_ndrf_teams} Teams
                    </strong>
                    <span style={{ fontSize: '0.73rem', color: '#64748b' }}>Peak Allocation across Belt</span>
                  </div>
                </div>
              </div>
              {/* STEP 1: Vision Extraction & Live Satellite Imagery Pass Analysis */}
              <div className="card" style={{ borderTop: '4px solid #0284c7', background: '#ffffff', padding: '14px 18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <h3 style={{ margin: 0, fontSize: '0.98rem', color: '#0f172a' }}>
                    📡 Satellite Vision Extraction & Live Imagery Analysis
                  </h3>
                  <span style={{ fontSize: '0.74rem', background: '#e0f2fe', color: '#0369a1', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
                    NASA GIBS / INSAT-3D Pass ({unifiedSurvey?.satellite_pass_date || 'Live Pass'})
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '14px', alignItems: 'center' }}>
                  {/* Live Analyzed Satellite Image Crop Thumbnail */}
                  <div style={{ position: 'relative', borderRadius: '6px', overflow: 'hidden', border: '1px solid #cbd5e1', background: '#0f172a', height: '100px' }}>
                    <img
                      src={unifiedSurvey?.nasa_gibs?.tile_snapshot_url || 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/2026-09-22/250m/3/2/5.jpg'}
                      alt="Analyzed Satellite Crop"
                      onError={(e) => { e.target.src = 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/2026-09-22/250m/3/2/5.jpg'; }}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                    <span style={{ position: 'absolute', bottom: '3px', left: '3px', background: 'rgba(15, 23, 42, 0.88)', color: '#38bdf8', fontSize: '0.62rem', padding: '1px 5px', borderRadius: '3px', fontWeight: 'bold' }}>
                      Live NASA GIBS Pass (PyTorch CNN)
                    </span>
                  </div>

                  {/* Compact Metrics Cards Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                    <div style={{ background: '#f8faf7', padding: '8px 10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'block' }}>👁️ Eye / LLCC Centroid</span>
                      <strong style={{ fontSize: '0.98rem', color: '#0284c7', display: 'block', marginTop: '1px' }}>
                        {summaryData.eye_coordinates?.lat}° N, {summaryData.eye_coordinates?.lon}° E
                      </strong>
                      <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Bay of Bengal Domain</span>
                    </div>

                    <div style={{ background: '#f8faf7', padding: '8px 10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'block' }}>🧭 Heading Vector</span>
                      <strong style={{ fontSize: '0.98rem', color: '#0f172a', display: 'block', marginTop: '1px' }}>
                        {summaryData.heading_vector}
                      </strong>
                      <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Steering South Odisha</span>
                    </div>

                    <div style={{ background: '#f8faf7', padding: '8px 10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'block' }}>⚡ Forward Speed</span>
                      <strong style={{ fontSize: '0.98rem', color: '#d97706', display: 'block', marginTop: '1px' }}>
                        {summaryData.translation_speed_kmh} km/h ({summaryData.translation_speed_knots} kt)
                      </strong>
                      <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Steady Track</span>
                    </div>

                    <div style={{ background: '#f8faf7', padding: '8px 10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'block' }}>🌀 Cloud Density & R</span>
                      <strong style={{ fontSize: '0.98rem', color: '#059669', display: 'block', marginTop: '1px' }}>
                        Score: {summaryData.convective_density_score} | R: {summaryData.storm_radius_km}km
                      </strong>
                      <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Convective Wall</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Prominent Interactive 48-Hour Timeline Scrubber (Layman UX Enhanced) */}
              {(() => {
                const etlHour = Math.round(shortRange?.estimated_time_to_landfall_hours || 7)
                const forwardHour = Math.max(0, etlHour - 3)
                const targetDistrict = shortRange?.predicted_landfall_target_district || "Ganjam"
                const dynamicTrackGradient = generateDynamicTrackGradient(timelineSteps)
                const currentLaymanTime = formatLaymanTime(currentHorizon?.timestamp_formatted, selectedHorizonIdx)
                const currentWindDesc = getLaymanWindDescriptor(currentHorizon?.projected_peak_wind_kmh || Math.round((currentHorizon?.projected_peak_wind_kt || 35) * 1.852))
                const situationalSummary = getLaymanSituationalSummary(currentHorizon, shortRange)
                const milestoneHours = Array.from(new Set([0, 1, 3, forwardHour, etlHour, 12, 18, 24, 36, 48]))
                  .filter(h => h >= 0 && h <= (timelineSteps.length - 1))
                  .sort((a, b) => a - b)

                return (
                  <div className="card" style={{ background: '#ffffff', borderTop: '4px solid #059669', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
                    {/* Header: Title, Layman IST Time & Hazard Severity */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <h3 style={{ margin: 0, fontSize: '1.12rem', color: '#0f172a' }}>⏱️ 48-Hour Interactive Cyclone Timeline</h3>
                          <span style={{ fontSize: '0.72rem', fontWeight: 'bold', background: '#ecfdf5', color: '#059669', padding: '3px 10px', borderRadius: '12px', border: '1px solid #a7f3d0' }}>
                            ⚡ Hour-by-Hour Evolution (0h - 48h)
                          </span>
                        </div>
                        <p style={{ margin: '3px 0 0', fontSize: '0.82rem', color: '#64748b' }}>
                          Drag the timeline or use quick presets below to track how winds, coastal landfall, and district danger change.
                        </p>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                        {/* Selected Time Pill */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', background: '#f8fafc', padding: '6px 14px', borderRadius: '8px', border: '1.5px solid #cbd5e1' }}>
                          <span style={{ fontSize: '0.94rem', fontWeight: 'bold', color: '#0f172a' }}>
                            🗓️ {currentLaymanTime.fullLabel}
                          </span>
                          <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '600' }}>
                            {selectedHorizonIdx === 0 ? '⚡ Live Ingest' : `⏱️ +${selectedHorizonIdx} Hours from Now`}
                          </span>
                        </div>

                        {/* Peak Wind & Damage Severity Pill */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', background: currentWindDesc.badgeBg, padding: '6px 14px', borderRadius: '8px', border: `1.5px solid ${currentWindDesc.border}` }}>
                          <span style={{ fontSize: '0.88rem', fontWeight: 'bold', color: currentWindDesc.badgeColor }}>
                            {currentWindDesc.icon} {currentHorizon?.projected_peak_wind_kmh || 65} km/h ({currentHorizon?.projected_peak_wind_kt || 35} kt)
                          </span>
                          <span style={{ fontSize: '0.72rem', color: currentWindDesc.badgeColor, fontWeight: '600' }}>
                            {currentWindDesc.severity}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Fast Presets & Playback Controls */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        onClick={() => setSelectedHorizonIdx(0)}
                        style={{ padding: '6px 12px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #cbd5e1', background: selectedHorizonIdx === 0 ? '#e2e8f0' : '#f8fafc', cursor: 'pointer', color: '#1e293b' }}
                      >
                        ⏮️ Live Now
                      </button>

                      {forwardHour > 0 && forwardHour !== etlHour && (
                        <button
                          type="button"
                          onClick={() => setSelectedHorizonIdx(forwardHour)}
                          style={{ padding: '6px 12px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #fcd34d', background: selectedHorizonIdx === forwardHour ? '#fde68a' : '#fffbeb', cursor: 'pointer', color: '#92400e' }}
                        >
                          ⚠️ Outer Winds on Coast (+{forwardHour}h Ahead)
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => setSelectedHorizonIdx(etlHour)}
                        style={{ padding: '6px 14px', fontSize: '0.82rem', fontWeight: 'bold', borderRadius: '6px', border: '1.5px solid #f87171', background: selectedHorizonIdx === etlHour ? '#fee2e2' : '#fef2f2', color: '#991b1b', cursor: 'pointer', boxShadow: '0 1px 3px rgba(220,38,38,0.15)' }}
                      >
                        🎯 Peak Eye Landfall (+{etlHour}h Ahead • {targetDistrict})
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedHorizonIdx(Math.min(18, timelineSteps.length - 1))}
                        style={{ padding: '6px 12px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #c4b5fd', background: selectedHorizonIdx === 18 ? '#ddd6fe' : '#f5f3ff', cursor: 'pointer', color: '#5b21b6' }}
                      >
                        🌅 Tomorrow Morning
                      </button>

                      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <button
                          type="button"
                          onClick={() => setSelectedHorizonIdx(prev => Math.max(0, prev - 1))}
                          disabled={selectedHorizonIdx === 0}
                          style={{ padding: '5px 10px', fontSize: '0.78rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#f8fafc', cursor: selectedHorizonIdx === 0 ? 'not-allowed' : 'pointer', color: '#334155' }}
                        >
                          ◀ -1h
                        </button>
                        <button
                          type="button"
                          onClick={() => setIsPlaying(!isPlaying)}
                          style={{ padding: '6px 16px', fontSize: '0.84rem', fontWeight: 'bold', borderRadius: '6px', border: 'none', background: isPlaying ? '#dc2626' : '#059669', color: '#ffffff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
                        >
                          {isPlaying ? '⏸ Pause Timeline' : '▶ Auto-Play 48h'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedHorizonIdx(prev => Math.min(timelineSteps.length - 1, prev + 1))}
                          disabled={selectedHorizonIdx >= timelineSteps.length - 1}
                          style={{ padding: '5px 10px', fontSize: '0.78rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#f8fafc', cursor: selectedHorizonIdx >= timelineSteps.length - 1 ? 'not-allowed' : 'pointer', color: '#334155' }}
                        >
                          +1h ▶
                        </button>
                      </div>
                    </div>

                    {/* Dynamic Multi-Zone Slider Track */}
                    <div style={{ margin: '14px 0 8px' }}>
                      <input
                        type="range"
                        min="0"
                        max={(timelineSteps.length || 49) - 1}
                        step="1"
                        value={selectedHorizonIdx}
                        onChange={(e) => setSelectedHorizonIdx(Number(e.target.value))}
                        style={{
                          width: '100%',
                          height: '14px',
                          borderRadius: '7px',
                          background: dynamicTrackGradient,
                          cursor: 'pointer',
                          outline: 'none',
                          boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.2)'
                        }}
                      />

                      {/* Dynamic Lifecycle Phase Track Labels */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#64748b', marginTop: '4px', fontWeight: '600' }}>
                        <span>🔵 Approaching Ocean</span>
                        <span>🟠 Coastal Gale Alert</span>
                        <span style={{ color: '#dc2626', fontWeight: 'bold' }}>🔴 Landfall Strike (+{etlHour}h Ahead)</span>
                        <span>🟣 Inland Decay across Western Odisha</span>
                      </div>

                      {/* Milestone Cards Bar with Dynamic Badges */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
                        {milestoneHours.map((milestoneHour) => {
                          const actualIdx = Math.min(milestoneHour, timelineSteps.length - 1)
                          const item = timelineSteps[actualIdx]
                          const isSelected = selectedHorizonIdx === actualIdx
                          const isLandfall = milestoneHour === etlHour
                          const isForward = milestoneHour === forwardHour && forwardHour !== 0 && forwardHour !== etlHour
                          const layman = formatLaymanTime(item?.timestamp_formatted, milestoneHour)
                          const lCode = item?.lifecycle_code

                          let badgeLabel = '🌊 Approaching'
                          let badgeBg = '#e0f2fe'
                          let badgeColor = '#0369a1'

                          if (isLandfall || lCode === 'CORE_LANDFALL') {
                            badgeLabel = '🔴 Landfall'
                            badgeBg = '#fee2e2'
                            badgeColor = '#dc2626'
                          } else if (isForward || lCode === 'FORWARD_EYEWALL') {
                            badgeLabel = '🟠 Outer Gale'
                            badgeBg = '#fef3c7'
                            badgeColor = '#d97706'
                          } else if (lCode === 'INLAND_WEAKENING') {
                            badgeLabel = '🟣 Inland'
                            badgeBg = '#ede9fe'
                            badgeColor = '#7c3aed'
                          }

                          const timeSubtitle = milestoneHour === 0 
                            ? 'Live Now' 
                            : (isLandfall ? `Landfall (~${milestoneHour}h)` : `+${milestoneHour} Hours`);

                          return (
                            <div
                              key={milestoneHour}
                              onClick={() => setSelectedHorizonIdx(actualIdx)}
                              style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                cursor: 'pointer',
                                padding: '8px 10px',
                                minWidth: '88px',
                                borderRadius: '8px',
                                background: isSelected
                                  ? 'rgba(5, 150, 105, 0.15)'
                                  : isLandfall
                                    ? 'rgba(239, 68, 68, 0.08)'
                                    : '#f8fafc',
                                border: isSelected
                                  ? '2px solid #059669'
                                  : isLandfall
                                    ? '1.5px solid #ef4444'
                                    : '1px solid #e2e8f0',
                                transition: 'all 0.15s',
                                boxShadow: isSelected ? '0 0 0 2px rgba(5, 150, 105, 0.25)' : 'none'
                              }}
                            >
                              <span style={{ fontSize: '0.66rem', fontWeight: 'bold', background: badgeBg, color: badgeColor, padding: '1px 6px', borderRadius: '4px', whiteSpace: 'nowrap' }}>
                                {badgeLabel}
                              </span>
                              <strong style={{ color: isSelected ? '#059669' : isLandfall ? '#dc2626' : '#0f172a', fontSize: '0.92rem', marginTop: '4px' }}>
                                {layman.timeOnly || 'Live'}
                              </strong>
                              <span style={{ color: '#475569', fontSize: '0.72rem', fontWeight: '600', marginTop: '1px', whiteSpace: 'nowrap' }}>
                                {timeSubtitle}
                              </span>
                              <span style={{ color: '#94a3b8', fontSize: '0.68rem', marginTop: '1px', whiteSpace: 'nowrap' }}>
                                {layman.relativeDay}
                              </span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                )
              })()}


              {/* STEP 3: District Wise Risk & Alert Status Matrix with Auto-Sorting & Filter Controls */}
              {(() => {
                const rawList = currentHorizon?.district_matrix || unifiedSurvey?.district_risk_matrix || unifiedSurvey?.district_survey_matrix || [];

                // Live Filtering
                const filteredList = rawList.filter((d) => {
                  const matchName = d.district.toLowerCase().includes(searchTerm.toLowerCase());
                  if (!matchName) return false;

                  const rScore = d.predicted_risk_score || 0.10;
                  const cDist = d.coastal_distance_km || d.distance_to_eye_km || 100.0;

                  if (filterCategory === 'high_risk') return rScore >= 0.40;
                  if (filterCategory === 'coastal') return cDist <= 20.0;
                  return true;
                });

                // Auto Sorting (Default: Risk Score Descending)
                const sortedList = [...filteredList].sort((a, b) => {
                  let valA = 0, valB = 0;
                  if (sortBy === 'risk') {
                    valA = a.predicted_risk_score || 0.10;
                    valB = b.predicted_risk_score || 0.10;
                  } else if (sortBy === 'dist') {
                    valA = a.coastal_distance_km || a.distance_to_eye_km || 0;
                    valB = b.coastal_distance_km || b.distance_to_eye_km || 0;
                  } else if (sortBy === 'wind') {
                    valA = a.projected_wind_kt || a.estimated_wind_kt || 0;
                    valB = b.projected_wind_kt || b.estimated_wind_kt || 0;
                  } else if (sortBy === 'evac') {
                    valA = a.evacuation_target || a.people_to_evacuate || 0;
                    valB = b.evacuation_target || b.people_to_evacuate || 0;
                  } else if (sortBy === 'name') {
                    return sortAsc ? a.district.localeCompare(b.district) : b.district.localeCompare(a.district);
                  }

                  return sortAsc ? valA - valB : valB - valA;
                });

                const countHigh = rawList.filter(d => (d.predicted_risk_score || 0.1) >= 0.40).length;
                const countCoastal = rawList.filter(d => (d.coastal_distance_km || d.distance_to_eye_km || 100) <= 20.0).length;

                // Single Unified Situational Summary
                const currentWindDesc = getLaymanWindDescriptor(currentHorizon?.projected_peak_wind_kmh || Math.round((currentHorizon?.projected_peak_wind_kt || 35) * 1.852));
                const situationalSummary = getLaymanSituationalSummary(currentHorizon, shortRange);
                const currentLaymanTime = formatLaymanTime(currentHorizon?.timestamp_formatted, selectedHorizonIdx);

                return (
                  <div className="card" style={{ background: '#ffffff', borderTop: '4px solid #d97706' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                      <h3 style={{ margin: 0, fontSize: '1.02rem', color: '#0f172a' }}>
                        📊 District Wise Risk & Alert Status Matrix (Analyzed for ALL {rawList.length} Districts at {formatToIST(currentHorizon?.timestamp_formatted) || 'Live IST'})
                      </h3>
                      <span style={{ fontSize: '0.78rem', color: '#059669', background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '3px 10px', borderRadius: '6px', fontWeight: '600' }}>
                        ⚡ Auto-Sorted by Risk Score (Highest First)
                      </span>
                    </div>

                    {/* Single Concise Situational Summary Banner */}
                    <div style={{
                      background: currentWindDesc.badgeBg,
                      border: `1.5px solid ${currentWindDesc.border}`,
                      borderRadius: '8px',
                      padding: '10px 14px',
                      margin: '10px 0 14px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '10px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                        <span style={{
                          background: currentWindDesc.badgeColor,
                          color: '#ffffff',
                          padding: '3px 10px',
                          borderRadius: '6px',
                          fontWeight: 'bold',
                          fontSize: '0.78rem',
                          letterSpacing: '0.3px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          {currentWindDesc.icon} {currentHorizon?.lifecycle_phase || currentWindDesc.severity}
                        </span>
                        <span style={{ fontSize: '0.82rem', color: currentWindDesc.badgeColor, fontWeight: '500', lineHeight: '1.4' }}>
                          {situationalSummary}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: currentWindDesc.badgeColor, background: 'rgba(255,255,255,0.7)', padding: '2px 8px', borderRadius: '4px' }}>
                        {currentLaymanTime.relativeDay} • {selectedHorizonIdx === 0 ? 'Live Now' : `+${selectedHorizonIdx}h Ahead`}
                      </span>
                    </div>

                    {/* Filter & Search Bar */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '14px 0 16px', flexWrap: 'wrap', gap: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <button
                          className={`filter-pill ${filterCategory === 'all' ? 'active' : ''}`}
                          onClick={() => setFilterCategory('all')}
                        >
                          All Districts ({rawList.length})
                        </button>
                        <button
                          className={`filter-pill ${filterCategory === 'high_risk' ? 'active' : ''}`}
                          onClick={() => setFilterCategory('high_risk')}
                        >
                          🔴 High Warning / Evac ({countHigh})
                        </button>
                        <button
                          className={`filter-pill ${filterCategory === 'coastal' ? 'active' : ''}`}
                          onClick={() => setFilterCategory('coastal')}
                        >
                          🌊 Coastal Belt (≤20km) ({countCoastal})
                        </button>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input
                          type="text"
                          placeholder="🔍 Search district..."
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          style={{
                            padding: '6px 12px',
                            borderRadius: '6px',
                            border: '1px solid #cbd5e1',
                            fontSize: '0.82rem',
                            outline: 'none',
                            width: '190px',
                            background: '#f8fafc'
                          }}
                        />
                      </div>
                    </div>

                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                        <thead>
                          <tr style={{ background: '#f1f5f9', color: '#0f172a', textTransform: 'uppercase', fontSize: '0.75rem', cursor: 'pointer' }}>
                            <th style={{ padding: '9px 10px', textAlign: 'left' }} onClick={() => handleSort('name')}>
                              District {sortBy === 'name' ? (sortAsc ? '▲' : '▼') : ''}
                            </th>
                            <th style={{ padding: '9px 10px', textAlign: 'left' }} onClick={() => handleSort('dist')}>
                              Eye Proximity (d_eye) {sortBy === 'dist' ? (sortAsc ? '▲' : '▼') : ''}
                            </th>
                            <th style={{ padding: '9px 10px', textAlign: 'left' }} onClick={() => handleSort('wind')}>
                              Rankine Wind V(r) {sortBy === 'wind' ? (sortAsc ? '▲' : '▼') : ''}
                            </th>
                            <th style={{ padding: '9px 10px', textAlign: 'left' }} onClick={() => handleSort('risk')}>
                              Risk Score {sortBy === 'risk' ? (sortAsc ? '▲' : '▼') : '↓'}
                            </th>
                            <th style={{ padding: '9px 10px', textAlign: 'left' }}>Alert Status Pill</th>
                            <th style={{ padding: '9px 10px', textAlign: 'left' }} onClick={() => handleSort('evac')}>
                              Evacuation Target {sortBy === 'evac' ? (sortAsc ? '▲' : '▼') : ''}
                            </th>
                            <th style={{ padding: '9px 10px', textAlign: 'left' }}>Activated MCS</th>
                            <th style={{ padding: '9px 10px', textAlign: 'left' }}>NDRF Teams</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sortedList.length === 0 ? (
                            <tr>
                              <td colSpan="8" style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>
                                No districts match the filter criteria "{searchTerm}".
                              </td>
                            </tr>
                          ) : (
                            sortedList.map((d, idx) => {
                              const pill = d.alert_status_pill || `🔴 ${d.alert_level}`
                              const isCritical = pill.includes('CRITICAL')
                              const isHigh = pill.includes('HIGH')
                              const isAdvisory = pill.includes('ADVISORY')
                              const windKt = d.projected_wind_kt || d.estimated_wind_kt || 25.0
                              const windKmh = d.projected_wind_kmh || d.estimated_wind_kmh || Math.round(windKt * 1.852)
                              const riskScore = d.predicted_risk_score || 0.10
                              const eyeDist = d.distance_to_eye_km || d.distance_to_storm_center_km || d.coastal_distance_km
                              const coastDist = Number(d.coastal_distance_km || 100.0)
                              const surgeM = (coastDist <= 20.0 && d.projected_storm_surge_m) ? Number(d.projected_storm_surge_m) : 0.0
                              const rainMm = d.projected_rainfall_24h_mm || Math.round(180 * Math.exp(-eyeDist / 140.0))
                              const quadrant = d.quadrant_sector || (d.bearing_deg !== undefined ? (d.bearing_deg > 315 || d.bearing_deg < 45 ? 'Right-Front (Dangerous Semicircle)' : 'Left-Front') : null)

                              return (
                                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', background: idx % 2 === 0 ? '#ffffff' : '#f8faf7' }}>
                                  <td style={{ padding: '8px 10px', fontWeight: 'bold', color: '#0f172a' }}>
                                    <div>{d.district}</div>
                                    {quadrant && eyeDist <= 160 && (
                                      <span style={{
                                        fontSize: '0.64rem',
                                        fontWeight: 'bold',
                                        padding: '1px 5px',
                                        borderRadius: '3px',
                                        background: quadrant.includes('Dangerous') || quadrant.includes('Right-Front') ? '#ffedd5' : '#f1f5f9',
                                        color: quadrant.includes('Dangerous') || quadrant.includes('Right-Front') ? '#c2410c' : '#64748b',
                                        display: 'inline-block',
                                        marginTop: '2px'
                                      }}>
                                        🧭 {quadrant.includes('Dangerous') ? 'Right-Front (Dangerous)' : quadrant}
                                      </span>
                                    )}
                                  </td>
                                  <td style={{ padding: '8px 10px' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                      <strong style={{ color: eyeDist <= 35 ? '#dc2626' : (eyeDist <= 100 ? '#d97706' : '#0284c7'), fontSize: '0.84rem' }}>
                                        {eyeDist} km
                                      </strong>
                                      <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                                        Coast: {coastDist} km
                                      </span>
                                    </div>
                                  </td>
                                  <td style={{ padding: '8px 10px' }}>
                                    <div style={{ color: '#d97706', fontWeight: 'bold', fontSize: '0.84rem' }}>
                                      {windKt} kt ({windKmh} km/h)
                                    </div>
                                    <div style={{ fontSize: '0.68rem', color: '#0284c7', marginTop: '2px', fontWeight: '500' }}>
                                      🌧️ 24h: {rainMm} mm
                                    </div>
                                  </td>
                                  <td style={{ padding: '8px 10px', fontWeight: 'bold' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                      <span style={{ minWidth: '42px', color: riskScore >= 0.40 ? '#dc2626' : (riskScore >= 0.22 ? '#d97706' : '#059669') }}>
                                        {(riskScore * 100).toFixed(1)}%
                                      </span>
                                      <div className="risk-progress-bar">
                                        <div
                                          className="risk-progress-fill"
                                          style={{
                                            width: `${Math.min(100, Math.max(8, riskScore * 100))}%`,
                                            background: riskScore >= 0.40 ? '#dc2626' : (riskScore >= 0.22 ? '#d97706' : '#059669')
                                          }}
                                        />
                                      </div>
                                    </div>
                                  </td>
                                  <td style={{ padding: '8px 10px' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                                      <span style={{
                                        fontSize: '0.72rem',
                                        fontWeight: 'bold',
                                        padding: '2px 7px',
                                        borderRadius: '4px',
                                        background: isCritical ? '#fee2e2' : (isHigh ? '#ffedd5' : (isAdvisory ? '#fef9c3' : '#d1fae5')),
                                        color: isCritical ? '#dc2626' : (isHigh ? '#c2410c' : (isAdvisory ? '#a16207' : '#15803d')),
                                        border: `1px solid ${isCritical ? '#fca5a5' : (isHigh ? '#fdba74' : (isAdvisory ? '#fef08a' : '#86efac'))}`
                                      }}>
                                        {pill}
                                      </span>
                                      {surgeM >= 0.8 && (
                                        <span style={{
                                          fontSize: '0.66rem',
                                          fontWeight: 'bold',
                                          padding: '1px 5px',
                                          borderRadius: '3px',
                                          background: surgeM >= 2.5 ? '#fee2e2' : (surgeM >= 1.5 ? '#e0f2fe' : '#f0fdf4'),
                                          color: surgeM >= 2.5 ? '#dc2626' : (surgeM >= 1.5 ? '#0369a1' : '#15803d'),
                                          display: 'inline-block'
                                        }}>
                                          🌊 Surge: {surgeM.toFixed(1)} m
                                        </span>
                                      )}
                                    </div>
                                  </td>
                                  <td style={{ padding: '8px 10px', fontWeight: 'bold', color: '#b91c1c' }}>
                                    {(d.evacuation_target || d.people_to_evacuate)?.toLocaleString()}
                                  </td>
                                  <td style={{ padding: '8px 10px', color: '#15803d', fontWeight: 'bold' }}>
                                    {d.mcs_activated || d.multipurpose_shelters_required}
                                  </td>
                                  <td style={{ padding: '8px 10px', color: '#0369a1', fontWeight: 'bold' }}>
                                    {d.ndrf_teams || d.ndrf_teams_required}
                                  </td>
                                </tr>
                              )
                            })
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )
              })()}

              {/* Block-Level Precautionary Directives for District Collectors */}
              <div className="card" style={{ background: '#ffffff', borderLeft: '4px solid #dc2626' }}>
                <h3 style={{ margin: '0 0 12px', fontSize: '1.02rem', color: '#0f172a' }}>
                  📜 Top 3 Block-Level SOP Precautionary Directives for District Collectors
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
                  <div style={{ background: '#fff5f5', padding: '14px', borderRadius: '8px', border: '1px solid #fecaca' }}>
                    <strong style={{ color: '#dc2626', fontSize: '0.88rem', display: 'block', marginBottom: '6px' }}>
                      🚨 DIRECTIVE 1: Mandatory Zero-Casualty Evacuation
                    </strong>
                    <span style={{ fontSize: '0.82rem', color: '#7f1d1d', lineHeight: '1.4' }}>
                      Execute mandatory zero-casualty evacuation within 10 km coastal belt by 23 Sep 04:00 AM IST (T-7 hours before landfall). Move all kutcha house dwellers to shelters.
                    </span>
                  </div>

                  <div style={{ background: '#fff7ed', padding: '14px', borderRadius: '8px', border: '1px solid #fed7aa' }}>
                    <strong style={{ color: '#c2410c', fontSize: '0.88rem', display: 'block', marginBottom: '6px' }}>
                      🚒 DIRECTIVE 2: NDRF / ODRAF Pre-positioning & Clear Corridors
                    </strong>
                    <span style={{ fontSize: '0.82rem', color: '#7c2d12', lineHeight: '1.4' }}>
                      Pre-position NDRF/ODRAF heavy rescue teams with tree-cutters and dewatering pumps. Clear main trunk transit corridors (NH-16 & state highways) for emergency medical conduits.
                    </span>
                  </div>

                  <div style={{ background: '#f0fdf4', padding: '14px', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                    <strong style={{ color: '#15803d', fontSize: '0.88rem', display: 'block', marginBottom: '6px' }}>
                      ⚡ DIRECTIVE 3: Port Operations Suspension & Power Isolation
                    </strong>
                    <span style={{ fontSize: '0.82rem', color: '#14532d', lineHeight: '1.4' }}>
                      Order full suspension of port operations at Gopalpur Port and anchor all fishing trawlers. Execute pre-emptive electrical grid shutdown for feeder lines exceeding 65 km/h sustained wind thresholds.
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Mode 1: 48-Hour Short-Range View */}
      {activeMode === '48h' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {loadingShort && !shortRange ? (
            <div className="card loading" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="spinner-icon"></div> Generating 48-Hour Trajectory & Landfall Matrix...
            </div>
          ) : shortRange && (
            <>
              {/* Live Satellite Imagery & Vision AI Telemetry Card */}
              <div className="card" style={{ borderTop: '4px solid #0284c7', background: '#ffffff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#0f172a' }}>📡 Live Satellite Imagery & Multimodal AI Vision Telemetry</span>
                    <span style={{ background: 'rgba(2, 132, 199, 0.1)', color: '#0284c7', padding: '2px 10px', borderRadius: '12px', fontWeight: 'bold', fontSize: '0.75rem' }}>
                      ISRO MOSDAC / NASA GIBS
                    </span>
                  </div>
                  <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                    Updated: {shortRange.satellite_telemetry?.fetched_at ? new Date(shortRange.satellite_telemetry.fetched_at).toLocaleTimeString() : 'Real-time'}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', alignItems: 'center' }}>
                  {/* Embedded Satellite Tile Preview */}
                  <div style={{ position: 'relative', borderRadius: '8px', overflow: 'hidden', border: '1px solid #cbd5e1', background: '#0f172a', height: '170px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {shortRange.satellite_telemetry?.nasa_gibs?.tile_snapshot_url ? (
                      <img
                        src={shortRange.satellite_telemetry.nasa_gibs.tile_snapshot_url}
                        alt="Live Satellite Pass Tile"
                        style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.9 }}
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = "https://www.mosdac.gov.in/gallery/images/INSAT-3D_3DR_Sector.png";
                        }}
                      />
                    ) : (
                      <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>🌐 Loading Live Satellite Feed...</div>
                    )}
                    <div style={{ position: 'absolute', bottom: '8px', left: '8px', background: 'rgba(15, 23, 42, 0.85)', padding: '3px 8px', borderRadius: '4px', color: '#38bdf8', fontSize: '0.72rem', fontWeight: 'bold' }}>
                      📷 {shortRange.satellite_telemetry?.nasa_gibs?.layer || 'INSAT-3D Infrared Sector'}
                    </div>
                  </div>

                  {/* AI Vision Telemetry Metrics */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                    <div style={{ background: '#f8faf7', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.73rem', color: '#64748b', display: 'block' }}>👁️ Eye Location (AI Lat/Lon)</span>
                      <strong style={{ fontSize: '1.05rem', color: '#0284c7' }}>
                        {shortRange.satellite_telemetry?.vision_ai_telemetry?.eye_latitude || 17.8}°N, {shortRange.satellite_telemetry?.vision_ai_telemetry?.eye_longitude || 86.1}°E
                      </strong>
                    </div>

                    <div style={{ background: '#f8faf7', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.73rem', color: '#64748b', display: 'block' }}>🧭 Heading Vector</span>
                      <strong style={{ fontSize: '1.05rem', color: '#0f172a' }}>
                        {shortRange.satellite_telemetry?.vision_ai_telemetry?.heading_vector || '315° NW'}
                      </strong>
                    </div>

                    <div style={{ background: '#f8faf7', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.73rem', color: '#64748b', display: 'block' }}>⚡ Forward Translation Speed</span>
                      <strong style={{ fontSize: '1.05rem', color: '#d97706' }}>
                        {shortRange.satellite_telemetry?.vision_ai_telemetry?.translation_speed_kmh || 14.8} km/h ({shortRange.satellite_telemetry?.vision_ai_telemetry?.translation_speed_kt || 8.0} kt)
                      </strong>
                    </div>

                    <div style={{ background: '#f8faf7', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.73rem', color: '#64748b', display: 'block' }}>🌀 Storm Radius & Density</span>
                      <strong style={{ fontSize: '1.05rem', color: '#059669' }}>
                        {shortRange.satellite_telemetry?.vision_ai_telemetry?.storm_radius_km || 245} km ({((shortRange.satellite_telemetry?.vision_ai_telemetry?.cloud_wall_density_score || 0.88) * 100).toFixed(0)}%)
                      </strong>
                    </div>
                  </div>
                </div>
              </div>

              {/* Landfall & Target Highlight Card */}
              <div className="card" style={{ borderTop: '4px solid #059669', background: '#ffffff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid #e2e8f0', paddingBottom: '14px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '1.15rem', fontWeight: 'bold', color: '#0f172a' }}>🎯 Landfall Target & Trajectory Intelligence</span>
                      <span style={{ background: shortRange.is_active_cyclone_warning ? 'rgba(220, 38, 38, 0.1)' : 'rgba(5, 150, 105, 0.1)', color: shortRange.is_active_cyclone_warning ? '#dc2626' : '#059669', padding: '2px 10px', borderRadius: '12px', fontWeight: 'bold', fontSize: '0.78rem' }}>
                        {shortRange.is_active_cyclone_warning ? '🚨 ACTIVE CYCLONE TRACK WARNING' : '🟢 NORMAL / PRECAUTIONARY WATCH'}
                      </span>
                    </div>
                    <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: '#64748b' }}>
                      Calculated from Open-Meteo 7-day hourly telemetry & NASA satellite pass embeddings
                    </p>
                  </div>
                  <button
                    onClick={() => fetchShortRange(true)}
                    disabled={loadingShort}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '6px',
                      background: '#059669',
                      color: '#ffffff',
                      fontWeight: 'bold',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '0.82rem'
                    }}
                  >
                    {loadingShort ? '⚡ Syncing...' : '🔄 Refresh 48h Track'}
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginTop: '16px' }}>
                  <div style={{ background: '#f8faf7', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Primary Target District</span>
                    <strong style={{ fontSize: '1.2rem', color: '#0f172a' }}>{shortRange.predicted_landfall_target_district}</strong>
                  </div>
                  <div style={{ background: '#f8faf7', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Estimated Time to Landfall (ETL)</span>
                    {shortRange.estimated_time_to_landfall_hours ? (
                      <strong style={{ fontSize: '1.15rem', color: '#d97706', display: 'block', marginTop: '4px' }}>
                        🗓️ {shortRange.estimated_landfall_timestamp_ist || shortRange.estimated_landfall_timestamp_formatted}
                      </strong>
                    ) : (
                      <strong style={{ fontSize: '1.2rem', color: '#d97706' }}>No Imminent Landfall</strong>
                    )}
                  </div>
                  <div style={{ background: '#f8faf7', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Projected Peak Wind (at Landfall)</span>
                    <strong style={{ fontSize: '1.2rem', color: '#dc2626' }}>
                      {shortRange.projected_peak_landfall_wind_kt} kt ({Math.round(shortRange.projected_peak_landfall_wind_kt * 1.852)} km/h)
                    </strong>
                  </div>
                  <div style={{ background: '#f8faf7', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Minimum Surface Pressure</span>
                    <strong style={{ fontSize: '1.2rem', color: '#059669' }}>{shortRange.projected_min_landfall_pressure_hpa} hPa</strong>
                  </div>
                </div>
              </div>

              {/* 48-Hour Timeline Scrubber (Layman UX Enhanced) */}
              {(() => {
                const etlHour = Math.round(shortRange?.estimated_time_to_landfall_hours || 7)
                const forwardHour = Math.max(0, etlHour - 3)
                const targetDistrict = shortRange?.predicted_landfall_target_district || "Ganjam"
                const dynamicTrackGradient = generateDynamicTrackGradient(timelineSteps)
                const currentLaymanTime = formatLaymanTime(currentHorizon?.timestamp_formatted, selectedHorizonIdx)
                const currentWindDesc = getLaymanWindDescriptor(currentHorizon?.projected_peak_wind_kmh || Math.round((currentHorizon?.projected_peak_wind_kt || 35) * 1.852))
                const situationalSummary = getLaymanSituationalSummary(currentHorizon, shortRange)
                const milestoneHours = Array.from(new Set([0, 1, 3, forwardHour, etlHour, 12, 18, 24, 36, 48]))
                  .filter(h => h >= 0 && h <= (timelineSteps.length - 1))
                  .sort((a, b) => a - b)

                return (
                  <div className="card" style={{ background: '#ffffff', borderTop: '4px solid #059669', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
                    {/* Header: Title, Layman IST Time & Hazard Severity */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <h3 style={{ margin: 0, fontSize: '1.12rem', color: '#0f172a' }}>⏱️ 48-Hour Interactive Cyclone Timeline</h3>
                          <span style={{ fontSize: '0.72rem', fontWeight: 'bold', background: '#ecfdf5', color: '#059669', padding: '3px 10px', borderRadius: '12px', border: '1px solid #a7f3d0' }}>
                            ⚡ Hour-by-Hour Evolution (0h - 48h)
                          </span>
                        </div>
                        <p style={{ margin: '3px 0 0', fontSize: '0.82rem', color: '#64748b' }}>
                          Drag the timeline or use quick presets below to track how winds, coastal landfall, and district danger change.
                        </p>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                        {/* Selected Time Pill */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', background: '#f8fafc', padding: '6px 14px', borderRadius: '8px', border: '1.5px solid #cbd5e1' }}>
                          <span style={{ fontSize: '0.94rem', fontWeight: 'bold', color: '#0f172a' }}>
                            🗓️ {currentLaymanTime.fullLabel}
                          </span>
                          <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '600' }}>
                            {selectedHorizonIdx === 0 ? '⚡ Live Ingest' : `⏱️ +${selectedHorizonIdx} Hours from Now`}
                          </span>
                        </div>

                        {/* Peak Wind & Damage Severity Pill */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', background: currentWindDesc.badgeBg, padding: '6px 14px', borderRadius: '8px', border: `1.5px solid ${currentWindDesc.border}` }}>
                          <span style={{ fontSize: '0.88rem', fontWeight: 'bold', color: currentWindDesc.badgeColor }}>
                            {currentWindDesc.icon} {currentHorizon?.projected_peak_wind_kmh || 65} km/h ({currentHorizon?.projected_peak_wind_kt || 35} kt)
                          </span>
                          <span style={{ fontSize: '0.72rem', color: currentWindDesc.badgeColor, fontWeight: '600' }}>
                            {currentWindDesc.severity}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Fast Presets & Playback Controls */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        onClick={() => setSelectedHorizonIdx(0)}
                        style={{ padding: '6px 12px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #cbd5e1', background: selectedHorizonIdx === 0 ? '#e2e8f0' : '#f8fafc', cursor: 'pointer', color: '#1e293b' }}
                      >
                        ⏮️ Live Now
                      </button>

                      {forwardHour > 0 && forwardHour !== etlHour && (
                        <button
                          type="button"
                          onClick={() => setSelectedHorizonIdx(forwardHour)}
                          style={{ padding: '6px 12px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #fcd34d', background: selectedHorizonIdx === forwardHour ? '#fde68a' : '#fffbeb', cursor: 'pointer', color: '#92400e' }}
                        >
                          ⚠️ Outer Winds on Coast (+{forwardHour}h Ahead)
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => setSelectedHorizonIdx(etlHour)}
                        style={{ padding: '6px 14px', fontSize: '0.82rem', fontWeight: 'bold', borderRadius: '6px', border: '1.5px solid #f87171', background: selectedHorizonIdx === etlHour ? '#fee2e2' : '#fef2f2', color: '#991b1b', cursor: 'pointer', boxShadow: '0 1px 3px rgba(220,38,38,0.15)' }}
                      >
                        🎯 Peak Eye Landfall (+{etlHour}h Ahead • {targetDistrict})
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedHorizonIdx(Math.min(18, timelineSteps.length - 1))}
                        style={{ padding: '6px 12px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #c4b5fd', background: selectedHorizonIdx === 18 ? '#ddd6fe' : '#f5f3ff', cursor: 'pointer', color: '#5b21b6' }}
                      >
                        🌅 Tomorrow Morning
                      </button>

                      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <button
                          type="button"
                          onClick={() => setSelectedHorizonIdx(prev => Math.max(0, prev - 1))}
                          disabled={selectedHorizonIdx === 0}
                          style={{ padding: '5px 10px', fontSize: '0.78rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#f8fafc', cursor: selectedHorizonIdx === 0 ? 'not-allowed' : 'pointer', color: '#334155' }}
                        >
                          ◀ -1h
                        </button>
                        <button
                          type="button"
                          onClick={() => setIsPlaying(!isPlaying)}
                          style={{ padding: '6px 16px', fontSize: '0.84rem', fontWeight: 'bold', borderRadius: '6px', border: 'none', background: isPlaying ? '#dc2626' : '#059669', color: '#ffffff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
                        >
                          {isPlaying ? '⏸ Pause Timeline' : '▶ Auto-Play 48h'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedHorizonIdx(prev => Math.min(timelineSteps.length - 1, prev + 1))}
                          disabled={selectedHorizonIdx >= timelineSteps.length - 1}
                          style={{ padding: '5px 10px', fontSize: '0.78rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#f8fafc', cursor: selectedHorizonIdx >= timelineSteps.length - 1 ? 'not-allowed' : 'pointer', color: '#334155' }}
                        >
                          +1h ▶
                        </button>
                      </div>
                    </div>

                    {/* Dynamic Multi-Zone Slider Track */}
                    <div style={{ margin: '14px 0 8px' }}>
                      <input
                        type="range"
                        min="0"
                        max={(timelineSteps.length || 49) - 1}
                        step="1"
                        value={selectedHorizonIdx}
                        onChange={(e) => setSelectedHorizonIdx(Number(e.target.value))}
                        style={{
                          width: '100%',
                          height: '14px',
                          borderRadius: '7px',
                          background: dynamicTrackGradient,
                          cursor: 'pointer',
                          outline: 'none',
                          boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.2)'
                        }}
                      />

                      {/* Dynamic Lifecycle Phase Track Labels */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#64748b', marginTop: '4px', fontWeight: '600' }}>
                        <span>🔵 Approaching Ocean</span>
                        <span>🟠 Coastal Gale Alert</span>
                        <span style={{ color: '#dc2626', fontWeight: 'bold' }}>🔴 Landfall Strike (+{etlHour}h Ahead)</span>
                        <span>🟣 Inland Decay across Western Odisha</span>
                      </div>

                      {/* Milestone Cards Bar with Dynamic Badges */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
                        {milestoneHours.map((milestoneHour) => {
                          const actualIdx = Math.min(milestoneHour, timelineSteps.length - 1)
                          const item = timelineSteps[actualIdx]
                          const isSelected = selectedHorizonIdx === actualIdx
                          const isLandfall = milestoneHour === etlHour
                          const isForward = milestoneHour === forwardHour && forwardHour !== 0 && forwardHour !== etlHour
                          const layman = formatLaymanTime(item?.timestamp_formatted, milestoneHour)
                          const lCode = item?.lifecycle_code

                          let badgeLabel = '🌊 Approaching'
                          let badgeBg = '#e0f2fe'
                          let badgeColor = '#0369a1'

                          if (isLandfall || lCode === 'CORE_LANDFALL') {
                            badgeLabel = '🔴 Landfall'
                            badgeBg = '#fee2e2'
                            badgeColor = '#dc2626'
                          } else if (isForward || lCode === 'FORWARD_EYEWALL') {
                            badgeLabel = '🟠 Outer Gale'
                            badgeBg = '#fef3c7'
                            badgeColor = '#d97706'
                          } else if (lCode === 'INLAND_WEAKENING') {
                            badgeLabel = '🟣 Inland'
                            badgeBg = '#ede9fe'
                            badgeColor = '#7c3aed'
                          }

                          const timeSubtitle = milestoneHour === 0 
                            ? 'Live Now' 
                            : (isLandfall ? `Landfall (~${milestoneHour}h)` : `+${milestoneHour} Hours`);

                          return (
                            <div
                              key={milestoneHour}
                              onClick={() => setSelectedHorizonIdx(actualIdx)}
                              style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                cursor: 'pointer',
                                padding: '8px 10px',
                                minWidth: '88px',
                                borderRadius: '8px',
                                background: isSelected
                                  ? 'rgba(5, 150, 105, 0.15)'
                                  : isLandfall
                                    ? 'rgba(239, 68, 68, 0.08)'
                                    : '#f8fafc',
                                border: isSelected
                                  ? '2px solid #059669'
                                  : isLandfall
                                    ? '1.5px solid #ef4444'
                                    : '1px solid #e2e8f0',
                                transition: 'all 0.15s',
                                boxShadow: isSelected ? '0 0 0 2px rgba(5, 150, 105, 0.25)' : 'none'
                              }}
                            >
                              <span style={{ fontSize: '0.66rem', fontWeight: 'bold', background: badgeBg, color: badgeColor, padding: '1px 6px', borderRadius: '4px', whiteSpace: 'nowrap' }}>
                                {badgeLabel}
                              </span>
                              <strong style={{ color: isSelected ? '#059669' : isLandfall ? '#dc2626' : '#0f172a', fontSize: '0.92rem', marginTop: '4px' }}>
                                {layman.timeOnly || 'Live'}
                              </strong>
                              <span style={{ color: '#475569', fontSize: '0.72rem', fontWeight: '600', marginTop: '1px', whiteSpace: 'nowrap' }}>
                                {timeSubtitle}
                              </span>
                              <span style={{ color: '#94a3b8', fontSize: '0.68rem', marginTop: '1px', whiteSpace: 'nowrap' }}>
                                {layman.relativeDay}
                              </span>
                            </div>
                          )
                        })}
                      </div>
                    </div>

                  </div>
                )
              })()}

              {/* Scrubbed Horizon Matrix Table */}
              {currentHorizon && (
                <div className="card" style={{ background: '#ffffff' }}>
                  {/* Single Unified Situational Summary Banner */}
                  {(() => {
                    const currentWindDesc = getLaymanWindDescriptor(currentHorizon?.projected_peak_wind_kmh || Math.round((currentHorizon?.projected_peak_wind_kt || 35) * 1.852));
                    const situationalSummary = getLaymanSituationalSummary(currentHorizon, shortRange);
                    const currentLaymanTime = formatLaymanTime(currentHorizon?.timestamp_formatted, selectedHorizonIdx);

                    return (
                      <div style={{
                        background: currentWindDesc.badgeBg,
                        border: `1.5px solid ${currentWindDesc.border}`,
                        borderRadius: '8px',
                        padding: '10px 14px',
                        marginBottom: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        flexWrap: 'wrap',
                        gap: '10px'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                          <span style={{
                            background: currentWindDesc.badgeColor,
                            color: '#ffffff',
                            padding: '3px 10px',
                            borderRadius: '6px',
                            fontWeight: 'bold',
                            fontSize: '0.78rem',
                            letterSpacing: '0.3px',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            {currentWindDesc.icon} {currentHorizon?.lifecycle_phase || currentWindDesc.severity}
                          </span>
                          <span style={{ fontSize: '0.82rem', color: currentWindDesc.badgeColor, fontWeight: '500', lineHeight: '1.4' }}>
                            {situationalSummary}
                          </span>
                        </div>
                        <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: currentWindDesc.badgeColor, background: 'rgba(255,255,255,0.7)', padding: '2px 8px', borderRadius: '4px' }}>
                          {currentLaymanTime.relativeDay} • {selectedHorizonIdx === 0 ? 'Live Now' : `+${selectedHorizonIdx}h Ahead`}
                        </span>
                      </div>
                    );
                  })()}

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                    <h3 style={{ margin: 0, fontSize: '0.98rem', color: '#0f172a' }}>
                      📊 District Risk Matrix at {formatToIST(currentHorizon.timestamp_formatted) || currentHorizon.timestamp_formatted}
                    </h3>
                    <div style={{ display: 'flex', gap: '14px', fontSize: '0.82rem' }}>
                      <span>Peak Wind: <strong style={{ color: '#d97706' }}>{currentHorizon.projected_peak_wind_kt || 0} kt ({Math.round((currentHorizon.projected_peak_wind_kt || 0) * 1.852)} km/h)</strong></span>
                      <span>Target Evac: <strong style={{ color: '#dc2626' }}>{(currentHorizon.total_state_evacuation_target || 0).toLocaleString()}</strong></span>
                      <span>MCS Shelters: <strong style={{ color: '#059669' }}>{currentHorizon.total_shelters_activated || 0}</strong></span>
                      <span>NDRF Teams: <strong style={{ color: '#0284c7' }}>{currentHorizon.total_ndrf_teams_deployed || 0}</strong></span>
                    </div>
                  </div>

                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                      <thead>
                        <tr style={{ background: '#f1f5f9', color: '#0f172a', textTransform: 'uppercase', fontSize: '0.75rem' }}>
                          <th style={{ padding: '8px 10px', textAlign: 'left' }}>District</th>
                          <th style={{ padding: '8px 10px', textAlign: 'left' }}>Distance</th>
                          <th style={{ padding: '8px 10px', textAlign: 'left' }}>Risk Score</th>
                          <th style={{ padding: '8px 10px', textAlign: 'left' }}>Status Pill</th>
                          <th style={{ padding: '8px 10px', textAlign: 'left' }}>Proj Wind (kt / km/h)</th>
                          <th style={{ padding: '8px 10px', textAlign: 'left' }}>Evac Target</th>
                          <th style={{ padding: '8px 10px', textAlign: 'left' }}>MCS Shelters</th>
                          <th style={{ padding: '8px 10px', textAlign: 'left' }}>NDRF Teams</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentHorizon.district_matrix?.map((d, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', background: idx % 2 === 0 ? '#ffffff' : '#f8faf7' }}>
                            <td style={{ padding: '8px 10px', fontWeight: 'bold', color: '#0f172a' }}>{d.district}</td>
                            <td style={{ padding: '8px 10px', color: '#64748b' }}>{d.coastal_distance_km} km</td>
                            <td style={{ padding: '8px 10px', fontWeight: 'bold', color: (d.predicted_risk_score || 0) > 0.45 ? '#dc2626' : '#059669' }}>
                              {((d.predicted_risk_score || 0) * 100).toFixed(1)}%
                            </td>
                            <td style={{ padding: '8px 10px' }}>
                              <span style={{
                                fontSize: '0.72rem',
                                fontWeight: 'bold',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                background: (d.predicted_risk_score || 0) >= 0.45 ? '#fee2e2' : ((d.predicted_risk_score || 0) >= 0.25 ? '#fef3c7' : '#d1fae5'),
                                color: (d.predicted_risk_score || 0) >= 0.45 ? '#dc2626' : ((d.predicted_risk_score || 0) >= 0.25 ? '#d97706' : '#059669')
                              }}>
                                {d.alert_status_pill || 'Normal'}
                              </span>
                            </td>
                            <td style={{ padding: '8px 10px', color: '#d97706', fontWeight: 'bold' }}>
                              {d.projected_wind_kt || 0} kt ({Math.round((d.projected_wind_kt || 0) * 1.852)} km/h)
                            </td>
                            <td style={{ padding: '8px 10px', fontWeight: 'bold' }}>{(d.people_to_evacuate || 0).toLocaleString()}</td>
                            <td style={{ padding: '8px 10px', color: '#059669', fontWeight: 'bold' }}>{d.multipurpose_shelters_required || 0}</td>
                            <td style={{ padding: '8px 10px', color: '#0284c7', fontWeight: 'bold' }}>{d.ndrf_teams_required || 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Mode 2: 60-Day Seasonal Outlook View */}
      {activeMode === '60day' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {loadingSeasonal && !seasonal ? (
            <div className="card loading" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="spinner-icon"></div> Analyzing IMD 66 Best-Track Database & Bay of Bengal SST Anomalies...
            </div>
          ) : seasonal && (
            <>
              {/* 60-Day Probability Summary Header */}
              <div className="card" style={{ borderTop: '4px solid #059669', background: '#ffffff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid #e2e8f0', paddingBottom: '14px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '1.15rem', fontWeight: 'bold', color: '#0f172a' }}>🗓️ 60-Day Seasonal Cyclonogenesis Outlook</span>
                      <span style={{ background: seasonal.overall_60day_threat_level === 'HIGH' ? 'rgba(217, 119, 6, 0.1)' : 'rgba(5, 150, 105, 0.1)', color: seasonal.overall_60day_threat_level === 'HIGH' ? '#d97706' : '#059669', padding: '2px 10px', borderRadius: '12px', fontWeight: 'bold', fontSize: '0.78rem' }}>
                        {seasonal.overall_60day_threat_level} SEASONAL THREAT
                      </span>
                    </div>
                    <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: '#64748b' }}>
                      Target Window: {seasonal.forecast_window} | Analyzed 66 Historical IMD Best-Track Events
                    </p>
                  </div>
                  <button
                    onClick={() => fetchSeasonal(true)}
                    disabled={loadingSeasonal}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '6px',
                      background: '#059669',
                      color: '#ffffff',
                      fontWeight: 'bold',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '0.82rem'
                    }}
                  >
                    {loadingSeasonal ? '⚡ Syncing...' : '🔄 Refresh Seasonal Outlook'}
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginTop: '16px' }}>
                  {seasonal.monthly_cyclonogenesis_probabilities?.map((m, idx) => (
                    <div key={idx} style={{ background: '#f8faf7', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#0f172a' }}>{m.month} Probability</span>
                        <span style={{ fontSize: '0.72rem', background: 'rgba(5, 150, 105, 0.1)', color: '#059669', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>
                          {m.status}
                        </span>
                      </div>
                      <strong style={{ fontSize: '1.4rem', color: m.cyclonogenesis_probability_pct > 30 ? '#d97706' : '#059669' }}>
                        {m.cyclonogenesis_probability_pct}%
                      </strong>
                    </div>
                  ))}
                  <div style={{ background: '#f8faf7', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.78rem', color: '#64748b', display: 'block' }}>Bay of Bengal Sea Surface Temp</span>
                    <strong style={{ fontSize: '1.4rem', color: '#0284c7' }}>
                      {seasonal.sea_surface_temp_c}°C (+{seasonal.sst_anomaly_c}°C Anomaly)
                    </strong>
                  </div>
                </div>
              </div>

              {/* 10-District Historical Landfall Vulnerability Ranking Table */}
              <div className="card" style={{ background: '#ffffff' }}>
                <h3 style={{ margin: '0 0 12px', fontSize: '1rem', color: '#0f172a' }}>
                  🏆 10-District Historical Cyclone Vulnerability Rankings (IMD Best-Track)
                </h3>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                    <thead>
                      <tr style={{ background: '#f1f5f9', color: '#0f172a', textTransform: 'uppercase', fontSize: '0.75rem' }}>
                        <th style={{ padding: '8px 10px', textAlign: 'left' }}>Rank</th>
                        <th style={{ padding: '8px 10px', textAlign: 'left' }}>District</th>
                        <th style={{ padding: '8px 10px', textAlign: 'left' }}>Proximity</th>
                        <th style={{ padding: '8px 10px', textAlign: 'left' }}>Vulnerability Score</th>
                        <th style={{ padding: '8px 10px', textAlign: 'left' }}>Seasonal Threat Tier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {seasonal.district_vulnerability_rankings?.map((d, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', background: idx % 2 === 0 ? '#ffffff' : '#f8faf7' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 'bold', color: '#059669' }}>#{d.rank}</td>
                          <td style={{ padding: '8px 10px', fontWeight: 'bold', color: '#0f172a' }}>{d.district}</td>
                          <td style={{ padding: '8px 10px', color: '#64748b' }}>{d.coastal_distance_km} km</td>
                          <td style={{ padding: '8px 10px', fontWeight: 'bold' }}>{(d.historical_landfall_vulnerability_score * 100).toFixed(0)}%</td>
                          <td style={{ padding: '8px 10px' }}>
                            <span style={{ fontSize: '0.72rem', fontWeight: 'bold', padding: '2px 8px', borderRadius: '4px', background: d.seasonal_risk_category === 'CRITICAL RISK' ? '#fee2e2' : (d.seasonal_risk_category === 'HIGH EXPOSURE' ? '#fef3c7' : '#d1fae5'), color: d.seasonal_risk_category === 'CRITICAL RISK' ? '#dc2626' : (d.seasonal_risk_category === 'HIGH EXPOSURE' ? '#d97706' : '#059669') }}>
                              {d.seasonal_risk_category}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Pre-Season Administrative Preparedness Checklist (RAG SOPs) */}
              <div className="card" style={{ background: '#ffffff', borderLeft: '4px solid #059669' }}>
                <h3 style={{ margin: '0 0 12px', fontSize: '1rem', color: '#0f172a' }}>
                  📋 Pre-Cyclone Season Administrative Preparedness Directives (OSDMA / IMD SOPs)
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
                  {seasonal.preseason_readiness_checklist?.map((item, idx) => (
                    <div key={idx} style={{ background: '#f8faf7', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <strong style={{ color: '#059669', fontSize: '0.85rem', display: 'block', marginBottom: '4px' }}>
                        {item.phase}
                      </strong>
                      <span style={{ fontSize: '0.81rem', color: '#475569', lineHeight: '1.4' }}>
                        {item.action}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* JSON Payload Export Modal */}
      {showJsonModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.75)',
          display: 'flex',
          alignItems: 'center',
          justify: 'center',
          zIndex: 9999,
          padding: '20px'
        }}>
          <div style={{
            background: '#0f172a',
            color: '#f8fafc',
            borderRadius: '12px',
            width: '100%',
            maxWidth: '850px',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.5)',
            border: '1px solid #334155'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid #334155' }}>
              <span style={{ fontSize: '1.05rem', fontWeight: 'bold', color: '#38bdf8' }}>
                📄 System JSON Payload (API Consumption Format)
              </span>
              <button
                onClick={() => setShowJsonModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer', fontWeight: 'bold' }}
              >
                ✕
              </button>
            </div>
            <div style={{ overflowY: 'auto', padding: '20px', flex: 1 }}>
              <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: '0.82rem', color: '#4ade80', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {JSON.stringify({
                  unified_survey_summary: summaryData,
                  forecast_trajectory_matrix: unifiedSurvey?.forecast_trajectory_matrix,
                  district_risk_matrix: unifiedSurvey?.district_risk_matrix || unifiedSurvey?.district_survey_matrix,
                  sop_directives: unifiedSurvey?.sop_directives
                }, null, 2)}
              </pre>
            </div>
            <div style={{ padding: '14px 20px', borderTop: '1px solid #334155', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify({
                    unified_survey_summary: summaryData,
                    forecast_trajectory_matrix: unifiedSurvey?.forecast_trajectory_matrix,
                    district_risk_matrix: unifiedSurvey?.district_risk_matrix || unifiedSurvey?.district_survey_matrix,
                    sop_directives: unifiedSurvey?.sop_directives
                  }, null, 2))
                  alert('JSON Payload copied to clipboard!')
                }}
                style={{ padding: '8px 16px', background: '#0284c7', color: '#ffffff', borderRadius: '6px', border: 'none', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.82rem' }}
              >
                📋 Copy JSON to Clipboard
              </button>
              <button
                onClick={() => setShowJsonModal(false)}
                style={{ padding: '8px 16px', background: '#334155', color: '#ffffff', borderRadius: '6px', border: 'none', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.82rem' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

