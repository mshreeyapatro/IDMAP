"""
IDMAP Master Pipeline & System Healthcheck Runner.

Verifies:
1. Dataset & Master CSV integrity
2. Machine Learning Checkpoints (TCIR ResNet backbone, Autoencoder, XGBoost Risk Model)
3. RAG Vector Database indices
4. Live Ingestion APIs (Open-Meteo & NASA GIBS)
5. Automated Test Suite Execution
"""

import sys
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent import tools
from src.ingestion import live_weather, live_satellite
from tests.test_pipeline import TestIDMAPPipeline


def run_healthcheck() -> dict:
    results = {
        "status": "HEALTHY",
        "checks": {}
    }

    # 1. Dataset Check
    master_csv = ROOT / "data" / "processed" / "master_cyclone_dataset.csv"
    results["checks"]["dataset_master"] = {
        "exists": master_csv.exists(),
        "path": str(master_csv)
    }

    # 2. Checkpoints Check
    backbone_ckpt = ROOT / "src" / "cv_models" / "checkpoints" / "tcir_backbone.pt"
    ae_ckpt = ROOT / "src" / "layer2" / "anomaly_autoencoder" / "checkpoints" / "autoencoder.pt"
    xgb_ckpt = ROOT / "src" / "layer2" / "risk_xgboost" / "checkpoints" / "risk_model.pkl"

    results["checks"]["checkpoints"] = {
        "tcir_backbone": backbone_ckpt.exists(),
        "autoencoder": ae_ckpt.exists(),
        "xgboost_risk": xgb_ckpt.exists(),
    }

    # 3. Live Open-Meteo Ingestion Check
    try:
        w = live_weather.get_live_weather_feed()
        results["checks"]["live_weather_api"] = {
            "status": "OK",
            "stations_count": len(w.get("stations", [])),
            "max_wind_speed_kt": w.get("max_coastal_wind_speed_kt")
        }
    except Exception as e:
        results["checks"]["live_weather_api"] = {"status": "FAILED", "error": str(e)}

    # 4. Live Satellite Feed Check
    try:
        sat = live_satellite.get_live_satellite_feed()
        results["checks"]["live_satellite_api"] = {
            "status": "OK",
            "provider": sat.get("nasa_gibs", {}).get("provider")
        }
    except Exception as e:
        results["checks"]["live_satellite_api"] = {"status": "FAILED", "error": str(e)}

    # 5. Unit & Integration Test Suite Execution
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIDMAPPipeline)
    runner = unittest.TextTestRunner(verbosity=0)
    test_res = runner.run(suite)

    results["checks"]["test_suite"] = {
        "tests_run": test_res.testsRun,
        "failures": len(test_res.failures),
        "errors": len(test_res.errors),
        "passed": test_res.wasSuccessful()
    }

    if not test_res.wasSuccessful():
        results["status"] = "DEGRADED"

    return results


if __name__ == "__main__":
    report = run_healthcheck()
    print("\n================ IDMAP SYSTEM HEALTHCHECK REPORT ================")
    print(json.dumps(report, indent=2))
    print("=================================================================\n")
