export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`${path} -> ${res.status}`)
  return res.json()
}

export const api = {
  status: () => getJSON('/api/status'),
  events: (split) => getJSON(`/api/events${split ? `?split=${split}` : ''}`),
  event: (baseId) => getJSON(`/api/events/${baseId}`),
  anomalies: (topN = 10, onlyFlagged = true) =>
    getJSON(`/api/anomalies?top_n=${topN}&only_flagged=${onlyFlagged}`),
  ask: async (question, history = []) => {
    const res = await fetch(`${API_BASE}/api/agent/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history }),
    })
    return res.json()
  },
  evaluation: () => getJSON('/api/evaluation'),
  districtGraph: (district) =>
    getJSON(`/api/district-graph${district ? `?district=${encodeURIComponent(district)}` : ''}`),
  predict: async (baseId) => {
    const res = await fetch(`${API_BASE}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ base_id: baseId }),
    })
    return res.json()
  },
  forecast: async (baseId) => {
    const res = await fetch(`${API_BASE}/api/forecast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ base_id: baseId }),
    })
    return res.json()
  },
  retrieve: async (query, topK = 4) => {
    const res = await fetch(`${API_BASE}/api/retrieve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK }),
    })
    return res.json()
  },
  advisory: async (baseId, task = 'advisory') => {
    const res = await fetch(`${API_BASE}/api/advisory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ base_id: baseId, task }),
    })
    return res.json()
  },
  explain: (baseId) => getJSON(`/api/explain/${baseId}`),
  explainLive: async (params = {}) => {
    const res = await fetch(`${API_BASE}/api/explain/live`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        wind_speed_kt: params.wind_speed_kt ?? 65.0,
        coastal_distance_km: params.coastal_distance_km ?? 85.0,
        district_population: params.district_population ?? 1250000.0,
        pressure_hpa: params.pressure_hpa ?? 998.0,
        anomaly_error: params.anomaly_error ?? 0.08
      }),
    })
    return res.json()
  },
  whatif: async (baseId, deltaWindSpeedKt = 0, newCoastalDistanceKm = null) => {
    const res = await fetch(`${API_BASE}/api/whatif`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        base_id: baseId,
        delta_wind_speed_kt: deltaWindSpeedKt,
        new_coastal_distance_km: newCoastalDistanceKm,
      }),
    })
    return res.json()
  },
  resources: (district, severity = 'High') =>
    getJSON(`/api/resources?severity=${severity}${district ? `&district=${encodeURIComponent(district)}` : ''}`),
  analyzeImage: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API_BASE}/api/analyze-image`, {
      method: 'POST',
      body: formData,
    })
    return res.json()
  },
  analyzeLiveSatellite: async () => {
    const res = await fetch(`${API_BASE}/api/analyze-live-satellite`, { method: 'POST' })
    return res.json()
  },
  liveWeather: (refresh = false) => getJSON(`/api/live/weather?refresh=${typeof refresh === 'boolean' ? refresh : false}`),
  liveSatellite: () => getJSON('/api/live/satellite'),
  liveAdvisory: async () => {
    const res = await fetch(`${API_BASE}/api/live/advisory`, { method: 'POST' })
    return res.json()
  },
  unifiedLiveSurvey: async (refresh = false) => {
    const isRefresh = typeof refresh === 'boolean' ? refresh : false
    const res = await fetch(`${API_BASE}/api/unified-live-survey?refresh=${isRefresh}`, { method: 'POST' })
    return res.json()
  },
  shortRangeForecast: async (refresh = false) => {
    const isRefresh = typeof refresh === 'boolean' ? refresh : false
    const res = await fetch(`${API_BASE}/api/forecast/short-range?refresh=${isRefresh}`, { method: 'POST' })
    return res.json()
  },
  seasonalOutlook: (refresh = false) => getJSON(`/api/forecast/seasonal-60day?refresh=${typeof refresh === 'boolean' ? refresh : false}`),
  submitFeedback: async (feedbackData) => {
    const res = await fetch(`${API_BASE}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedbackData),
    })
    return res.json()
  },
  advisoryHistory: (limit = 20) => getJSON(`/api/history/advisories?limit=${limit}`),
  triggerRetraining: async () => {
    const res = await fetch(`${API_BASE}/api/retrain/run`, { method: 'POST' })
    return res.json()
  },
  imageUrl: (relativeUrl) => `${API_BASE}${relativeUrl}`,
}
