"""
Unit tests for Neon DB Prisma CRUD operations and AI retraining dataset export pipeline.
"""

import pytest
import asyncio
from pathlib import Path
from src.retraining import exporter, retrain_pipeline
from src.db import crud as db_crud


@pytest.mark.asyncio
async def test_sft_dataset_export():
    """Verify SFT dataset exporter produces valid JSONL structure."""
    out_path = await exporter.export_llm_sft_dataset(output_file="test_sft_dataset.jsonl")
    assert Path(out_path).exists()
    
    with open(out_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0
        assert "messages" in lines[0]


@pytest.mark.asyncio
async def test_dpo_dataset_export():
    """Verify DPO dataset exporter produces valid preference pairs."""
    out_path = await exporter.export_llm_dpo_dataset(output_file="test_dpo_dataset.jsonl")
    assert Path(out_path).exists()

    with open(out_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0
        assert "prompt" in lines[0]


@pytest.mark.asyncio
async def test_retraining_pipeline():
    """Verify full automated retraining pipeline execution."""
    report = await retrain_pipeline.run_retraining_pipeline()
    assert report["status"] == "success"
    assert "sft_dataset_path" in report
    assert "ml_models_evaluated" in report
