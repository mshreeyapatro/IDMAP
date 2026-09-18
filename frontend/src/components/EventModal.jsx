import { useEffect, useState } from 'react'
import { api } from '../api'

export default function EventModal({ baseId, onClose }) {
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    if (baseId == null) return
    setDetail(null)
    api.event(baseId).then(setDetail).catch(() => setDetail({ error: 'failed to load' }))
  }, [baseId])

  if (baseId == null) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>×</button>
        {!detail ? (
          <p className="loading">Loading…</p>
        ) : detail.error ? (
          <p>{detail.error}</p>
        ) : (
          <>
            <h2>
              {detail.matched_storm_name ? `Cyclone ${detail.matched_storm_name}` : `Event ${detail.base_id}`}
              {detail.is_odisha_relevant && <span className="odisha-badge" title="Storm track came within 150km of Odisha">Odisha</span>}
            </h2>
            <span className={`split-tag split-${detail.split}`}>{detail.split}</span>

            {detail.matched_storm_name && (
              <dl className="modal-facts">
                <dt>Storm ID / basin</dt>
                <dd>{detail.matched_storm_id} ({detail.matched_basin === 'ARB' ? 'Arabian Sea' : 'Bay of Bengal'})</dd>
                <dt>Date</dt>
                <dd>{detail.timestamp}</dd>
                {detail.wind_speed_kt != null && (
                  <>
                    <dt>Wind / pressure</dt>
                    <dd>{detail.wind_speed_kt.toFixed(0)} kt / {detail.pressure_hpa?.toFixed(0)} hPa</dd>
                  </>
                )}
                {detail.coastal_distance_km != null && (
                  <>
                    <dt>Distance to Odisha coast</dt>
                    <dd>{detail.coastal_distance_km.toFixed(0)} km</dd>
                  </>
                )}
                {detail.hours_before_landfall != null && (
                  <>
                    <dt>Before Odisha closest approach</dt>
                    <dd>{detail.hours_before_landfall.toFixed(0)} hours</dd>
                  </>
                )}
                {detail.nearest_odisha_district && (
                  <>
                    <dt>Nearest Odisha district</dt>
                    <dd>
                      {detail.nearest_odisha_district}
                      {detail.district_population != null && (
                        <span className="muted"> — pop. {detail.district_population.toLocaleString()} (Census 2011)</span>
                      )}
                    </dd>
                  </>
                )}
                <dt>Identity match confidence</dt>
                <dd className="muted">
                  {detail.identity_match_time_diff_hours != null ? `±${detail.identity_match_time_diff_hours}h, ` : ''}
                  {detail.identity_match_dist_km}km from OCR + IMD best-track matching
                </dd>
              </dl>
            )}

            <div className="modal-images">
              {detail.images?.map((im) => (
                <figure key={`${im.modality}-${im.filename}`} className="modal-image-fig">
                  <img src={api.imageUrl(im.url)} alt={`${im.modality} ${im.filename}`} />
                  <figcaption>{im.modality} / {im.filename}</figcaption>
                </figure>
              ))}
            </div>

            <dl className="modal-facts">
              <dt>Raw images</dt>
              <dd>{detail.raw_image_count}</dd>
              <dt>Infrared images</dt>
              <dd>{detail.infrared_image_count}</dd>
              {detail.raw_tcir_vmax_proxy_kt != null && (
                <>
                  <dt>Raw vmax proxy</dt>
                  <dd>{detail.raw_tcir_vmax_proxy_kt.toFixed(1)} kt <em>(unvalidated)</em></dd>
                </>
              )}
              {detail.infrared_tcir_vmax_proxy_kt != null && (
                <>
                  <dt>Infrared vmax proxy</dt>
                  <dd>{detail.infrared_tcir_vmax_proxy_kt.toFixed(1)} kt <em>(unvalidated)</em></dd>
                </>
              )}
            </dl>

            {detail.per_image_anomaly_scores?.some((a) => a.is_anomaly) && (
              <p className="caveat">
                Flagged anomalous:{' '}
                {detail.per_image_anomaly_scores.filter((a) => a.is_anomaly).map((a) => a.filename).join(', ')}
              </p>
            )}

            {detail.unavailable_data_groups?.length > 0 && (
              <p className="caveat">
                Missing data groups: {detail.unavailable_data_groups.join(', ')} — not sourced yet.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  )
}
