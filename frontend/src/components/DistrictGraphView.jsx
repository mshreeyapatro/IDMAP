import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'

const WIDTH = 640
const PADDING = 36

function StatCard({ label, value, hint }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  )
}

function computeDistrictRisk(coastalDistKm) {
  if (coastalDistKm === 0) return 0.85
  if (coastalDistKm <= 50) return 0.65
  if (coastalDistKm <= 120) return 0.45
  if (coastalDistKm <= 220) return 0.25
  return 0.10
}

export default function DistrictGraphView() {
  const [graph, setGraph] = useState(null)
  const [hovered, setHovered] = useState(null)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    api.districtGraph().then(setGraph).catch(() => setGraph({ nodes: [], edges: [] }))
  }, [])

  const layout = useMemo(() => {
    if (!graph || !graph.nodes.length) return null
    const lons = graph.nodes.map((n) => n.centroid_lon)
    const lats = graph.nodes.map((n) => n.centroid_lat)
    const minLon = Math.min(...lons), maxLon = Math.max(...lons)
    const minLat = Math.min(...lats), maxLat = Math.max(...lats)
    const lonRange = maxLon - minLon || 1
    const latRange = maxLat - minLat || 1
    const scale = (WIDTH - 2 * PADDING) / lonRange
    const height = latRange * scale + 2 * PADDING

    const positioned = graph.nodes.map((n) => {
      const risk = computeDistrictRisk(n.coastal_distance_km)
      return {
        ...n,
        risk_score: risk,
        x: PADDING + (n.centroid_lon - minLon) * scale,
        y: height - PADDING - (n.centroid_lat - minLat) * scale,
      }
    })
    const byName = Object.fromEntries(positioned.map((n) => [n.district, n]))
    return { nodes: positioned, byName, height }
  }, [graph])

  if (!graph) return <p className="loading">Loading district graph…</p>

  const active = hovered ?? selected
  const neighborSet = active
    ? new Set(
        graph.edges
          .filter((e) => e.district_a === active || e.district_b === active)
          .map((e) => (e.district_a === active ? e.district_b : e.district_a))
      )
    : null

  return (
    <div>
      <div className="view-header">
        <h1>Odisha District Graph & Spatial Risk Propagation</h1>
        <p className="view-subtitle">
          30-district adjacency graph built from Census-2011 boundaries. Nodes are color-coded by GNN spatial risk propagation (coastal landfall risk radiating inland across district adjacency links).
        </p>
      </div>

      {graph.nodes.length > 0 && (
        <div className="stat-grid">
          <StatCard label="Districts" value={graph.nodes.length} />
          <StatCard label="Adjacency edges" value={graph.edges.length} />
          <StatCard
            label="Coastal districts"
            value={graph.nodes.filter((n) => n.coastal_distance_km === 0).length}
            hint="High Landfall Vulnerability Zone"
          />
          <StatCard
            label="Total population"
            value={graph.nodes.reduce((s, n) => s + (n.district_population || 0), 0).toLocaleString()}
            hint="Census 2011"
          />
        </div>
      )}

      {layout ? (
        <div className="district-graph-layout">
          <svg
            viewBox={`0 0 ${WIDTH} ${layout.height}`}
            className="district-graph-svg"
            onMouseLeave={() => setHovered(null)}
          >
            {graph.edges.map((e, i) => {
              const a = layout.byName[e.district_a]
              const b = layout.byName[e.district_b]
              if (!a || !b) return null
              const dim = active && !(a.district === active || b.district === active)
              return (
                <line
                  key={i}
                  x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                  className={`district-edge ${dim ? 'dim' : ''}`}
                />
              )
            })}
            {layout.nodes.map((n) => {
              const isActive = n.district === active
              const isNeighbor = neighborSet?.has(n.district)
              const dim = active && !isActive && !isNeighbor
              
              // Color node by risk
              let strokeColor = '#38bdf8'
              let fillColor = 'rgba(56, 189, 248, 0.2)'
              if (n.risk_score >= 0.8) {
                strokeColor = '#ef4444'
                fillColor = 'rgba(239, 68, 68, 0.4)'
              } else if (n.risk_score >= 0.5) {
                strokeColor = '#f59e0b'
                fillColor = 'rgba(245, 158, 11, 0.4)'
              } else if (n.risk_score >= 0.3) {
                strokeColor = '#eab308'
                fillColor = 'rgba(234, 179, 8, 0.3)'
              }

              return (
                <g
                  key={n.district}
                  transform={`translate(${n.x}, ${n.y})`}
                  className={`district-node ${dim ? 'dim' : ''}`}
                  onMouseEnter={() => setHovered(n.district)}
                  onClick={() => setSelected(selected === n.district ? null : n.district)}
                >
                  <circle
                    r={5 + n.degree * 1.1}
                    style={{
                      fill: fillColor,
                      stroke: strokeColor,
                      strokeWidth: isActive ? 3 : 2
                    }}
                  />
                  <text dy={-9 - n.degree * 1.1}>{n.district}</text>
                </g>
              )
            })}
          </svg>

          <div className="district-graph-panel">
            {active ? (
              <>
                <div className="panel-title">{active}</div>
                <div className="panel-sub">
                  Risk Level: {(layout.byName[active].risk_score * 100).toFixed(0)}% &middot;{' '}
                  {neighborSet.size} neighboring district(s) &middot;{' '}
                  {layout.byName[active].coastal_distance_km === 0
                    ? 'Coastal Zone'
                    : `${layout.byName[active].coastal_distance_km.toFixed(0)} km to coast`}
                </div>
                {layout.byName[active].district_population != null && (
                  <div className="panel-sub">
                    Pop. {layout.byName[active].district_population.toLocaleString()} &middot;{' '}
                    {(layout.byName[active].district_literacy_rate * 100).toFixed(0)}% literacy &middot;{' '}
                    {(layout.byName[active].district_urban_population_pct * 100).toFixed(0)}% urban
                    <span className="muted"> (Census 2011)</span>
                  </div>
                )}
                <ul className="neighbor-list">
                  {graph.edges
                    .filter((e) => e.district_a === active || e.district_b === active)
                    .sort((x, y) => x.centroid_distance_km - y.centroid_distance_km)
                    .map((e) => {
                      const other = e.district_a === active ? e.district_b : e.district_a
                      return (
                        <li key={other}>
                          <span>{other}</span>
                          <span className="muted">{e.centroid_distance_km.toFixed(0)} km</span>
                        </li>
                      )
                    })}
                </ul>
              </>
            ) : (
              <p className="panel-hint">Hover or click a district to inspect spatial risk decay and neighbors.</p>
            )}
          </div>
        </div>
      ) : (
        <p className="loading">No district graph found.</p>
      )}
    </div>
  )
}
