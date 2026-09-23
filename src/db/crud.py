"""
CRUD helper operations for IDMAP data persistence using Prisma Client Python & Neon DB.
Includes graceful fallback if database operations fail or are disabled.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("idmap.db")


async def log_prediction(
    event_id: Optional[int],
    predicted_category: str,
    severity: str,
    anomaly_error: float,
    vmax_proxy_kt: float,
    confidence: float = 1.0,
    district_forecasts: Optional[List[Dict[str, Any]]] = None
) -> Optional[str]:
    """Persists a model prediction and optional district evacuation forecasts."""
    try:
        from src.db.db import prisma
        if prisma is None or not prisma.is_connected():
            return None

        prediction = await prisma.modelprediction.create(
            data={
                "eventId": event_id,
                "predictedCategory": predicted_category,
                "severity": severity,
                "anomalyError": float(anomaly_error),
                "vmaxProxyKt": float(vmax_proxy_kt),
                "confidence": float(confidence),
            }
        )

        if district_forecasts and prediction:
            for dist in district_forecasts:
                await prisma.districtforecast.create(
                    data={
                        "predictionId": prediction.id,
                        "districtName": dist.get("district_name", "Unknown"),
                        "riskScore": float(dist.get("risk_score", 0.0)),
                        "shelterCapacity": int(dist.get("shelter_capacity", 0)),
                        "evacuationTarget": int(dist.get("evacuation_target", 0)),
                        "ndrfTeamsAllocated": int(dist.get("ndrf_teams", 0)),
                    }
                )

        return prediction.id if prediction else None
    except Exception as e:
        logger.warning(f"Failed to log prediction to Neon DB: {e}")
        return None


async def log_shap_attribution(
    prediction_id: str,
    base_value: float,
    shap_values: Dict[str, float]
) -> Optional[str]:
    """Persists SHAP feature importance attributions for a given prediction."""
    try:
        from src.db.db import prisma
        if prisma is None or not prisma.is_connected():
            return None

        shap_rec = await prisma.shapattribution.create(
            data={
                "predictionId": prediction_id,
                "baseValue": float(base_value),
                "shapValues": json.dumps(shap_values),
            }
        )
        return shap_rec.id if shap_rec else None
    except Exception as e:
        logger.warning(f"Failed to log SHAP attribution to Neon DB: {e}")
        return None


async def log_agent_advisory(
    event_id: Optional[int],
    prompt: str,
    advisory_text: str,
    citations: List[Dict[str, Any]]
) -> Optional[str]:
    """Persists a generated AI agent advisory report and vector search citations."""
    try:
        from src.db.db import prisma
        if prisma is None or not prisma.is_connected():
            return None

        advisory = await prisma.agentadvisory.create(
            data={
                "eventId": event_id,
                "prompt": prompt,
                "advisoryText": advisory_text,
                "citations": json.dumps(citations),
            }
        )
        return advisory.id if advisory else None
    except Exception as e:
        logger.warning(f"Failed to log advisory to Neon DB: {e}")
        return None


async def log_human_feedback(
    advisory_id: str,
    rating: int,
    is_helpful: bool,
    is_verified: bool = False,
    corrections: Optional[str] = None
) -> Optional[str]:
    """Persists human expert feedback, star rating, and corrections for an AI advisory."""
    try:
        from src.db.db import prisma
        if prisma is None or not prisma.is_connected():
            return None

        feedback = await prisma.humanfeedback.create(
            data={
                "advisoryId": advisory_id,
                "rating": int(rating),
                "isHelpful": bool(is_helpful),
                "isVerified": bool(is_verified),
                "corrections": corrections,
            }
        )
        return feedback.id if feedback else None
    except Exception as e:
        logger.warning(f"Failed to log human feedback to Neon DB: {e}")
        return None


async def log_whatif_simulation(
    base_id: int,
    delta_wind_speed_kt: float,
    new_coastal_distance_km: Optional[float],
    simulated_risk_category: str,
    simulated_severity: str
) -> Optional[str]:
    """Persists scenario simulation parameters and resulting risk metrics."""
    try:
        from src.db.db import prisma
        if prisma is None or not prisma.is_connected():
            return None

        sim = await prisma.whatifsimulation.create(
            data={
                "baseId": base_id,
                "deltaWindSpeedKt": float(delta_wind_speed_kt),
                "newCoastalDistanceKm": float(new_coastal_distance_km) if new_coastal_distance_km else None,
                "simulatedRiskCategory": simulated_risk_category,
                "simulatedSeverity": simulated_severity,
            }
        )
        return sim.id if sim else None
    except Exception as e:
        logger.warning(f"Failed to log what-if simulation to Neon DB: {e}")
        return None


async def fetch_advisories_with_feedback(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves advisories alongside human feedback ratings."""
    try:
        from src.db.db import prisma
        if prisma is None or not prisma.is_connected():
            return []

        advisories = await prisma.agentadvisory.find_many(
            take=limit,
            order={"createdAt": "desc"},
            include={"feedback": True}
        )
        results = []
        for adv in advisories:
            results.append({
                "id": adv.id,
                "event_id": adv.eventId,
                "prompt": adv.prompt,
                "advisory_text": adv.advisoryText,
                "citations": json.loads(adv.citations) if isinstance(adv.citations, str) else adv.citations,
                "created_at": adv.createdAt.isoformat() if isinstance(adv.createdAt, datetime) else str(adv.createdAt),
                "feedback": {
                    "rating": adv.feedback.rating,
                    "is_helpful": adv.feedback.isHelpful,
                    "is_verified": adv.feedback.isVerified,
                    "corrections": adv.feedback.corrections
                } if adv.feedback else None
            })
        return results
    except Exception as e:
        logger.warning(f"Failed to fetch advisories from Neon DB: {e}")
        return []
