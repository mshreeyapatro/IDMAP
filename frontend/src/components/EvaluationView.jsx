import { useEffect, useState } from 'react'
import { api } from '../api'

function MetricCard({ label, value, hint }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  )
}

export default function EvaluationView() {
  const [evalData, setEvalData] = useState(null)

  useEffect(() => {
    api.evaluation().then(setEvalData).catch(() => setEvalData({}))
  }, [])

  if (!evalData) return <p className="loading">Loading evaluation data…</p>

  const { backbone, autoencoder, images } = evalData
  const hasCurves = images?.['tcir_backbone_training_curves.png']
  const hasEmbedding = images?.['embedding_space.png']

  return (
    <div>
      <div className="view-header">
        <h1>Model Evaluation</h1>
        <p className="view-subtitle">
          Phase 3 (CV backbone) and Phase 6 (anomaly detector) metrics, read live from the
          most recent training run's checkpoints -- not hardcoded.
        </p>
      </div>

      {!backbone && !autoencoder && (
        <p className="loading">No training run found yet -- run src/cv_models/pretrain_tcir_backbone.py first.</p>
      )}

      {backbone && (
        <>
          <h2 className="section-title">CV backbone (TCIR pretraining)</h2>
          <div className="stat-grid">
            <MetricCard label="Training images" value={backbone.n_train_images ?? '—'} />
            <MetricCard label="Embedding dims" value={backbone.embed_dim ?? '—'} />
            <MetricCard label="Val MAE" value={backbone.final_val_mae_kt != null ? `${backbone.final_val_mae_kt.toFixed(1)} kt` : '—'}
                        hint="unvalidated on insat3d -- TCIR-domain only" />
            <MetricCard label="Val R²" value={backbone.final_val_r2 != null ? backbone.final_val_r2.toFixed(3) : '—'} />
            <MetricCard label="Dead embedding dims" value={backbone.dead_dims ?? '—'}
                        hint="dying-ReLU check; 0 is ideal" />
          </div>
          {hasCurves && (
            <div className="report-image-card">
              <img src={api.imageUrl('/static/reports/tcir_backbone_training_curves.png')} alt="Training curves" />
            </div>
          )}
        </>
      )}

      {autoencoder && (
        <>
          <h2 className="section-title">Anomaly detector (Autoencoder)</h2>
          <div className="stat-grid">
            <MetricCard label="Active embedding dims used" value={autoencoder.active_embed_dims ?? '—'} />
            <MetricCard label="Anomaly threshold" value={autoencoder.anomaly_threshold != null ? autoencoder.anomaly_threshold.toFixed(3) : '—'}
                        hint={`${autoencoder.anomaly_percentile ?? 95}th percentile of train reconstruction error`} />
          </div>
          {hasEmbedding && (
            <div className="report-image-card">
              <img src={api.imageUrl('/static/reports/embedding_space.png')} alt="Embedding space" />
            </div>
          )}
        </>
      )}
    </div>
  )
}
