"""
AI Retraining & Data Flywheel Exporter for IDMAP.
Extracts persisted database records from Neon DB to construct training datasets for:
1. LLM Supervised Fine-Tuning (SFT) - JSONL instruction format.
2. Direct Preference Optimization (DPO) - Preference pairs.
3. Tabular ML Models (XGBoost & Autoencoder) - Cleaned CSV/Parquet formats.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("idmap.retraining")

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "retraining"
DATA_DIR.mkdir(parents=True, exist_ok=True)


async def export_llm_sft_dataset(min_rating: int = 4, output_file: str = "sft_advisory_dataset.jsonl") -> str:
    """
    Queries Neon DB via Prisma for advisories rated min_rating stars or verified by human experts,
    formatting them as OpenAI/HuggingFace style SFT chat instruction messages.
    """
    out_path = DATA_DIR / output_file
    try:
        from src.db.db import prisma
        if prisma is None or not prisma.is_connected():
            logger.warning("Prisma DB not connected. Generating sample fallback SFT dataset structure.")
            _write_sample_sft(out_path)
            return str(out_path)

        advisories = await prisma.agentadvisory.find_many(
            include={"feedback": True}
        )

        records = []
        for adv in advisories:
            # Include if rated highly or explicitly verified
            if adv.feedback and (adv.feedback.rating >= min_rating or adv.feedback.isVerified):
                system_prompt = (
                    "You are IDMAP's expert disaster response AI advisory agent for Odisha state emergency authorities. "
                    "Provide evidence-grounded, zero-hallucination cyclone risk assessments and evacuation guidance."
                )
                assistant_response = adv.feedback.corrections if adv.feedback.corrections else adv.advisoryText

                records.append({
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": adv.prompt},
                        {"role": "assistant", "content": assistant_response}
                    ],
                    "metadata": {
                        "advisory_id": adv.id,
                        "rating": adv.feedback.rating,
                        "verified": adv.feedback.isVerified
                    }
                })

        with open(out_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")

        logger.info(f"Successfully exported {len(records)} SFT training samples to {out_path}")
        return str(out_path)
    except Exception as e:
        logger.error(f"Error exporting SFT dataset: {e}")
        _write_sample_sft(out_path)
        return str(out_path)


def _write_sample_sft(out_path: Path):
    """Fallback sample generator to ensure dataset directory structure is always valid."""
    sample = {
        "messages": [
            {
                "role": "system",
                "content": "You are IDMAP disaster response agent. Provide evidence-backed cyclone advisories."
            },
            {
                "role": "user",
                "content": "Generate emergency advisory report for Base ID 1205 (Very Severe Cyclonic Storm)."
            },
            {
                "role": "assistant",
                "content": "# IDMAP Cyclone Emergency Advisory\n- Severity: EXTREME\n- Evacuation: Coastal Kendrapara & Jagatsinghpur districts."
            }
        ],
        "metadata": {"sample": True}
    }
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(sample) + "\n")


async def export_llm_dpo_dataset(output_file: str = "dpo_advisory_dataset.jsonl") -> str:
    """
    Constructs Direct Preference Optimization (DPO) preference pairs (chosen vs rejected)
    from advisories with high ratings vs low ratings.
    """
    out_path = DATA_DIR / output_file
    try:
        from src.db.db import prisma
        if prisma is None or not prisma.is_connected():
            _write_sample_dpo(out_path)
            return str(out_path)

        advisories = await prisma.agentadvisory.find_many(include={"feedback": True})
        
        high_rated = [a for a in advisories if a.feedback and a.feedback.rating >= 4]
        low_rated = [a for a in advisories if a.feedback and a.feedback.rating <= 2]

        dpo_pairs = []
        for high in high_rated:
            matching_lows = [l for l in low_rated if l.eventId == high.eventId]
            for low in matching_lows:
                dpo_pairs.append({
                    "prompt": high.prompt,
                    "chosen": high.feedback.corrections if high.feedback.corrections else high.advisoryText,
                    "rejected": low.advisoryText,
                    "metadata": {
                        "chosen_rating": high.feedback.rating,
                        "rejected_rating": low.feedback.rating
                    }
                })

        with open(out_path, "w", encoding="utf-8") as f:
            for pair in dpo_pairs:
                f.write(json.dumps(pair) + "\n")

        logger.info(f"Successfully exported {len(dpo_pairs)} DPO preference pairs to {out_path}")
        return str(out_path)
    except Exception as e:
        logger.error(f"Error exporting DPO dataset: {e}")
        _write_sample_dpo(out_path)
        return str(out_path)


def _write_sample_dpo(out_path: Path):
    sample = {
        "prompt": "Generate emergency advisory report for Base ID 1205.",
        "chosen": "# Detailed Advisory with Citations\n- Action: Mandatory evacuation within 10km of coastline.",
        "rejected": "Generic cyclone summary without district-level details.",
        "metadata": {"sample": True}
    }
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(sample) + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(export_llm_sft_dataset())
    asyncio.run(export_llm_dpo_dataset())
