import { useEffect, useState } from 'react'
import { api } from '../api'

export default function AnomaliesView({ onSelectEvent }) {
  const [anomalies, setAnomalies] = useState(null)
  const [onlyFlagged, setOnlyFlagged] = useState(true)

  useEffect(() => {
    api.anomalies(20, onlyFlagged).then(setAnomalies).catch(() => setAnomalies([]))
  }, [onlyFlagged])

  const maxErr = anomalies?.length ? Math.max(...anomalies.map((a) => a.reconstruction_error)) : 1

  return (
    <div>
      <div className="view-header">
        <h1>Anomaly detection</h1>
        <p className="view-subtitle">
          Unsupervised autoencoder over CV feature embeddings. Cross-sectional (all 276 images
          compared against each other), not a temporal-evolution detector yet — no per-image
          timestamps exist to build a real sequence model. Threshold is the 95th percentile of
          training reconstruction error.
        </p>
      </div>

      <div className="filter-row">
        <button
          className={`chip ${onlyFlagged ? 'chip-active' : ''}`}
          onClick={() => setOnlyFlagged(true)}
        >
          flagged only
        </button>
        <button
          className={`chip ${!onlyFlagged ? 'chip-active' : ''}`}
          onClick={() => setOnlyFlagged(false)}
        >
          all (top 20)
        </button>
      </div>

      {!anomalies ? (
        <p className="loading">Loading anomalies…</p>
      ) : anomalies.length === 0 ? (
        <p className="loading">No images currently flagged as anomalous.</p>
      ) : (
        <div className="anomaly-list">
          {anomalies.map((a) => (
            <div
              key={`${a.base_id}-${a.modality}-${a.filename}`}
              className="anomaly-row clickable"
              onClick={() => onSelectEvent(a.base_id)}
            >
              <img src={api.imageUrl(a.url)} alt="" className="anomaly-thumb" />
              <div className="anomaly-info">
                <div className="anomaly-title">
                  Event {a.base_id} <span className={`split-tag split-${a.split}`}>{a.split}</span>
                </div>
                <div className="anomaly-meta">{a.modality} / {a.filename}</div>
                <div className="error-track">
                  <div
                    className="error-fill"
                    style={{ width: `${(a.reconstruction_error / maxErr) * 100}%` }}
                  />
                </div>
              </div>
              <div className="anomaly-score">{a.reconstruction_error.toFixed(2)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
