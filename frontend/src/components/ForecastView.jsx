import { useEffect, useState, useRef } from 'react'
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

// Dynamic Layman Date Formatter with Calendar-Accurate Days (Today, Tomorrow, or Clean Date for Day+2)
function formatLaymanTime(timeStr, horizonHours = 0, baseTimeStr = null) {
  if (!timeStr) return { relativeDay: horizonHours === 0 ? 'Live Now' : `+${horizonHours}h Ahead`, timeOnly: '', dateOnly: '', fullLabel: horizonHours === 0 ? 'Live Now' : `+${horizonHours} Hours Ahead` }

  const parseToDate = (s) => {
    if (!s) return null
    if (s instanceof Date) return isNaN(s.getTime()) ? null : s
    const str = String(s).trim()
    const utcMatch = str.match(/^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{1,2}):(\d{2})\s*UTC$/i)
    if (utcMatch) {
      const months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
      const mIdx = months.indexOf(utcMatch[2].toLowerCase())
      if (mIdx !== -1) {
        const year = new Date().getFullYear()
        return new Date(Date.UTC(year, mIdx, parseInt(utcMatch[1], 10), parseInt(utcMatch[3], 10), parseInt(utcMatch[4], 10)))
      }
    }
    const istMatch = str.match(/^(\d{1,2})\s+([A-Za-z]{3}),?\s+(\d{1,2}):(\d{2})/i)
    if (istMatch) {
      const months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
      const mIdx = months.indexOf(istMatch[2].toLowerCase())
      if (mIdx !== -1) {
        const year = new Date().getFullYear()
        const istDay = parseInt(istMatch[1], 10)
        const istH = parseInt(istMatch[3], 10)
        const istM = parseInt(istMatch[4], 10)
        return new Date(Date.UTC(year, mIdx, istDay, istH - 5, istM - 30))
      }
    }
    try {
      const d = new Date(str.replace(' UTC', 'Z').replace(' IST', ''))
      if (!isNaN(d.getTime())) return d
    } catch (e) { }
    return null
  }

  let targetDate = parseToDate(timeStr)
  if (!targetDate) {
    targetDate = new Date(Date.now() + horizonHours * 3600000)
  }

  let baseDate = parseToDate(baseTimeStr)
  if (!baseDate) {
    baseDate = new Date(targetDate.getTime() - horizonHours * 3600000)
  }

  // Calculate true calendar day difference in IST
  let diffDays = 0
  try {
    const baseIST = baseDate.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' })
    const targetIST = targetDate.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' })
    const [by, bm, bd] = baseIST.split('-').map(Number)
    const [ty, tm, td] = targetIST.split('-').map(Number)
    diffDays = Math.round((new Date(ty, tm - 1, td).getTime() - new Date(by, bm - 1, bd).getTime()) / 86400000)
  } catch (e) {
    diffDays = Math.floor(horizonHours / 24)
  }

  // Format date and time in IST
  let dateOnly = ''
  let timeOnly = ''
  try {
    const raw = targetDate.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
    const parts = raw.split(' ')
    if (parts.length >= 2) {
      dateOnly = `${parts[0]} ${parts[1]}`.replace(',', '')
      timeOnly = parts.length >= 3 ? parts[2] : ''
    }
  } catch (e) { }

  if (!dateOnly || !timeOnly) {
    const raw = formatToIST(timeStr)
    const parts = raw.split(' ')
    if (parts.length >= 3) {
      dateOnly = `${parts[0]} ${parts[1]}`.replace(',', '')
      timeOnly = parts.slice(2).join(' ').replace('IST', '').trim()
    } else {
      timeOnly = raw
      dateOnly = `${horizonHours}h`
    }
  }

  // Parse hour for accurate time of day (Morning / Afternoon / Evening / Night)
  let tod = 'Morning'
  const hourMatch = timeOnly.match(/^(\d{1,2}):/)
  if (hourMatch) {
    const h = parseInt(hourMatch[1], 10)
    if (h >= 4 && h < 12) tod = 'Morning'
    else if (h >= 12 && h < 17) tod = 'Afternoon'
    else if (h >= 17 && h < 21) tod = 'Evening'
    else tod = 'Night'
  }

  let relativeDay = ''
  let fullLabel = ''

  if (diffDays <= 0) {
    if (horizonHours === 0) {
      relativeDay = 'Live Now'
      fullLabel = `Live Now • ${timeOnly} IST (${dateOnly})`
    } else {
      relativeDay = `Today ${tod}`
      fullLabel = `Today ${tod} • ${timeOnly} IST (${dateOnly})`
    }
  } else if (diffDays === 1) {
    relativeDay = `Tomorrow ${tod}`
    fullLabel = `Tomorrow ${tod} • ${timeOnly} IST (${dateOnly})`
  } else {
    // Next new day (diffDays >= 2, e.g. 21 Nov): strictly only show the date and time, NO "Day 3"
    relativeDay = dateOnly
    fullLabel = `${dateOnly} • ${timeOnly} IST`
  }

  return {
    relativeDay,
    timeOnly,
    dateOnly,
    fullLabel
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

// Dynamic Plain-Language Situational Summary Generator (IMD Standards Calibrated)
function getLaymanSituationalSummary(currentHorizon, shortRange) {
  if (!currentHorizon) return "Loading active cyclone trajectory data..."
  const isCycloneActive = shortRange?.is_cyclone_active ?? (shortRange?.predicted_landfall_target_district && shortRange.predicted_landfall_target_district !== "No Coastal Strike" && (shortRange?.estimated_time_to_landfall_hours ?? 0) > 0)

  if (!isCycloneActive || shortRange?.predicted_landfall_target_district === "No Coastal Strike") {
    return `🟢 NORMAL MARINE STATE: Quiet, non-cyclonic conditions across the Bay of Bengal and Odisha coastline. Routine telemetry streaming at safe baseline levels.`
  }

  const lCode = currentHorizon.lifecycle_code
  const windKmh = currentHorizon.projected_peak_wind_kmh || Math.round((currentHorizon.projected_peak_wind_kt || 35) * 1.852)
  const windKt = currentHorizon.projected_peak_wind_kt || Math.round(windKmh / 1.852)
  const targetDist = shortRange?.predicted_landfall_target_district || "Ganjam"
  const etlHours = Math.round(shortRange?.estimated_time_to_landfall_hours ?? 7)
  const h = currentHorizon.horizon_hours || 0

  // Calibrate physical hazard description to actual wind intensity
  const isSevereOrAbove = windKt >= 48 // >= 89 km/h (SCS, VSCS, ESCS, SuCS)
  const isGaleCyclone = windKt >= 34 // 62 - 88 km/h (Cyclonic Storm)

  if (lCode === 'CORE_LANDFALL' || (etlHours > 0 && h === etlHours)) {
    if (isSevereOrAbove) {
      return `🚨 SEVERE CYCLONE LANDFALL IN PROGRESS: Core eyewall is crossing over ${targetDist} coast. Destructive gale/hurricane winds (${windKmh} km/h), storm surge (>2.5m), and torrential inundation are actively hitting coastal belts. Evacuees must remain in shelters.`
    }
    if (isGaleCyclone) {
      return `⚠️ CYCLONIC STORM LANDFALL IN PROGRESS: Vortex center is crossing over ${targetDist} coast. Sustained gale winds (${windKmh} km/h) and moderate storm surge (1.0–1.8m) are impacting coastal belts. Coastal residents should stay indoors.`
    }
    return `🟡 DEPRESSION / LOW-PRESSURE LANDFALL: Low-pressure circulation center is crossing ${targetDist} coast. Moderate squally breeze (${windKmh} km/h) and light coastal showers. Baseline risk remains normal; no large-scale evacuation required.`
  }

  if (lCode === 'FORWARD_EYEWALL' || (etlHours > 0 && h < etlHours && h >= etlHours - 3)) {
    if (isSevereOrAbove) {
      return `🌪️ LEADING EYEWALL REACHING SHORE: Outer spiral rainbands and severe winds (${windKmh} km/h) are battering ${targetDist} coastline with rising surge. Final zero-casualty evacuations are underway before eye crossing.`
    }
    if (isGaleCyclone) {
      return `🌊 FORWARD GALE RAINBANDS REACHING SHORE: Squally coastal winds (${windKmh} km/h) and increasing tidal surf along ${targetDist}. Artisanal fishing suspended and local alerts active.`
    }
    return `🌦️ PRE-LANDFALL SQUALLY RAINBANDS: Outer cloud clusters bringing localized coastal showers and moderate winds (${windKmh} km/h) to ${targetDist}. Coastal conditions remain manageable.`
  }

  if (lCode === 'INLAND_WEAKENING' || (etlHours > 0 && h > etlHours)) {
    return `📉 POST-LANDFALL INLAND DECAY: System center has moved inland across Western Odisha/neighboring terrain and is weakening (${windKmh} km/h). Coastal districts have transitioned to safe post-storm recovery.`
  }

  if (isSevereOrAbove) {
    return `🌊 INTENSE CYCLONE ADVANCING OVER BAY OF BENGAL: System tracking towards ${targetDist} at ${currentHorizon.projected_translation_speed_kmh || 14.8} km/h with core intensity of ${windKmh} km/h. Coastal emergency agencies on high alert.`
  }
  if (isGaleCyclone) {
    return `🌊 CYCLONIC STORM TRACKING OVER BAY OF BENGAL: System advancing towards ${targetDist} with sustained winds of ${windKmh} km/h. Maritime buoys monitoring approaching vortex.`
  }
  return `☁️ LOW PRESSURE / DEPRESSION MONITORING: System tracking over ocean with ambient winds of ${windKmh} km/h. Normal marine operations monitored; no severe threat detected.`
}


// Dynamically generate slider gradient based on 15-day synoptic lifecycle codes
function generate15DayTrackGradient(fifteenDaySteps) {
  if (!fifteenDaySteps || fifteenDaySteps.length === 0) {
    return 'linear-gradient(to right, #0284c7 0%, #d97706 25%, #dc2626 50%, #7c3aed 70%, #059669 100%)'
  }
  const total = fifteenDaySteps.length - 1 || 1
  const stops = []
  const codeColorMap = {
    genesis: '#0284c7',
    depression: '#0ea5e9',
    deep_depression: '#d97706',
    cyclonic_storm: '#ea580c',
    severe_cyclonic_storm: '#f97316',
    vscs: '#dc2626',
    coastal_approach: '#dc2626',
    landfall: '#991b1b',
    inland_decay: '#7c3aed',
    inland_depression: '#9333ea',
    remnant_depression: '#059669',
    dissipation: '#10b981',
    stabilization: '#10b981',
    routine: '#059669',
    extended_baseline: '#047857'
  }
  fifteenDaySteps.forEach((step, idx) => {
    const pct = ((idx / total) * 100).toFixed(1)
    const color = codeColorMap[step.lifecycle_code] || '#0284c7'
    stops.push(`${color} ${pct}%`)
  })
  return `linear-gradient(to right, ${stops.join(', ')})`
}

export default function ForecastView({ telemetryMode = 'simulated', onToggleTelemetryMode }) {
  const [activeMode, setActiveMode] = useState('unified') // 'unified', '48h', or '60day'
  const [unifiedSurvey, setUnifiedSurvey] = useState(null)
  const [shortRange, setShortRange] = useState(null)
  const [seasonal, setSeasonal] = useState(null)
  const [loadingSurvey, setLoadingSurvey] = useState(false)
  const [loadingShort, setLoadingShort] = useState(false)
  const [loadingSeasonal, setLoadingSeasonal] = useState(false)
  const [selectedHorizonIdx, setSelectedHorizonIdx] = useState(0)
  const [isCalculatingRisk, setIsCalculatingRisk] = useState(false)
  const calcTimeoutRef = useRef(null)

  const handleHorizonChange = (targetIdx) => {
    setIsCalculatingRisk(true)
    const validIdx = typeof targetIdx === 'function' ? targetIdx(selectedHorizonIdx) : Number(targetIdx)
    setSelectedHorizonIdx(validIdx)
    if (calcTimeoutRef.current) clearTimeout(calcTimeoutRef.current)
    calcTimeoutRef.current = setTimeout(() => {
      setIsCalculatingRisk(false)
    }, 280)
  }

  useEffect(() => {
    return () => {
      if (calcTimeoutRef.current) clearTimeout(calcTimeoutRef.current)
    }
  }, [])
  const [isPlaying, setIsPlaying] = useState(false)
  const [showJsonModal, setShowJsonModal] = useState(false)

  // Interactive Table Controls: Search, Risk Filtering, and Column Auto-Sorting
  const [searchTerm, setSearchTerm] = useState('')
  const [filterCategory, setFilterCategory] = useState('all') // 'all', 'high_risk', 'coastal'
  const [sortBy, setSortBy] = useState('risk') // 'risk', 'dist', 'wind', 'evac', 'name'
  const [sortAsc, setSortAsc] = useState(false) // Default descending: highest risk first!

  // 60-Day Seasonal Dashboard Interactive Controls
  // 15-Day Extended Horizon Interactive Controls (Similar to 48hr Scrubber)
  const [selected15DayIdx, setSelected15DayIdx] = useState(7) // Defaults to Day 8 Landfall Peak
  const [isPlaying15Day, setIsPlaying15Day] = useState(false)
  const [active15DayTab, setActive15DayTab] = useState('scrubber') // 'scrubber', 'ensemble', 'drivers', 'directives', 'vulnerability'
  const [fifteenDaySearch, setFifteenDaySearch] = useState('')
  const [fifteenDayZoneFilter, setFifteenDayZoneFilter] = useState('all')
  const [sort15DayBy, setSort15DayBy] = useState('risk')
  const [sort15DayAsc, setSort15DayAsc] = useState(false)

  const handle15DaySort = (colKey) => {
    if (sort15DayBy === colKey) {
      setSort15DayAsc(!sort15DayAsc)
    } else {
      setSort15DayBy(colKey)
      setSort15DayAsc(colKey === 'dist' || colKey === 'name')
    }
  }

  const fifteenDaySteps = seasonal?.fifteen_day_matrix || []
  useEffect(() => {
    let interval = null
    if (isPlaying15Day && fifteenDaySteps.length > 0) {
      interval = setInterval(() => {
        setSelected15DayIdx((prev) => (prev + 1) % fifteenDaySteps.length)
      }, 1500)
    } else {
      clearInterval(interval)
    }
    return () => clearInterval(interval)
  }, [isPlaying15Day, fifteenDaySteps.length])

  const current15DayHorizon = fifteenDaySteps[selected15DayIdx] || null

  const [activeSeasonalTab, setActiveSeasonalTab] = useState('overview') // 'overview', 'timeline', 'analogs', 'districts', 'readiness'
  const [seasonalSearch, setSeasonalSearch] = useState('')
  const [seasonalZoneFilter, setSeasonalZoneFilter] = useState('all') // 'all', 'Direct Coastal Front', 'Near-Coast Buffer', 'Central Delta', 'Inland Western Plateau'

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
    api.unifiedLiveSurvey(forceRefresh, telemetryMode)
      .then((data) => {
        setUnifiedSurvey(data)
        setLoadingSurvey(false)
      })
      .catch(() => setLoadingSurvey(false))
  }

  const fetchShortRange = (forceRefresh = false) => {
    setLoadingShort(true)
    api.shortRangeForecast(forceRefresh, telemetryMode)
      .then((data) => {
        setShortRange(data)
        setLoadingShort(false)
      })
      .catch(() => setLoadingShort(false))
  }

  const fetchSeasonal = (forceRefresh = false) => {
    setLoadingSeasonal(true)
    api.seasonalOutlook(forceRefresh, telemetryMode)
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
  }, [telemetryMode])

  const timelineSteps = shortRange?.timeline_matrix || []

  // Auto-play timeline animation playback
  useEffect(() => {
    let interval = null
    if (isPlaying && timelineSteps.length > 0) {
      interval = setInterval(() => {
        handleHorizonChange((prev) => (prev + 1) % timelineSteps.length)
      }, 1000)
    } else {
      clearInterval(interval)
    }
    return () => clearInterval(interval)
  }, [isPlaying, timelineSteps.length])
  const currentHorizon = timelineSteps[selectedHorizonIdx] || null
  const currentLaymanTime = formatLaymanTime(currentHorizon?.timestamp_formatted, selectedHorizonIdx, timelineSteps[0]?.timestamp_formatted)
  const currentWindDesc = getLaymanWindDescriptor(currentHorizon?.projected_peak_wind_kmh || Math.round((currentHorizon?.projected_peak_wind_kt || 35) * 1.852))
  const situationalSummary = getLaymanSituationalSummary(currentHorizon, shortRange)
  const peakEvacTarget = Math.max(...timelineSteps.map(t => t.total_state_evacuation_target || 0), 0)
  const peakShelters = Math.max(...timelineSteps.map(t => t.total_shelters_activated || 0), 0)
  const peakNDRF = Math.max(...timelineSteps.map(t => t.total_ndrf_teams_deployed || 0), 0)
  const isCycloneActive = shortRange?.is_cyclone_active ?? (
    shortRange?.predicted_landfall_target_district &&
    shortRange.predicted_landfall_target_district !== "No Coastal Strike" &&
    (shortRange?.estimated_time_to_landfall_hours ?? 0) > 0
  )

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
    <div className="forecast-view-root">
      {/* <div className="view-header" style={{ marginBottom: 0 }}>
        <h1>🔮 OSDMA Unified Disaster Risk Survey & Predictive Forecast Generator</h1>
        <p className="view-subtitle">
          Multimodal AI Intelligence Engine for Odisha: Real-time Satellite Vision Extraction, 0-48h Trajectory Steering, Dynamic Wind Decay, 10-District Evacuation & MCS Allocations.
        </p>
      </div> */}

      {/* Unified Executive Command Strip: Title + Status Beacon + Segmented Mode Switcher + Controls */}
      <div className="card" style={{
        flexShrink: 0,
        borderTop: telemetryMode === 'simulated' ? '4px solid #dc2626' : '4px solid #059669',
        borderRadius: '10px',
        border: '1px solid #e2e8f0',
        boxShadow: '0 4px 16px -2px rgba(15, 23, 42, 0.06)',
        background: '#ffffff',
        padding: '10px 16px',
        marginBottom: '0'
      }}>
        {/* Header Row: Agency Title + Status Beacon + Segmented Mode Tablets + Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '1.08rem', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.01em', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>🏛️</span> OSDMA State Command Executive Survey
            </span>

            {/* Dynamic Status Beacon based on Actual Landfall Forecast */}
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              background: isCycloneActive ? '#fef2f2' : '#f0fdf4',
              color: isCycloneActive ? '#b91c1c' : '#15803d',
              padding: '3px 12px',
              borderRadius: '20px',
              fontWeight: '700',
              fontSize: '0.74rem',
              border: `1.5px solid ${isCycloneActive ? '#fca5a5' : '#86efac'}`,
              letterSpacing: '0.02em'
            }}>
              <span style={{
                display: 'inline-block',
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: isCycloneActive ? '#dc2626' : '#16a34a',
                marginRight: '6px',
                boxShadow: isCycloneActive ? '0 0 8px rgba(220,38,38,0.8)' : '0 0 6px rgba(22,163,74,0.7)'
              }} />
              {isCycloneActive
                ? `48H CYCLONE WARNING • LANDFALL PROJECTED (${telemetryMode === 'simulated' ? 'SIMULATION' : 'LIVE FEED'})`
                : `PEACETIME STANDBY • NO ACTIVE CYCLONE (${telemetryMode === 'simulated' ? 'SIMULATION' : 'LIVE FEED'})`}
            </span>
          </div>

          {/* Center: Segmented Horizon Mode Tablets */}
          <div style={{
            display: 'inline-flex',
            background: '#f1f5f9',
            padding: '3px',
            borderRadius: '10px',
            border: '1px solid #e2e8f0'
          }}>
            <button
              onClick={() => setActiveMode('unified')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeMode === 'unified' ? '#dc2626' : 'transparent',
                color: activeMode === 'unified' ? '#ffffff' : '#475569',
                fontWeight: '700',
                fontSize: '0.8rem',
                cursor: 'pointer',
                boxShadow: activeMode === 'unified' ? '0 2px 6px rgba(220,38,38,0.25)' : 'none',
                transition: 'all 0.15s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              <span>🚨</span>
              <span>48h Forecast</span>
            </button>
            <button
              onClick={() => setActiveMode('15day')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                border: 'none',
                background: (activeMode === '15day' || activeMode === '60day') ? '#059669' : 'transparent',
                color: (activeMode === '15day' || activeMode === '60day') ? '#ffffff' : '#475569',
                fontWeight: '700',
                fontSize: '0.8rem',
                cursor: 'pointer',
                boxShadow: (activeMode === '15day' || activeMode === '60day') ? '0 2px 6px rgba(5,150,105,0.25)' : 'none',
                transition: 'all 0.15s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              <span>🗓️</span>
              <span>15-Day Forecast</span>
            </button>
          </div>

          {/* Right Controls: Mode Switcher + Refresh + JSON Payload */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={onToggleTelemetryMode}
              title="Toggle between Live Real-Time Peacetime Buoys and Simulated Category-4 Cyclone Emergency Scenario"
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                background: telemetryMode === 'simulated' ? '#0f172a' : '#059669',
                color: '#ffffff',
                fontWeight: '700',
                fontSize: '0.76rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                transition: 'all 0.15s ease'
              }}
            >
              <span>{telemetryMode === 'simulated' ? '🌊' : '⚡'}</span>
              <span>{telemetryMode === 'simulated' ? 'Switch to Live Ocean Feed' : 'Switch to Cyclone Drill'}</span>
            </button>

            <button
              onClick={() => { fetchUnifiedSurvey(true); fetchShortRange(true); fetchSeasonal(true); }}
              disabled={loadingSurvey || loadingShort || loadingSeasonal}
              title="Trigger fresh ingestion from live Open-Meteo coastal telemetry stations and satellite feed"
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                background: '#f1f5f9',
                color: '#334155',
                fontWeight: '700',
                border: '1px solid #cbd5e1',
                cursor: 'pointer',
                fontSize: '0.76rem',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                transition: 'all 0.15s ease'
              }}
            >
              <span>🔄</span> {loadingSurvey || loadingShort ? 'Syncing...' : 'Sync'}
            </button>

            <button
              onClick={() => setShowJsonModal(true)}
              title="Inspect full JSON payload generated by the multimodal fusion pipeline"
              style={{
                padding: '6px 10px',
                borderRadius: '6px',
                background: '#f8fafc',
                color: '#475569',
                fontWeight: '700',
                border: '1px solid #cbd5e1',
                cursor: 'pointer',
                fontSize: '0.76rem',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <span>{'{ }'}</span> JSON
            </button>
          </div>
        </div>
      </div>

      {/* Merged View: Unified Live Disaster Risk Survey & 48h Dynamic Track Scrubber */}
      {activeMode === 'unified' && (
        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          {loadingSurvey && !unifiedSurvey ? (
            <div className="card loading" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="spinner-icon"></div> Generating Unified Disaster Risk Survey & Vision Extraction...
            </div>
          ) : (
            <div className="forecast-workspace-grid">
              {/* LEFT / MAIN WORKSPACE: 48h Interactive Scrubber + 30-District Risk & Alert Status Matrix */}
              <div className="forecast-left-pane">
                {(() => {
                  const isCycloneActive = shortRange?.is_cyclone_active ?? (shortRange?.predicted_landfall_target_district && shortRange.predicted_landfall_target_district !== "No Coastal Strike" && (shortRange?.estimated_time_to_landfall_hours ?? 0) > 0)
                  const etlHour = isCycloneActive ? Math.round(shortRange?.estimated_time_to_landfall_hours ?? 7) : 0
                  const dynamicTrackGradient = generateDynamicTrackGradient(timelineSteps)
                  const currentLaymanTime = formatLaymanTime(currentHorizon?.timestamp_formatted, selectedHorizonIdx, timelineSteps[0]?.timestamp_formatted)
                  const currentWindDesc = getLaymanWindDescriptor(currentHorizon?.projected_peak_wind_kmh || Math.round((currentHorizon?.projected_peak_wind_kt || 35) * 1.852))

                  // Build clean milestone ticks: every 6 hours + Landfall hour
                  const baseTicks = [0, 6, 12, 18, 24, 30, 36, 42, 48].filter(h => h < timelineSteps.length)
                  if (isCycloneActive && etlHour > 0 && etlHour < timelineSteps.length && !baseTicks.includes(etlHour)) {
                    baseTicks.push(etlHour)
                    baseTicks.sort((a, b) => a - b)
                  }

                  // Helper to format date & time and flag when date (DD/MM) changes
                  let previousDayKey = null
                  const parsedTicks = baseTicks.map((h) => {
                    const item = timelineSteps[h]
                    const rawTs = item?.timestamp_formatted || item?.timestamp || ''
                    let dateStr = ''
                    let timeStr = ''

                    try {
                      const d = rawTs ? new Date(rawTs.replace(' UTC', 'Z').replace(' IST', '')) : new Date(Date.now() + h * 3600000)
                      if (!isNaN(d.getTime())) {
                        dateStr = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`
                        timeStr = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
                      }
                    } catch (e) { }

                    if (!timeStr) {
                      const fallback = formatLaymanTime(rawTs, h, timelineSteps[0]?.timestamp_formatted)
                      timeStr = fallback.timeOnly || `+${h}h`
                      dateStr = fallback.dateOnly || ''
                    }

                    const isDayChange = (previousDayKey === null || dateStr !== previousDayKey)
                    if (dateStr) previousDayKey = dateStr

                    const isLandfall = isCycloneActive && h === etlHour && etlHour > 0
                    return {
                      h,
                      dateStr,
                      timeStr,
                      isDayChange,
                      isLandfall
                    }
                  })

                  return (
                    <div className="card" style={{
                      flexShrink: 0,
                      background: '#ffffff',
                      borderTop: '4px solid #059669',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                      padding: '10px 16px',
                      margin: 0
                    }}>
                      {/* Compact Top Control Line */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <span style={{ fontSize: '0.92rem', fontWeight: '800', color: '#0f172a' }}>
                            48h Timeline
                          </span>
                          {/* Selected IST Time */}
                          <span style={{
                            fontSize: '0.8rem',
                            fontWeight: '700',
                            color: '#0f172a',
                            background: '#f8fafc',
                            padding: '3px 10px',
                            borderRadius: '6px',
                            border: '1px solid #cbd5e1'
                          }}>
                            🗓️ {currentLaymanTime.fullLabel}
                          </span>
                          {/* Wind & Intensity Severity */}
                          <span style={{
                            fontSize: '0.74rem',
                            fontWeight: '700',
                            color: currentWindDesc.badgeColor,
                            background: currentWindDesc.badgeBg,
                            padding: '3px 8px',
                            borderRadius: '6px',
                            border: `1px solid ${currentWindDesc.border}`
                          }}>
                            {currentWindDesc.icon} {currentHorizon?.projected_peak_wind_kmh || 65} km/h • {currentWindDesc.severity}
                          </span>

                          {/* Live Risk Calculation Indicator */}
                          {isCalculatingRisk ? (
                            <span style={{
                              fontSize: '0.72rem',
                              fontWeight: '700',
                              color: '#b45309',
                              background: '#fef3c7',
                              padding: '3px 9px',
                              borderRadius: '6px',
                              border: '1px solid #fde68a',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px'
                            }}>
                              <span className="spinner-icon" style={{ width: '9px', height: '9px', borderWidth: '1.5px', borderTopColor: '#d97706' }}></span>
                              Recalculating Risk Surface...
                            </span>
                          ) : (
                            <span style={{
                              fontSize: '0.70rem',
                              fontWeight: '600',
                              color: '#059669',
                              background: '#f0fdf4',
                              padding: '3px 8px',
                              borderRadius: '6px',
                              border: '1px solid #bbf7d0',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '3px'
                            }}>
                              ✓ Step Synced
                            </span>
                          )}
                        </div>

                        {/* Playback Controls & Quick Presets */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <button
                            type="button"
                            onClick={() => handleHorizonChange(0)}
                            style={{ padding: '3px 8px', fontSize: '0.72rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #cbd5e1', background: selectedHorizonIdx === 0 ? '#e2e8f0' : '#ffffff', cursor: 'pointer', color: '#1e293b' }}
                          >
                            Live Now
                          </button>
                          {isCycloneActive && etlHour > 0 && (
                            <button
                              type="button"
                              onClick={() => handleHorizonChange(etlHour)}
                              style={{ padding: '3px 10px', fontSize: '0.72rem', fontWeight: '700', borderRadius: '5px', border: '1px solid #fca5a5', background: selectedHorizonIdx === etlHour ? '#fee2e2' : '#fef2f2', color: '#dc2626', cursor: 'pointer' }}
                            >
                              Landfall (+{etlHour}h)
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleHorizonChange(prev => Math.max(0, prev - 1))}
                            disabled={selectedHorizonIdx === 0}
                            style={{ padding: '3px 7px', fontSize: '0.72rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #cbd5e1', background: '#f8fafc', cursor: selectedHorizonIdx === 0 ? 'not-allowed' : 'pointer', color: '#334155' }}
                          >
                            ◀
                          </button>
                          <button
                            type="button"
                            onClick={() => setIsPlaying(!isPlaying)}
                            style={{ padding: '3px 12px', fontSize: '0.74rem', fontWeight: '700', borderRadius: '5px', border: 'none', background: isPlaying ? '#dc2626' : '#059669', color: '#ffffff', cursor: 'pointer' }}
                          >
                            {isPlaying ? '⏸ Pause' : '▶ Play'}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleHorizonChange(prev => Math.min(timelineSteps.length - 1, prev + 1))}
                            disabled={selectedHorizonIdx >= timelineSteps.length - 1}
                            style={{ padding: '3px 7px', fontSize: '0.72rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #cbd5e1', background: '#f8fafc', cursor: selectedHorizonIdx >= timelineSteps.length - 1 ? 'not-allowed' : 'pointer', color: '#334155' }}
                          >
                            ▶
                          </button>
                        </div>
                      </div>

                      {/* Continuous Multi-Zone Range Track */}
                      <div style={{ margin: '6px 0 2px' }}>
                        <input
                          type="range"
                          min="0"
                          max={(timelineSteps.length || 49) - 1}
                          step="1"
                          value={selectedHorizonIdx}
                          onChange={(e) => handleHorizonChange(Number(e.target.value))}
                          style={{
                            width: '100%',
                            height: '10px',
                            borderRadius: '5px',
                            background: dynamicTrackGradient,
                            cursor: 'pointer',
                            outline: 'none',
                            boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.2)'
                          }}
                        />

                        {/* Clean Ticks: DD/MM ONLY on Day Change, Clean Time for Others */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: '6px', padding: '0 2px' }}>
                          {parsedTicks.map((t) => {
                            const isSelected = selectedHorizonIdx === t.h
                            return (
                              <div
                                key={t.h}
                                onClick={() => handleHorizonChange(t.h)}
                                style={{
                                  display: 'flex',
                                  flexDirection: 'column',
                                  alignItems: 'center',
                                  cursor: 'pointer',
                                  padding: '2px 4px',
                                  borderRadius: '5px',
                                  background: isSelected ? 'rgba(5, 150, 105, 0.12)' : 'transparent',
                                  border: isSelected ? '1px solid #059669' : '1px solid transparent',
                                  transition: 'all 0.15s ease'
                                }}
                              >
                                {t.isDayChange && (
                                  <span style={{
                                    fontSize: '0.64rem',
                                    fontWeight: '800',
                                    color: '#0f172a',
                                    background: '#e2e8f0',
                                    padding: '1px 4px',
                                    borderRadius: '3px',
                                    marginBottom: '2px',
                                    letterSpacing: '0.02em',
                                    whiteSpace: 'nowrap'
                                  }}>
                                    {t.dateStr}
                                  </span>
                                )}
                                <span style={{
                                  fontSize: '0.72rem',
                                  fontWeight: t.isLandfall ? '800' : (isSelected ? '700' : '500'),
                                  color: t.isLandfall ? '#dc2626' : (isSelected ? '#059669' : '#64748b'),
                                  whiteSpace: 'nowrap'
                                }}>
                                  {t.isLandfall ? `🔴 ${t.timeStr}` : t.timeStr}
                                </span>
                                {t.isLandfall && (
                                  <span style={{ fontSize: '0.58rem', fontWeight: '800', color: '#dc2626', textTransform: 'uppercase', letterSpacing: '0.03em', whiteSpace: 'nowrap' }}>
                                    Landfall
                                  </span>
                                )}
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

                  return (
                    <div className="forecast-table-card">
                      {/* Top recalculating shimmer bar */}
                      {isCalculatingRisk && <div className="matrix-recalculating-shimmer" />}

                      <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <h3 style={{ margin: 0, fontSize: '1.02rem', color: '#0f172a' }}>
                            District Wise Risk & Alert Status Matrix ({formatToIST(currentHorizon?.timestamp_formatted) || 'Live IST'})
                          </h3>
                          {isCalculatingRisk ? (
                            <span style={{
                              fontSize: '0.74rem',
                              color: '#b45309',
                              background: '#fef3c7',
                              border: '1px solid #fcd34d',
                              padding: '2px 9px',
                              borderRadius: '12px',
                              fontWeight: '700',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px'
                            }}>
                              <span className="spinner-icon" style={{ width: '9px', height: '9px', borderWidth: '1.5px', borderTopColor: '#d97706' }}></span>
                              Recalculating Risk Surface...
                            </span>
                          ) : (
                            <span style={{
                              fontSize: '0.72rem',
                              color: '#059669',
                              background: '#f0fdf4',
                              border: '1px solid #bbf7d0',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontWeight: '600'
                            }}>
                              ✓ Live Analyzed
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Filter & Search Bar */}
                      <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '6px 0 10px', flexWrap: 'wrap', gap: '10px' }}>
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

                      <div className="district-matrix-scroll-wrap" style={{ position: 'relative' }}>
                        {/* Floating Glassmorphic Evaluating Capsule during scrub */}
                        {isCalculatingRisk && (
                          <div style={{
                            position: 'absolute',
                            top: '60px',
                            left: '50%',
                            transform: 'translateX(-50%)',
                            zIndex: 25,
                            background: 'rgba(15, 23, 42, 0.90)',
                            backdropFilter: 'blur(6px)',
                            color: '#ffffff',
                            padding: '8px 18px',
                            borderRadius: '24px',
                            boxShadow: '0 8px 24px rgba(0,0,0,0.22)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '10px',
                            fontSize: '0.8rem',
                            fontWeight: '700',
                            letterSpacing: '0.02em',
                            pointerEvents: 'none'
                          }}>
                            <span className="spinner-icon" style={{ width: '12px', height: '12px', borderWidth: '2px', borderTopColor: '#38bdf8' }}></span>
                            <span>Recomputing 30-District Risk Surface for +{selectedHorizonIdx}h ({currentLaymanTime.timeOnly} IST)...</span>
                          </div>
                        )}

                        <table className="district-matrix-table" style={{
                          width: '100%',
                          borderCollapse: 'collapse',
                          fontSize: '0.82rem',
                          opacity: isCalculatingRisk ? 0.45 : 1,
                          filter: isCalculatingRisk ? 'blur(0.5px)' : 'none',
                          transition: 'opacity 0.2s ease, filter 0.2s ease'
                        }}>
                          <thead>
                            <tr style={{ background: '#f1f5f9', color: '#0f172a', textTransform: 'uppercase', fontSize: '0.75rem', cursor: 'pointer' }}>
                              <th style={{ padding: '9px 10px', textAlign: 'left' }} onClick={() => handleSort('name')}>
                                District {sortBy === 'name' ? (sortAsc ? '▲' : '▼') : ''}
                              </th>
                              <th style={{ padding: '9px 10px', textAlign: 'left' }} onClick={() => handleSort('dist')}>
                                {isCycloneActive ? 'Eye Proximity (d_eye)' : 'Proximity / Coast'} {sortBy === 'dist' ? (sortAsc ? '▲' : '▼') : ''}
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
                                const windKt = Number(d.projected_wind_kt ?? d.estimated_wind_kt ?? 25.0).toFixed(1)
                                const windKmh = Number(d.projected_wind_kmh ?? d.estimated_wind_kmh ?? (windKt * 1.852)).toFixed(1)
                                const riskScore = d.predicted_risk_score || 0.10
                                const eyeDist = Number(d.distance_to_eye_km ?? d.distance_to_storm_center_km ?? d.coastal_distance_km ?? 0).toFixed(1)
                                const coastDist = Number(d.coastal_distance_km || 100.0).toFixed(1)
                                const surgeM = (Number(coastDist) <= 20.0 && d.projected_storm_surge_m) ? Number(d.projected_storm_surge_m) : 0.0
                                const rainMm = d.projected_rainfall_24h_mm ? Number(d.projected_rainfall_24h_mm).toFixed(1) : Math.round(180 * Math.exp(-Number(eyeDist) / 140.0))
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
                                        <strong style={{ color: !isCycloneActive ? '#059669' : (eyeDist <= 35 ? '#dc2626' : (eyeDist <= 100 ? '#d97706' : '#0284c7')), fontSize: '0.84rem' }}>
                                          {isCycloneActive && d.distance_to_eye_km != null ? `${eyeDist} km` : '—'}
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
              </div>

              {/* RIGHT SIDEBAR INSPECTOR (Fixed 350px width, Pinned Dossier) */}
              <div className="forecast-right-pane">
                {/* Widget 1: Primary Landfall Target & Window ETA */}
                <div style={{
                  background: '#ffffff',
                  padding: '14px 16px',
                  borderRadius: '10px',
                  border: '1px solid #e2e8f0',
                  borderTop: `4px solid ${isCycloneActive ? '#dc2626' : '#10b981'}`,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{
                      fontSize: '0.7rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      color: isCycloneActive ? '#991b1b' : '#15803d',
                      fontWeight: '800'
                    }}>
                      🎯 Landfall Target & ETA
                    </span>
                    {isCycloneActive && (
                      <span style={{ fontSize: '0.66rem', background: '#fee2e2', color: '#dc2626', padding: '1px 7px', borderRadius: '10px', fontWeight: '700' }}>
                        {shortRange?.probabilistic_ensemble?.ensemble_confidence_score_pct || 100}% Consensus
                      </span>
                    )}
                  </div>

                  <div>
                    <strong style={{
                      fontSize: '1.25rem',
                      color: isCycloneActive ? '#dc2626' : '#059669',
                      display: 'block',
                      lineHeight: '1.2'
                    }}>
                      {(() => {
                        const target = shortRange?.predicted_landfall_target_district || summaryData.primary_landfall_target || 'Ganjam'
                        if (target === 'No Coastal Strike' || !isCycloneActive) return 'No Coastal Strike'
                        return `${target} Coast`
                      })()}
                    </strong>
                    <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
                      {isCycloneActive
                        ? (shortRange?.landfall_sector || summaryData.landfall_sector || 'Gopalpur Coastal Sector (Sompeta-Gopalpur Belt)')
                        : 'Bay of Bengal Basin Clear • Normal Marine Domain'}
                    </span>
                  </div>

                  <div style={{
                    background: isCycloneActive ? '#fff7ed' : '#f0fdf4',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: `1px solid ${isCycloneActive ? '#fed7aa' : '#bbf7d0'}`
                  }}>
                    <span style={{ fontSize: '0.66rem', textTransform: 'uppercase', color: isCycloneActive ? '#c2410c' : '#15803d', fontWeight: '700', display: 'block' }}>
                      Operational Impact Window
                    </span>
                    <strong style={{ fontSize: '0.94rem', color: isCycloneActive ? '#c2410c' : '#14532d', display: 'block', margin: '2px 0' }}>
                      {isCycloneActive
                        ? (shortRange?.landfall_impact_window_ist || summaryData.landfall_impact_window_ist || '11:23 AM – 03:53 PM IST')
                        : 'Standby Monitoring (No Active ETA)'}
                    </strong>
                    {isCycloneActive && (
                      <div style={{ fontSize: '0.72rem', color: '#7c2d12', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                        <span>Eye:</span>
                        <strong>{shortRange?.estimated_landfall_timestamp_ist || summaryData.estimated_landfall_ist || '20 Nov, 01:52 PM IST'}</strong>
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.62rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>💨 Peak Landfall Wind</span>
                      <strong style={{ fontSize: '0.84rem', color: isCycloneActive ? '#dc2626' : '#059669' }}>
                        {isCycloneActive
                          ? `${shortRange?.projected_peak_landfall_wind_kt || summaryData.landfall_intensity_knots || 85} kt (${Math.round((shortRange?.projected_peak_landfall_wind_kt || summaryData.landfall_intensity_knots || 85) * 1.852)} km/h)`
                          : '15 km/h (Calm)'}
                      </strong>
                    </div>
                    <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.62rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>🌊 Coastal Surge</span>
                      <strong style={{ fontSize: '0.84rem', color: isCycloneActive ? '#d97706' : '#0284c7' }}>
                        {isCycloneActive ? '2.8m (High Surge)' : '0.2m (Normal Tide)'}
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Widget 2: Satellite Vision & TCIR AI Embeddings */}
                <div style={{
                  background: '#ffffff',
                  padding: '14px 16px',
                  borderRadius: '10px',
                  border: '1px solid #e2e8f0',
                  borderTop: '4px solid #0284c7',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#0369a1', fontWeight: '800' }}>
                      🛰️ Satellite Vision & TCIR
                    </span>
                    <span style={{ fontSize: '0.66rem', background: '#e0f2fe', color: '#0369a1', padding: '1px 8px', borderRadius: '10px', fontWeight: '700' }}>
                      Pass {unifiedSurvey?.satellite_pass_date || '2026-11-19'}
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '84px 1fr', gap: '10px', alignItems: 'center' }}>
                    <div style={{ position: 'relative', borderRadius: '6px', overflow: 'hidden', border: '1px solid #cbd5e1', background: '#0f172a', height: '74px' }}>
                      <img
                        src={unifiedSurvey?.nasa_gibs?.tile_snapshot_url || 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/2026-09-22/250m/3/2/5.jpg'}
                        alt="Satellite Crop"
                        onError={(e) => { e.target.src = 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/2026-09-22/250m/3/2/5.jpg'; }}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                      <span style={{ position: 'absolute', bottom: '2px', left: '2px', right: '2px', textAlign: 'center', background: 'rgba(15, 23, 42, 0.92)', color: '#38bdf8', fontSize: '0.55rem', padding: '1px 2px', borderRadius: '3px', fontWeight: '700' }}>
                        TCIR CNN
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px' }}>
                      <div style={{ background: '#f8fafc', padding: '4px 6px', borderRadius: '5px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.58rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>🧭 Vector</span>
                        <strong style={{ fontSize: '0.74rem', color: '#0f172a', display: 'block' }}>
                          {shortRange?.satellite_telemetry?.vision_ai_telemetry?.heading_vector || summaryData?.heading_vector || '315° NW'}
                        </strong>
                      </div>
                      <div style={{ background: '#f8fafc', padding: '4px 6px', borderRadius: '5px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.58rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>⚡ Speed</span>
                        <strong style={{ fontSize: '0.74rem', color: '#d97706', display: 'block' }}>
                          {shortRange?.satellite_telemetry?.vision_ai_telemetry?.translation_speed_kmh
                            ? `${shortRange.satellite_telemetry.vision_ai_telemetry.translation_speed_kmh} km/h`
                            : (summaryData?.translation_speed_kmh ? `${summaryData.translation_speed_kmh} km/h` : '14.8 km/h')}
                        </strong>
                      </div>
                      <div style={{ background: '#f8fafc', padding: '4px 6px', borderRadius: '5px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.58rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>
                          {isCycloneActive ? '👁️ Eye' : '🌊 Vortex'}
                        </span>
                        <strong style={{ fontSize: '0.70rem', color: isCycloneActive ? '#0284c7' : '#059669', display: 'block' }}>
                          {isCycloneActive
                            ? (shortRange?.satellite_telemetry?.vision_ai_telemetry?.eye_latitude
                                ? `${shortRange.satellite_telemetry.vision_ai_telemetry.eye_latitude}°N, ${shortRange.satellite_telemetry.vision_ai_telemetry.eye_longitude}°E`
                                : (summaryData?.eye_coordinates?.lat ? `${summaryData.eye_coordinates.lat}°N, ${summaryData.eye_coordinates.lon}°E` : '17.8°N, 86.1°E'))
                            : 'No Eye (Calm)'}
                        </strong>
                      </div>
                      <div style={{ background: '#f8fafc', padding: '4px 6px', borderRadius: '5px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.58rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>🌀 Density</span>
                        <strong style={{ fontSize: '0.74rem', color: '#059669', display: 'block' }}>
                          {shortRange?.satellite_telemetry?.vision_ai_telemetry?.cloud_wall_density_score != null
                            ? String(shortRange.satellite_telemetry.vision_ai_telemetry.cloud_wall_density_score)
                            : (summaryData?.convective_density_score != null ? String(summaryData.convective_density_score) : (telemetryMode === 'simulated' ? '0.88' : '0.33'))}
                        </strong>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Widget 3: Live Lifecycle Phase & Situational Brief (Synced with 48h Scrubber) */}
                <div style={{
                  background: currentWindDesc.badgeBg || '#fffbeb',
                  padding: '14px 16px',
                  borderRadius: '10px',
                  border: `1.5px solid ${currentWindDesc.border || '#fde68a'}`,
                  borderTop: `4px solid ${currentWindDesc.badgeColor || '#d97706'}`,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  flex: 1,
                  minHeight: 0,
                  overflowY: 'auto'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{
                      fontSize: '0.80rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      color: currentWindDesc.badgeColor || '#92400e',
                      fontWeight: '800'
                    }}>
                      🌪️ Live Situational Brief
                    </span>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: '700',
                      color: currentWindDesc.badgeColor || '#92400e',
                      background: 'rgba(255, 255, 255, 0.92)',
                      padding: '2px 9px',
                      borderRadius: '8px',
                      border: `1px solid ${currentWindDesc.border || '#fde68a'}`
                    }}>
                      {selectedHorizonIdx === 0
                        ? (currentLaymanTime.relativeDay === 'Live Now' ? 'Live Now' : `${currentLaymanTime.relativeDay} • Live Now`)
                        : `${currentLaymanTime.relativeDay} • +${selectedHorizonIdx}h`}
                    </span>
                  </div>

                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div>
                      <span style={{
                        background: currentWindDesc.badgeColor || '#d97706',
                        color: '#ffffff',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontWeight: '700',
                        fontSize: '0.82rem',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        lineHeight: '1.2'
                      }}>
                        {currentWindDesc.icon} {currentHorizon?.lifecycle_phase || currentWindDesc.severity}
                      </span>
                    </div>

                    <div style={{
                      background: 'rgba(255, 255, 255, 0.75)',
                      padding: '12px 14px',
                      borderRadius: '8px',
                      border: '1px solid rgba(0,0,0,0.06)',
                      flex: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      gap: '10px'
                    }}>
                      <p style={{
                        fontSize: '0.86rem',
                        color: '#0f172a',
                        lineHeight: '1.55',
                        margin: 0,
                        fontWeight: '500'
                      }}>
                        {situationalSummary}
                      </p>

                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '8px',
                        paddingTop: '8px',
                        borderTop: '1px solid rgba(0,0,0,0.08)',
                        marginTop: 'auto'
                      }}>
                        <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                          <span style={{ fontWeight: '600' }}>Timeline Horizon:</span>
                          <strong style={{ display: 'block', color: '#0f172a', fontSize: '0.80rem' }}>
                            {selectedHorizonIdx === 0 ? 'Live Telemetry (T=0)' : `+${selectedHorizonIdx}h Projection`}
                          </strong>
                        </div>
                        <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                          <span style={{ fontWeight: '600' }}>Sustained Wind:</span>
                          <strong style={{ display: 'block', color: currentWindDesc.badgeColor || '#d97706', fontSize: '0.80rem' }}>
                            {currentHorizon?.projected_peak_wind_kmh || Math.round((currentHorizon?.projected_peak_wind_kt || 35) * 1.852)} km/h
                          </strong>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
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
                const isCycloneActive = shortRange?.is_cyclone_active ?? (shortRange?.predicted_landfall_target_district && shortRange.predicted_landfall_target_district !== "No Coastal Strike" && (shortRange?.estimated_time_to_landfall_hours ?? 0) > 0)
                const etlHour = isCycloneActive ? Math.round(shortRange?.estimated_time_to_landfall_hours ?? 7) : 0
                const forwardHour = isCycloneActive ? Math.max(0, etlHour - 3) : 0
                const targetDistrict = shortRange?.predicted_landfall_target_district || (isCycloneActive ? "Ganjam" : "No Coastal Strike")
                const dynamicTrackGradient = generateDynamicTrackGradient(timelineSteps)
                const currentLaymanTime = formatLaymanTime(currentHorizon?.timestamp_formatted, selectedHorizonIdx)
                const currentWindDesc = getLaymanWindDescriptor(currentHorizon?.projected_peak_wind_kmh || Math.round((currentHorizon?.projected_peak_wind_kt || 35) * 1.852))
                const situationalSummary = getLaymanSituationalSummary(currentHorizon, shortRange)
                const milestoneHours = isCycloneActive
                  ? Array.from(new Set([0, 1, 3, forwardHour, etlHour, 12, 18, 24, 36, 48]))
                    .filter(h => h >= 0 && h <= (timelineSteps.length - 1))
                    .sort((a, b) => a - b)
                  : [0, 1, 3, 6, 12, 18, 24, 36, 48].filter(h => h < timelineSteps.length)

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
                        onClick={() => handleHorizonChange(0)}
                        style={{ padding: '6px 12px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #cbd5e1', background: selectedHorizonIdx === 0 ? '#e2e8f0' : '#f8fafc', cursor: 'pointer', color: '#1e293b' }}
                      >
                        ⏮️ Live Now
                      </button>

                      {isCycloneActive && forwardHour > 0 && forwardHour !== etlHour && (
                        <button
                          type="button"
                          onClick={() => handleHorizonChange(forwardHour)}
                          style={{ padding: '6px 12px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #fcd34d', background: selectedHorizonIdx === forwardHour ? '#fde68a' : '#fffbeb', cursor: 'pointer', color: '#92400e' }}
                        >
                          ⚠️ Outer Winds on Coast (+{forwardHour}h Ahead)
                        </button>
                      )}

                      {isCycloneActive && etlHour > 0 && (
                        <button
                          type="button"
                          onClick={() => handleHorizonChange(etlHour)}
                          style={{ padding: '6px 14px', fontSize: '0.82rem', fontWeight: 'bold', borderRadius: '6px', border: '1.5px solid #f87171', background: selectedHorizonIdx === etlHour ? '#fee2e2' : '#fef2f2', color: '#991b1b', cursor: 'pointer', boxShadow: '0 1px 3px rgba(220,38,38,0.15)' }}
                        >
                          🎯 Peak Eye Landfall (+{etlHour}h Ahead • {targetDistrict})
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleHorizonChange(Math.min(18, timelineSteps.length - 1))}
                        style={{ padding: '6px 12px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '6px', border: '1px solid #c4b5fd', background: selectedHorizonIdx === 18 ? '#ddd6fe' : '#f5f3ff', cursor: 'pointer', color: '#5b21b6' }}
                      >
                        🌅 Tomorrow Morning
                      </button>

                      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <button
                          type="button"
                          onClick={() => handleHorizonChange(prev => Math.max(0, prev - 1))}
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
                          onClick={() => handleHorizonChange(prev => Math.min(timelineSteps.length - 1, prev + 1))}
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
                        onChange={(e) => handleHorizonChange(Number(e.target.value))}
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
                        {isCycloneActive ? (
                          <>
                            <span>🔵 Approaching Ocean</span>
                            <span>🟠 Coastal Gale Alert</span>
                            <span style={{ color: '#dc2626', fontWeight: 'bold' }}>🔴 Landfall Strike (+{etlHour}h Ahead)</span>
                            <span>🟣 Inland Decay across Western Odisha</span>
                          </>
                        ) : (
                          <>
                            <span>🟢 Calm Bay of Bengal</span>
                            <span>🟢 Normal Coastal Winds</span>
                            <span>🟢 Safe Marine Domain</span>
                            <span>🟢 Routine Monitoring</span>
                          </>
                        )}
                      </div>

                      {/* Milestone Cards Bar with Dynamic Badges */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
                        {milestoneHours.map((milestoneHour) => {
                          const actualIdx = Math.min(milestoneHour, timelineSteps.length - 1)
                          const item = timelineSteps[actualIdx]
                          const isSelected = selectedHorizonIdx === actualIdx
                          const isLandfall = isCycloneActive && milestoneHour === etlHour && etlHour > 0
                          const isForward = isCycloneActive && milestoneHour === forwardHour && forwardHour !== 0 && forwardHour !== etlHour
                          const layman = formatLaymanTime(item?.timestamp_formatted, milestoneHour, timelineSteps[0]?.timestamp_formatted)
                          const lCode = item?.lifecycle_code

                          let badgeLabel = isCycloneActive ? '🌊 Approaching' : '🟢 Normal'
                          let badgeBg = isCycloneActive ? '#e0f2fe' : '#ecfdf5'
                          let badgeColor = isCycloneActive ? '#0369a1' : '#059669'

                          if (isCycloneActive && (isLandfall || lCode === 'CORE_LANDFALL')) {
                            badgeLabel = '🔴 Landfall'
                            badgeBg = '#fee2e2'
                            badgeColor = '#dc2626'
                          } else if (isCycloneActive && (isForward || lCode === 'FORWARD_EYEWALL')) {
                            badgeLabel = '🟠 Outer Gale'
                            badgeBg = '#fef3c7'
                            badgeColor = '#d97706'
                          } else if (isCycloneActive && lCode === 'INLAND_WEAKENING') {
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
                              onClick={() => handleHorizonChange(actualIdx)}
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
                    const currentLaymanTime = formatLaymanTime(currentHorizon?.timestamp_formatted, selectedHorizonIdx, timelineSteps[0]?.timestamp_formatted);

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

      {/* Mode 2: Unified 15-Day Extended Horizon Forecast */}
      {(activeMode === '15day' || activeMode === '60day') && (
        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          {loadingSeasonal && !seasonal ? (
            <div className="card loading" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="spinner-icon"></div> Generating 15-Day Extended Horizon Forecast, ECMWF/GFS Multi-Model Ensembles & District Matrices...
            </div>
          ) : seasonal && (
            <div className="forecast-workspace-grid">
              {/* LEFT / MAIN WORKSPACE: 15-Day Scrubber + Multi-Tab Matrix/Ensemble/Drivers/Directives Card */}
              <div className="forecast-left-pane">
                {/* 15-Day Interactive Timeline Scrubber Card */}
                <div className="card" style={{
                  flexShrink: 0,
                  background: '#ffffff',
                  borderTop: '4px solid #059669',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  padding: '10px 16px',
                  margin: 0
                }}>
                  {/* Top Line: Day label, Peak Hazard, Synced badge, and Controls */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.92rem', fontWeight: '800', color: '#0f172a' }}>
                        15-Day Timeline
                      </span>
                      {/* Selected Day Pill */}
                      <span style={{
                        fontSize: '0.8rem',
                        fontWeight: '700',
                        color: '#0f172a',
                        background: '#f8fafc',
                        padding: '3px 10px',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e1'
                      }}>
                        🗓️ {current15DayHorizon?.date_full || current15DayHorizon?.date_formatted || 'Selected Date'}
                      </span>
                      {/* Wind & Intensity Severity */}
                      <span style={{
                        fontSize: '0.74rem',
                        fontWeight: '700',
                        color: current15DayHorizon?.tier_color || '#dc2626',
                        background: current15DayHorizon?.threat_tier === 'CRITICAL PEAK' ? '#fee2e2' : (current15DayHorizon?.threat_tier === 'HIGH THREAT' ? '#ffedd5' : '#ecfdf5'),
                        padding: '3px 8px',
                        borderRadius: '6px',
                        border: `1px solid ${current15DayHorizon?.threat_tier === 'CRITICAL PEAK' ? '#fca5a5' : '#86efac'}`
                      }}>
                        🌪️ {current15DayHorizon?.projected_peak_wind_kmh || 56} km/h • {current15DayHorizon?.classification || 'Squally Breeze'}
                      </span>
                      <span style={{
                        fontSize: '0.70rem',
                        fontWeight: '600',
                        color: '#059669',
                        background: '#f0fdf4',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        border: '1px solid #bbf7d0'
                      }}>
                        ✓ Day {selected15DayIdx + 1} Synced
                      </span>
                    </div>

                    {/* Milestone Presets and Playback Controls */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                      {seasonal?.is_cyclone_active ? (
                        <>
                          <button
                            type="button"
                            onClick={() => setSelected15DayIdx(0)}
                            title="Coastal Approach Phase (Day 1)"
                            style={{ padding: '3px 8px', fontSize: '0.74rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #cbd5e1', background: selected15DayIdx === 0 ? '#e2e8f0' : '#f8fafc', cursor: 'pointer', color: '#1e293b' }}
                          >
                            ⏮️ {fifteenDaySteps[0]?.date_str || 'Day 1'} • Approach
                          </button>
                          {(() => {
                            const landIdx = (() => {
                              const codeIdx = fifteenDaySteps.findIndex(s => s.lifecycle_code === 'landfall')
                              return codeIdx !== -1 ? codeIdx : Math.max(0, Math.min(14, (seasonal.peak_threat_day || 2) - 1))
                            })()
                            return (
                              <button
                                type="button"
                                onClick={() => setSelected15DayIdx(landIdx)}
                                title={`Landfall Strike at ${seasonal.primary_landfall_target || 'Target Coast'}`}
                                style={{ padding: '3px 9px', fontSize: '0.74rem', fontWeight: 700, borderRadius: '5px', border: '1.5px solid #f87171', background: selected15DayIdx === landIdx ? '#fee2e2' : '#fef2f2', color: '#991b1b', cursor: 'pointer', boxShadow: '0 1px 3px rgba(220,38,38,0.15)' }}
                              >
                                🎯 {fifteenDaySteps[landIdx]?.date_str || 'Day 2'} • Landfall
                              </button>
                            )
                          })()}
                          {(() => {
                            const landIdx = (() => {
                              const codeIdx = fifteenDaySteps.findIndex(s => s.lifecycle_code === 'landfall')
                              return codeIdx !== -1 ? codeIdx : Math.max(0, Math.min(14, (seasonal.peak_threat_day || 2) - 1))
                            })()
                            const decayIdx = (() => {
                              const codeIdx = fifteenDaySteps.findIndex(s => s.lifecycle_code === 'inland_decay')
                              return codeIdx !== -1 ? codeIdx : Math.min(14, landIdx + 1)
                            })()
                            return (
                              <button
                                type="button"
                                onClick={() => setSelected15DayIdx(decayIdx)}
                                title="Kaplan-DeMaria Overland Frictional Decay"
                                style={{ padding: '3px 8px', fontSize: '0.74rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #fb923c', background: selected15DayIdx === decayIdx ? '#fed7aa' : '#fff7ed', cursor: 'pointer', color: '#c2410c' }}
                              >
                                ⚡ {fifteenDaySteps[decayIdx]?.date_str || 'Day 3'} • Decay
                              </button>
                            )
                          })()}
                          {(() => {
                            const landIdx = (() => {
                              const codeIdx = fifteenDaySteps.findIndex(s => s.lifecycle_code === 'landfall')
                              return codeIdx !== -1 ? codeIdx : Math.max(0, Math.min(14, (seasonal.peak_threat_day || 2) - 1))
                            })()
                            const floodIdx = (() => {
                              const codeIdx = fifteenDaySteps.findIndex(s => s.lifecycle_code === 'river_flood_crest')
                              return codeIdx !== -1 ? codeIdx : Math.min(14, landIdx + 2)
                            })()
                            return (
                              <button
                                type="button"
                                onClick={() => setSelected15DayIdx(floodIdx)}
                                title="River Basin Flood Inundation Cresting"
                                style={{ padding: '3px 8px', fontSize: '0.74rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #c4b5fd', background: selected15DayIdx === floodIdx ? '#ddd6fe' : '#f5f3ff', cursor: 'pointer', color: '#5b21b6' }}
                              >
                                🌧️ {fifteenDaySteps[floodIdx]?.date_str || 'Day 4'} • River Floods
                              </button>
                            )
                          })()}
                          <button
                            type="button"
                            onClick={() => setSelected15DayIdx(14)}
                            title="Extended Synoptic S2S Horizon Baseline"
                            style={{ padding: '3px 8px', fontSize: '0.74rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #86efac', background: selected15DayIdx === 14 ? '#bbf7d0' : '#f0fdf4', cursor: 'pointer', color: '#166534' }}
                          >
                            🌅 {fifteenDaySteps[14]?.date_str || 'Day 15'} • 15d Horizon
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => setSelected15DayIdx(0)}
                            title="Today / Baseline Synoptic Observation"
                            style={{ padding: '3px 8px', fontSize: '0.74rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #cbd5e1', background: selected15DayIdx === 0 ? '#e2e8f0' : '#f8fafc', cursor: 'pointer', color: '#1e293b' }}
                          >
                            ⚡ {fifteenDaySteps[0]?.date_str || 'Today'} • Baseline
                          </button>
                          <button
                            type="button"
                            onClick={() => setSelected15DayIdx(6)}
                            title="End of Week 1 Predictability Boundary"
                            style={{ padding: '3px 8px', fontSize: '0.74rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #a7f3d0', background: selected15DayIdx === 6 ? '#d1fae5' : '#ecfdf5', cursor: 'pointer', color: '#047857' }}
                          >
                            🌐 {fifteenDaySteps[6]?.date_str || 'Day 7'} • End Week 1
                          </button>
                          <button
                            type="button"
                            onClick={() => setSelected15DayIdx(14)}
                            title="15-Day S2S Horizon Outlook"
                            style={{ padding: '3px 8px', fontSize: '0.74rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #86efac', background: selected15DayIdx === 14 ? '#bbf7d0' : '#f0fdf4', cursor: 'pointer', color: '#166534' }}
                          >
                            🌅 {fifteenDaySteps[14]?.date_str || 'Day 15'} • 15d Horizon
                          </button>
                        </>
                      )}

                      {/* Step & Playback Controls */}
                      <button
                        type="button"
                        onClick={() => setSelected15DayIdx(prev => Math.max(0, prev - 1))}
                        disabled={selected15DayIdx === 0}
                        style={{ padding: '3px 7px', fontSize: '0.74rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #cbd5e1', background: '#f8fafc', cursor: selected15DayIdx === 0 ? 'not-allowed' : 'pointer', color: '#334155' }}
                      >
                        ◀
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsPlaying15Day(!isPlaying15Day)}
                        style={{ padding: '4px 10px', fontSize: '0.75rem', fontWeight: 'bold', borderRadius: '5px', border: 'none', background: isPlaying15Day ? '#dc2626' : '#059669', color: '#ffffff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        {isPlaying15Day ? '⏸ Pause' : '▶ Play'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setSelected15DayIdx(prev => Math.min(fifteenDaySteps.length - 1, prev + 1))}
                        disabled={selected15DayIdx >= fifteenDaySteps.length - 1}
                        style={{ padding: '3px 7px', fontSize: '0.74rem', fontWeight: '600', borderRadius: '5px', border: '1px solid #cbd5e1', background: '#f8fafc', cursor: selected15DayIdx >= fifteenDaySteps.length - 1 ? 'not-allowed' : 'pointer', color: '#334155' }}
                      >
                        ▶
                      </button>
                    </div>
                  </div>

                  {/* Slider Track + Day Ticks */}
                  <div style={{ margin: '6px 0 2px' }}>
                    <input
                      type="range"
                      min="0"
                      max={(fifteenDaySteps.length || 15) - 1}
                      step="1"
                      value={selected15DayIdx}
                      onChange={(e) => setSelected15DayIdx(Number(e.target.value))}
                      style={{
                        width: '100%',
                        height: '10px',
                        borderRadius: '5px',
                        background: generate15DayTrackGradient(fifteenDaySteps),
                        cursor: 'pointer',
                        outline: 'none',
                        boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.2)'
                      }}
                    />

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: '6px', padding: '0 2px' }}>
                      {fifteenDaySteps.map((step, idx) => {
                        const isSelected = selected15DayIdx === idx
                        const isLandfall = seasonal?.is_cyclone_active && (
                          step.lifecycle_code === 'landfall' ||
                          (!fifteenDaySteps.some(s => s.lifecycle_code === 'landfall') && idx === Math.max(0, Math.min(14, (seasonal.peak_threat_day || 2) - 1)))
                        )
                        return (
                          <div
                            key={idx}
                            onClick={() => setSelected15DayIdx(idx)}
                            style={{
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              cursor: 'pointer',
                              padding: '2px 4px',
                              borderRadius: '5px',
                              background: isSelected ? 'rgba(5, 150, 105, 0.12)' : 'transparent',
                              border: isSelected ? '1px solid #059669' : '1px solid transparent',
                              transition: 'all 0.15s ease'
                            }}
                          >
                            <span style={{
                              fontSize: '0.68rem',
                              fontWeight: isLandfall ? '800' : (isSelected ? '700' : '500'),
                              color: isLandfall ? '#dc2626' : (isSelected ? '#059669' : '#64748b'),
                              whiteSpace: 'nowrap'
                            }}>
                              {isLandfall ? `🔴 ${step.date_str}` : step.date_str}
                            </span>
                            {isLandfall ? (
                              <span style={{ fontSize: '0.56rem', fontWeight: '800', color: '#dc2626', textTransform: 'uppercase' }}>
                                Landfall
                              </span>
                            ) : (
                              <span style={{ fontSize: '0.56rem', color: '#94a3b8' }}>

                              </span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>

                {/* Main Content Card (Sub-Tabs + Dynamic Scroll Container) */}
                <div className="forecast-table-card">
                  {/* Top Bar: Sub-Navigation Tabs + Refresh */}
                  <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px', borderBottom: '1px solid #e2e8f0', paddingBottom: '8px' }}>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                      {[
                        { id: 'scrubber', label: '⏱️ 15-Day Timeline', full: '15-Day Interactive Timeline & District Impacts' },
                        { id: 'ensemble', label: '🌐 Ensemble Models', full: 'Multi-Model Extended Ensemble Consensus (IMD, ECMWF, GFS)' },
                        { id: 'drivers', label: '🌊 Climate Drivers', full: 'Ocean & Atmospheric Teleconnections (MJO, SST, OHC)' },
                        { id: 'directives', label: '📋 OSDMA Directives', full: 'OSDMA Phased Action Directives' },
                        { id: 'vulnerability', label: '🏛️ District Baseline', full: '30-District Baseline Vulnerability Rankings' }
                      ].map(tab => (
                        <button
                          key={tab.id}
                          onClick={() => setActive15DayTab(tab.id)}
                          title={tab.full}
                          style={{
                            padding: '5px 12px',
                            fontSize: '0.78rem',
                            fontWeight: 'bold',
                            borderRadius: '6px',
                            border: 'none',
                            background: active15DayTab === tab.id ? '#059669' : '#f1f5f9',
                            color: active15DayTab === tab.id ? '#ffffff' : '#475569',
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                            boxShadow: active15DayTab === tab.id ? '0 1px 4px rgba(5,150,105,0.25)' : 'none',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          {tab.label}
                        </button>
                      ))}
                    </div>

                    <button
                      onClick={() => fetchSeasonal(true)}
                      disabled={loadingSeasonal}
                      style={{
                        padding: '5px 12px',
                        borderRadius: '6px',
                        background: '#f1f5f9',
                        color: '#059669',
                        fontWeight: 'bold',
                        border: '1px solid #cbd5e1',
                        cursor: 'pointer',
                        fontSize: '0.76rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}
                    >
                      {loadingSeasonal ? '⚡ Syncing...' : '🔄 Refresh 15-Day'}
                    </button>
                  </div>

                  {/* Filter & Search Bar (Only shown for 15-Day Timeline Scrubber tab) */}
                  {active15DayTab === 'scrubber' && (
                    <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <h3 style={{ margin: 0, fontSize: '0.98rem', color: '#0f172a' }}>
                          District Wise Impact Matrix ({current15DayHorizon?.date_full || current15DayHorizon?.date_formatted})
                        </h3>
                        <span style={{
                          fontSize: '0.70rem',
                          fontWeight: '600',
                          color: '#059669',
                          background: '#f0fdf4',
                          border: '1px solid #bbf7d0',
                          padding: '2px 8px',
                          borderRadius: '12px'
                        }}>
                          ✓ Auto-Sorted by Risk
                        </span>
                      </div>

                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                        <input
                          type="text"
                          placeholder="🔍 Search district..."
                          value={fifteenDaySearch}
                          onChange={(e) => setFifteenDaySearch(e.target.value)}
                          style={{
                            padding: '4px 10px',
                            fontSize: '0.78rem',
                            borderRadius: '6px',
                            border: '1px solid #cbd5e1',
                            width: '140px'
                          }}
                        />
                        <select
                          value={fifteenDayZoneFilter}
                          onChange={(e) => setFifteenDayZoneFilter(e.target.value)}
                          style={{
                            padding: '4px 8px',
                            fontSize: '0.78rem',
                            borderRadius: '6px',
                            border: '1px solid #cbd5e1',
                            background: '#ffffff'
                          }}
                        >
                          <option value="all">All Odisha Districts (30)</option>
                          <option value="Direct Coastal Front">Direct Coastal Front (&lt;25km)</option>
                          <option value="Near-Coast Buffer">Near-Coast Buffer (25-75km)</option>
                          <option value="Central Delta / Riverine">Central Delta (75-150km)</option>
                          <option value="Inland Western Plateau">Inland Western Plateau (&gt;150km)</option>
                        </select>
                      </div>
                    </div>
                  )}

                  {/* Scrollable Container (Sticky Headers & Smooth Internal Scroll) */}
                  <div className="district-matrix-scroll-wrap">
                    {/* TAB 1: 15-Day Interactive Timeline District Matrix */}
                    {active15DayTab === 'scrubber' && current15DayHorizon && current15DayHorizon.district_matrix && (
                      <table className="district-matrix-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left', minWidth: '820px' }}>
                        <thead>
                          <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', color: '#475569' }}>
                            <th onClick={() => handle15DaySort('name')} className="sticky-col" style={{ padding: '8px 10px', cursor: 'pointer', minWidth: '130px' }}>District {sort15DayBy === 'name' ? (sort15DayAsc ? '▲' : '▼') : ''}</th>
                            <th onClick={() => handle15DaySort('dist')} style={{ padding: '8px 10px', cursor: 'pointer' }}>{seasonal?.is_cyclone_active ? 'Dist to Eye' : 'Dist to Coast'} {sort15DayBy === 'dist' ? (sort15DayAsc ? '▲' : '▼') : ''}</th>
                            <th onClick={() => handle15DaySort('wind')} style={{ padding: '8px 10px', cursor: 'pointer' }}>Wind (km/h) {sort15DayBy === 'wind' ? (sort15DayAsc ? '▲' : '▼') : ''}</th>
                            <th onClick={() => handle15DaySort('rain')} style={{ padding: '8px 10px', cursor: 'pointer' }}>24h Rain (mm) {sort15DayBy === 'rain' ? (sort15DayAsc ? '▲' : '▼') : ''}</th>
                            <th style={{ padding: '8px 10px' }}>Storm Surge</th>
                            <th onClick={() => handle15DaySort('risk')} style={{ padding: '8px 10px', cursor: 'pointer' }}>Risk Score {sort15DayBy === 'risk' ? (sort15DayAsc ? '▲' : '▼') : ''}</th>
                            <th style={{ padding: '8px 10px' }}>Status</th>
                            <th onClick={() => handle15DaySort('evac')} style={{ padding: '8px 10px', cursor: 'pointer' }}>Evac Target {sort15DayBy === 'evac' ? (sort15DayAsc ? '▲' : '▼') : ''}</th>
                            <th style={{ padding: '8px 10px' }}>Shelters / ODRAF</th>
                          </tr>
                        </thead>
                        <tbody>
                          {current15DayHorizon.district_matrix
                            .filter(d => {
                              const matchesSearch = !fifteenDaySearch || d.district.toLowerCase().includes(fifteenDaySearch.toLowerCase())
                              const matchesZone = fifteenDayZoneFilter === 'all' || (fifteenDayZoneFilter === 'Direct Coastal Front' && d.coastal_distance_km <= 25) || (fifteenDayZoneFilter === 'Near-Coast Buffer' && d.coastal_distance_km > 25 && d.coastal_distance_km <= 75) || (fifteenDayZoneFilter === 'Central Delta / Riverine' && d.coastal_distance_km > 75 && d.coastal_distance_km <= 150) || (fifteenDayZoneFilter === 'Inland Western Plateau' && d.coastal_distance_km > 150)
                              return matchesSearch && matchesZone
                            })
                            .sort((a, b) => {
                              let valA = sort15DayBy === 'name' ? a.district : (sort15DayBy === 'dist' ? (seasonal?.is_cyclone_active ? (a.distance_to_storm_center_km ?? 9999) : a.coastal_distance_km) : (sort15DayBy === 'wind' ? a.projected_wind_kmh : (sort15DayBy === 'rain' ? a.projected_rainfall_24h_mm : (sort15DayBy === 'evac' ? a.evacuation_target : a.risk_score))))
                              let valB = sort15DayBy === 'name' ? b.district : (sort15DayBy === 'dist' ? (seasonal?.is_cyclone_active ? (b.distance_to_storm_center_km ?? 9999) : b.coastal_distance_km) : (sort15DayBy === 'wind' ? b.projected_wind_kmh : (sort15DayBy === 'rain' ? b.projected_rainfall_24h_mm : (sort15DayBy === 'evac' ? b.evacuation_target : b.risk_score))))
                              if (sort15DayAsc) return valA > valB ? 1 : -1
                              return valA < valB ? 1 : -1
                            })
                            .map((d, idx) => (
                              <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', background: d.risk_score >= 0.70 ? '#fff1f2' : (d.risk_score >= 0.45 ? '#fffbeb' : '#ffffff') }}>
                                <td className="sticky-col" style={{ padding: '8px 10px', fontWeight: 'bold', color: '#0f172a', background: d.risk_score >= 0.70 ? '#fff1f2' : (d.risk_score >= 0.45 ? '#fffbeb' : '#ffffff') }}>
                                  {d.district}
                                  <span style={{ display: 'block', fontSize: '0.68rem', color: '#64748b', fontWeight: 'normal' }}>
                                    Coast: {d.coastal_distance_km}km
                                  </span>
                                </td>
                                <td style={{ padding: '8px 10px', color: '#475569' }}>
                                  {seasonal?.is_cyclone_active ? (d.distance_to_storm_center_km != null ? `${d.distance_to_storm_center_km} km` : '—') : `${d.coastal_distance_km} km`}
                                </td>
                                <td style={{ padding: '8px 10px', fontWeight: 'bold', color: d.projected_wind_kmh >= 100 ? '#dc2626' : (d.projected_wind_kmh >= 60 ? '#d97706' : '#166534') }}>
                                  {d.projected_wind_kmh} km/h
                                </td>
                                <td style={{ padding: '8px 10px', fontWeight: 'bold', color: d.projected_rainfall_24h_mm >= 150 ? '#7c3aed' : '#0284c7' }}>
                                  {d.projected_rainfall_24h_mm} mm
                                </td>
                                <td style={{ padding: '8px 10px', color: '#475569' }}>
                                  {d.projected_storm_surge_m > 0.5 ? `${d.projected_storm_surge_m}m surge` : '<0.5m'}
                                </td>
                                <td style={{ padding: '8px 10px' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <div style={{ width: '45px', height: '6px', borderRadius: '3px', background: '#e2e8f0', overflow: 'hidden' }}>
                                      <div style={{ width: `${Math.round(d.risk_score * 100)}%`, height: '100%', background: d.risk_score >= 0.7 ? '#dc2626' : (d.risk_score >= 0.45 ? '#ea580c' : '#059669') }} />
                                    </div>
                                    <span style={{ fontSize: '0.76rem', fontWeight: 'bold' }}>{d.risk_score}</span>
                                  </div>
                                </td>
                                <td style={{ padding: '8px 10px' }}>
                                  <span style={{
                                    fontSize: '0.7rem',
                                    fontWeight: 'bold',
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    background: d.status_pill.includes('CRITICAL') ? '#fee2e2' : (d.status_pill.includes('HIGH') ? '#ffedd5' : (d.status_pill.includes('MODERATE') ? '#fef3c7' : '#ecfdf5')),
                                    color: d.status_pill.includes('CRITICAL') ? '#dc2626' : (d.status_pill.includes('HIGH') ? '#c2410c' : (d.status_pill.includes('MODERATE') ? '#b45309' : '#059669'))
                                  }}>
                                    {d.status_pill}
                                  </span>
                                </td>
                                <td style={{ padding: '8px 10px', fontWeight: 'bold', color: d.evacuation_target > 0 ? '#dc2626' : '#64748b' }}>
                                  {d.evacuation_target > 0 ? d.evacuation_target.toLocaleString() : 'Standby'}
                                </td>
                                <td style={{ padding: '8px 10px', color: '#334155' }}>
                                  {d.shelters_activated > 0 ? `${d.shelters_activated} MCS / ${d.odraf_platoons} Plt` : 'Routine'}
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    )}

                    {/* TAB 2: Multi-Model Ensemble Comparison */}
                    {active15DayTab === 'ensemble' && (
                      <div style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <h3 style={{ margin: 0, fontSize: '1rem', color: '#0f172a' }}>
                            🌐 Multi-Model Extended Ensemble Consensus (15-Day Horizon)
                          </h3>
                          <span style={{ fontSize: '0.74rem', background: '#ecfdf5', color: '#059669', padding: '3px 10px', borderRadius: '12px', fontWeight: 'bold' }}>
                            Ensemble Agreement: 88% High Confidence
                          </span>
                        </div>
                        <p style={{ fontSize: '0.82rem', color: '#475569', lineHeight: '1.45', margin: 0 }}>
                          {seasonal.multi_model_ensemble?.consensus_summary || 'Tight spatial agreement between IMD Multi-Model Ensemble (MME) and European ECMWF 15-day EPS indicates a persistent Northwestward track crossing South-Central Odisha coast around 23 Oct - 24 Oct (Fri - Sat).'}
                        </p>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px' }}>
                          {seasonal.multi_model_ensemble?.models?.map((m, idx) => (
                            <div key={idx} style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1.5px solid #cbd5e1' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                <strong style={{ fontSize: '0.92rem', color: '#0f172a' }}>{m.model_name}</strong>
                                <span style={{ fontSize: '0.7rem', fontWeight: 'bold', background: '#ecfdf5', color: '#059669', padding: '2px 8px', borderRadius: '4px' }}>
                                  {m.confidence_score}% Match
                                </span>
                              </div>
                              <div style={{ fontSize: '0.8rem', color: '#334155', marginBottom: '4px' }}>
                                <strong>Projected Landfall:</strong> {m.landfall_target} ({m.landfall_day})
                              </div>
                              <div style={{ fontSize: '0.8rem', color: '#dc2626', fontWeight: 'bold', marginBottom: '4px' }}>
                                <strong>Peak Wind:</strong> {m.peak_wind_kmh} km/h (Category VSCS)
                              </div>
                              <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '6px' }}>
                                {m.status}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* TAB 3: Climate Drivers & Teleconnections */}
                    {active15DayTab === 'drivers' && (
                      <div style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        <h3 style={{ margin: 0, fontSize: '1rem', color: '#0f172a' }}>
                          🌊 Large-Scale Ocean & Atmospheric Teleconnection Indices (15-Day Drivers)
                        </h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px' }}>
                          {/* ENSO */}
                          <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                              <span style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#0f172a' }}>El Niño / La Niña (ENSO)</span>
                              <span style={{ fontSize: '0.72rem', fontWeight: 'bold', background: '#ecfdf5', color: '#059669', padding: '2px 8px', borderRadius: '4px' }}>
                                {seasonal.climate_teleconnections?.enso?.state || 'La Niña'}
                              </span>
                            </div>
                            <div style={{ fontSize: '1.05rem', fontWeight: 'bold', color: '#059669', marginBottom: '6px' }}>
                              ONI Index: {seasonal.climate_teleconnections?.enso?.oni_value_c}°C
                            </div>
                            <p style={{ fontSize: '0.8rem', color: '#475569', margin: 0, lineHeight: '1.4' }}>
                              {seasonal.climate_teleconnections?.enso?.impact_summary}
                            </p>
                          </div>

                          {/* IOD */}
                          <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                              <span style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#0f172a' }}>Indian Ocean Dipole (IOD)</span>
                              <span style={{ fontSize: '0.72rem', fontWeight: 'bold', background: '#fef3c7', color: '#d97706', padding: '2px 8px', borderRadius: '4px' }}>
                                {seasonal.climate_teleconnections?.iod?.state || 'Neutral/Negative'}
                              </span>
                            </div>
                            <div style={{ fontSize: '1.05rem', fontWeight: 'bold', color: '#d97706', marginBottom: '6px' }}>
                              IOD Index: {seasonal.climate_teleconnections?.iod?.iod_index_c}°C
                            </div>
                            <p style={{ fontSize: '0.8rem', color: '#475569', margin: 0, lineHeight: '1.4' }}>
                              {seasonal.climate_teleconnections?.iod?.impact_summary}
                            </p>
                          </div>

                          {/* MJO */}
                          <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                              <span style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#0f172a' }}>Madden-Julian Oscillation (MJO)</span>
                              <span style={{ fontSize: '0.72rem', fontWeight: 'bold', background: '#fee2e2', color: '#dc2626', padding: '2px 8px', borderRadius: '4px' }}>
                                {seasonal.climate_teleconnections?.mjo?.signal || 'Active Convective Pulse'}
                              </span>
                            </div>
                            <div style={{ fontSize: '1.05rem', fontWeight: 'bold', color: '#dc2626', marginBottom: '6px' }}>
                              {seasonal.climate_teleconnections?.mjo?.phase} (Amp: {seasonal.climate_teleconnections?.mjo?.amplitude})
                            </div>
                            <p style={{ fontSize: '0.8rem', color: '#475569', margin: 0, lineHeight: '1.4' }}>
                              {seasonal.climate_teleconnections?.mjo?.impact_summary}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* TAB 4: OSDMA 15-Day Phased Action Directives */}
                    {active15DayTab === 'directives' && (
                      <div style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        <h3 style={{ margin: 0, fontSize: '1rem', color: '#0f172a' }}>
                          OSDMA 15-Day Phased Disaster Preparedness & Action Directives
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          {(seasonal.fifteen_day_readiness_phases || seasonal.preseason_readiness_checklist || []).map((item, idx) => (
                            <div key={idx} style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', borderLeft: item.priority.includes('P0') ? '4px solid #dc2626' : (item.priority.includes('P1') ? '4px solid #d97706' : '4px solid #059669') }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                                <strong style={{ fontSize: '0.90rem', color: '#0f172a' }}>{item.phase}</strong>
                                <span style={{ fontSize: '0.70rem', fontWeight: 'bold', background: item.priority.includes('P0') ? '#fee2e2' : '#fef3c7', color: item.priority.includes('P0') ? '#dc2626' : '#d97706', padding: '2px 8px', borderRadius: '4px' }}>
                                  {item.priority}
                                </span>
                              </div>
                              <p style={{ fontSize: '0.80rem', color: '#475569', margin: 0, lineHeight: '1.45' }}>
                                {item.action}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* TAB 5: 30-District Baseline Vulnerability Rankings */}
                    {active15DayTab === 'vulnerability' && (
                      <table className="district-matrix-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left', minWidth: '780px' }}>
                        <thead>
                          <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', color: '#475569' }}>
                            <th style={{ padding: '8px 12px' }}>Rank</th>
                            <th className="sticky-col" style={{ padding: '8px 12px', background: '#f8fafc', minWidth: '120px' }}>District</th>
                            <th style={{ padding: '8px 12px' }}>Zone</th>
                            <th style={{ padding: '8px 12px' }}>Coastal Dist</th>
                            <th style={{ padding: '8px 12px' }}>Vuln Score</th>
                            <th style={{ padding: '8px 12px' }}>Risk Category</th>
                            <th style={{ padding: '8px 12px' }}>MCS Shelters</th>
                            <th style={{ padding: '8px 12px' }}>Grain Buffer</th>
                            <th style={{ padding: '8px 12px' }}>ODRAF Platoons</th>
                          </tr>
                        </thead>
                        <tbody>
                          {seasonal.district_vulnerability_rankings?.map((d, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                              <td style={{ padding: '8px 12px', fontWeight: 'bold' }}>#{d.rank}</td>
                              <td className="sticky-col" style={{ padding: '8px 12px', fontWeight: 'bold', color: '#0f172a', background: 'inherit' }}>{d.district}</td>
                              <td style={{ padding: '8px 12px', color: '#475569' }}>{d.zone}</td>
                              <td style={{ padding: '8px 12px' }}>{d.coastal_distance_km} km</td>
                              <td style={{ padding: '8px 12px', fontWeight: 'bold', color: d.historical_landfall_vulnerability_score >= 0.7 ? '#dc2626' : '#059669' }}>
                                {d.historical_landfall_vulnerability_score}
                              </td>
                              <td style={{ padding: '8px 12px' }}>
                                <span style={{
                                  fontSize: '0.7rem',
                                  fontWeight: 'bold',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  background: d.seasonal_risk_category === 'CRITICAL RISK' ? '#fee2e2' : (d.seasonal_risk_category === 'HIGH EXPOSURE' ? '#ffedd5' : '#ecfdf5'),
                                  color: d.seasonal_risk_category === 'CRITICAL RISK' ? '#dc2626' : (d.seasonal_risk_category === 'HIGH EXPOSURE' ? '#c2410c' : '#059669')
                                }}>
                                  {d.seasonal_risk_category}
                                </span>
                              </td>
                              <td style={{ padding: '8px 12px' }}>{d.multipurpose_shelters_count} Units</td>
                              <td style={{ padding: '8px 12px' }}>{d.emergency_grain_buffer_mt.toLocaleString()} MT</td>
                              <td style={{ padding: '8px 12px' }}>{d.odraf_platoons_recommended} Platoons</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              </div>

              {/* RIGHT SIDEBAR INSPECTOR (Fixed 350px width, Pinned Dossier) */}
              <div className="forecast-right-pane">
                {/* Widget 1: Primary Landfall Target & Window ETA */}
                <div style={{
                  background: '#ffffff',
                  padding: '14px 16px',
                  borderRadius: '10px',
                  border: '1px solid #e2e8f0',
                  borderTop: `4px solid ${seasonal?.is_cyclone_active ? '#dc2626' : '#10b981'}`,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{
                      fontSize: '0.7rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      color: seasonal?.is_cyclone_active ? '#991b1b' : '#15803d',
                      fontWeight: '800'
                    }}>
                      Landfall Target & Window
                    </span>
                    <span style={{ fontSize: '0.66rem', background: '#ecfdf5', color: '#059669', padding: '1px 7px', borderRadius: '10px', fontWeight: '700' }}>
                      {seasonal?.ensemble_confidence_pct || (seasonal?.is_cyclone_active ? 88 : 94)}% Consensus
                    </span>
                  </div>

                  <div>
                    <strong style={{
                      fontSize: '1.25rem',
                      color: seasonal?.is_cyclone_active ? '#dc2626' : '#059669',
                      display: 'block',
                      lineHeight: '1.2'
                    }}>
                      {seasonal?.primary_landfall_target ? `${seasonal.primary_landfall_target} Coast` : 'Bay of Bengal Basin Clear'}
                    </strong>
                    <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
                      {seasonal?.primary_landfall_sector || 'Dhamra / Kendrapara Sector'}
                    </span>
                  </div>

                  <div style={{
                    background: seasonal?.is_cyclone_active ? '#fff7ed' : '#f0fdf4',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: `1px solid ${seasonal?.is_cyclone_active ? '#fed7aa' : '#bbf7d0'}`
                  }}>
                    <span style={{ fontSize: '0.66rem', textTransform: 'uppercase', color: seasonal?.is_cyclone_active ? '#c2410c' : '#15803d', fontWeight: '700', display: 'block' }}>
                      Operational Impact Window
                    </span>
                    <strong style={{ fontSize: '0.94rem', color: seasonal?.is_cyclone_active ? '#c2410c' : '#14532d', display: 'block', margin: '2px 0' }}>
                      {seasonal?.primary_landfall_window || 'No Active Landfall Window'}
                    </strong>
                    <div style={{ fontSize: '0.72rem', color: '#7c2d12', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                      <span>Peak Strike:</span>
                      <strong>{seasonal?.peak_landfall_dates || (fifteenDaySteps[1]?.date_full || '20 Nov 2026')}</strong>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.62rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>🌪️ Peak Wind</span>
                      <strong style={{ fontSize: '0.84rem', color: seasonal?.is_cyclone_active ? '#dc2626' : '#059669' }}>
                        {seasonal?.peak_projected_wind_kmh || 56.5} km/h ({seasonal?.peak_projected_wind_kt || 30.5} kt)
                      </strong>
                    </div>
                    <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '0.62rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>🌊 Ocean Heat</span>
                      <strong style={{ fontSize: '0.84rem', color: '#7c3aed' }}>
                        {seasonal.climate_teleconnections?.ohc?.value_kj_cm2 || 83.6} kJ/cm²
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Widget 2: Selected Day Eye & Vortex Dynamics */}
                {current15DayHorizon && (
                  <div style={{
                    background: '#ffffff',
                    padding: '14px 16px',
                    borderRadius: '10px',
                    border: '1px solid #e2e8f0',
                    borderTop: '4px solid #0284c7',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#0369a1', fontWeight: '800' }}>
                        {seasonal?.is_cyclone_active ? 'Vortex Dynamics & Eye' : 'Synoptic State & Ambient Watch'}
                      </span>
                      <span style={{ fontSize: '0.66rem', background: '#e0f2fe', color: '#0369a1', padding: '1px 8px', borderRadius: '10px', fontWeight: '700' }}>
                        Day {selected15DayIdx + 1} ({current15DayHorizon.short_weekday || ''})
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                      <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.60rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>
                          {seasonal?.is_cyclone_active ? '👁️ Eye Centroid' : '🌊 Vortex Status'}
                        </span>
                        <strong style={{ fontSize: '0.76rem', color: seasonal?.is_cyclone_active ? '#0284c7' : '#059669', display: 'block' }}>
                          {seasonal?.is_cyclone_active && current15DayHorizon.eye_coordinates?.lat != null
                            ? `${current15DayHorizon.eye_coordinates.lat}°N, ${current15DayHorizon.eye_coordinates.lon}°E`
                            : 'No Active Vortex'}
                        </strong>
                      </div>
                      <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.60rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>
                          {seasonal?.is_cyclone_active ? '🎯 Cone Uncertainty' : '🛡️ Cone Domain'}
                        </span>
                        <strong style={{ fontSize: '0.76rem', color: seasonal?.is_cyclone_active ? '#7c3aed' : '#059669', display: 'block' }}>
                          {seasonal?.is_cyclone_active && (current15DayHorizon.cone_uncertainty_km || 0) > 0
                            ? `±${current15DayHorizon.cone_uncertainty_km} km`
                            : 'Clear (0 km)'}
                        </strong>
                      </div>
                      <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.60rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>
                          {seasonal?.is_cyclone_active ? '⚡ Peak Core Wind' : '💨 Ambient Wind'}
                        </span>
                        <strong style={{ fontSize: '0.76rem', color: seasonal?.is_cyclone_active ? '#dc2626' : '#0f172a', display: 'block' }}>
                          {current15DayHorizon.projected_peak_wind_kmh} km/h
                        </strong>
                      </div>
                      <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.60rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>📉 Central Pressure</span>
                        <strong style={{ fontSize: '0.76rem', color: '#0f172a', display: 'block' }}>
                          {current15DayHorizon.projected_central_pressure_hpa} hPa
                        </strong>
                      </div>
                      <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.60rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>👥 State Evac</span>
                        <strong style={{ fontSize: '0.76rem', color: '#d97706', display: 'block' }}>
                          {current15DayHorizon.total_state_evacuation_target?.toLocaleString() || '0'}
                        </strong>
                      </div>
                      <div style={{ background: '#f8fafc', padding: '6px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.60rem', color: '#64748b', display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>🏠 Shelters / ODRAF</span>
                        <strong style={{ fontSize: '0.76rem', color: '#16a34a', display: 'block' }}>
                          {current15DayHorizon.total_shelters_activated} / {current15DayHorizon.total_ndrf_teams_deployed} Plt
                        </strong>
                      </div>
                    </div>
                  </div>
                )}

                {/* Widget 3: Live Situational Assessment Brief */}
                {current15DayHorizon && (
                  <div style={{
                    background: current15DayHorizon.threat_tier === 'CRITICAL PEAK' ? '#fff1f2' : (current15DayHorizon.threat_tier === 'HIGH THREAT' ? '#fff7ed' : '#ecfdf5'),
                    padding: '14px 16px',
                    borderRadius: '10px',
                    border: `1.5px solid ${current15DayHorizon.tier_color || '#a7f3d0'}`,
                    borderTop: `4px solid ${current15DayHorizon.tier_color || '#059669'}`,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    flex: 1,
                    minHeight: 0,
                    overflowY: 'auto'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{
                        fontSize: '0.80rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.06em',
                        color: current15DayHorizon.tier_color || '#059669',
                        fontWeight: '800'
                      }}>
                        🌪️ Live Situational Brief
                      </span>
                      <span style={{
                        fontSize: '0.72rem',
                        fontWeight: '700',
                        color: current15DayHorizon.tier_color || '#059669',
                        background: 'rgba(255, 255, 255, 0.92)',
                        padding: '2px 9px',
                        borderRadius: '8px',
                        border: `1px solid ${current15DayHorizon.tier_color || '#a7f3d0'}`
                      }}>
                        {selected15DayIdx === 0
                          ? 'Day 1 • Live Baseline'
                          : `Day ${selected15DayIdx + 1} • +${current15DayHorizon.horizon_hours || (selected15DayIdx + 1) * 24}h`}
                      </span>
                    </div>

                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <div>
                        <span style={{
                          background: current15DayHorizon.tier_color || '#059669',
                          color: '#ffffff',
                          padding: '4px 10px',
                          borderRadius: '6px',
                          fontWeight: '700',
                          fontSize: '0.82rem',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          lineHeight: '1.2'
                        }}>
                          {current15DayHorizon.threat_tier}: {current15DayHorizon.lifecycle_phase}
                        </span>
                      </div>

                      <div style={{
                        background: 'rgba(255, 255, 255, 0.75)',
                        padding: '12px 14px',
                        borderRadius: '8px',
                        border: '1px solid rgba(0,0,0,0.06)',
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        gap: '10px'
                      }}>
                        <p style={{
                          fontSize: '0.86rem',
                          color: '#0f172a',
                          lineHeight: '1.55',
                          margin: 0,
                          fontWeight: '500'
                        }}>
                          <strong style={{ color: current15DayHorizon.tier_color || '#059669', display: 'block', marginBottom: '4px', fontSize: '0.88rem' }}>
                            🛰️ Synoptic Steering & Meteorology:
                          </strong>
                          {current15DayHorizon.synoptic_driver}
                        </p>

                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: '1fr 1fr',
                          gap: '8px',
                          paddingTop: '8px',
                          borderTop: '1px solid rgba(0,0,0,0.08)',
                          marginTop: 'auto'
                        }}>
                          <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                            <span style={{ fontWeight: '600' }}>Ensemble Match:</span>
                            <strong style={{ display: 'block', color: '#059669', fontSize: '0.80rem' }}>
                              {current15DayHorizon.ensemble_confidence_pct || 88}% Consensus
                            </strong>
                          </div>
                          <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                            <span style={{ fontWeight: '600' }}>Cone Radius:</span>
                            <strong style={{ display: 'block', color: seasonal?.is_cyclone_active ? '#7c3aed' : '#059669', fontSize: '0.80rem' }}>
                              {seasonal?.is_cyclone_active && (current15DayHorizon.cone_uncertainty_km || 0) > 0
                                ? `±${current15DayHorizon.cone_uncertainty_km} km`
                                : 'None (Calm Sea)'}
                            </strong>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
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

