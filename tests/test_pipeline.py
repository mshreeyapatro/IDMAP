"""
End-to-End Automated Integration Test Suite for IDMAP.

Tests:
1. Agent toolsfact registry
2. XGBoost risk prediction & SHAP explainability engine
3. What-if scenario simulation engine
4. Emergency resource & shelter planning engine
5. Multimodal satellite image analysis pipeline
6. FastAPI backend endpoint responses
"""

import sys
from pathlib import Path
import unittest
import numpy as np
from PIL import Image
import io

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent import tools
from src.layer2.risk_xgboost import explainability
from src.agent import whatif_engine, resource_planner
from src.cv_models import analyze_image


class TestIDMAPPipeline(unittest.TestCase):

    def test_01_project_status(self):
        status = tools.get_project_status()
        self.assertIsInstance(status, dict)
        self.assertIn(1, status)
        self.assertEqual(status[1]["status"], "done")

    def test_02_events_list(self):
        events = tools.list_events()
        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)
        self.assertIn("cyclone_id", events[0])

    def test_03_shap_explainability(self):
        # Base ID 25 is storm MADI in master dataset
        res = explainability.explain_event(25)
        self.assertNotIn("error", res)
        self.assertEqual(res["base_id"], 25)
        self.assertIn("predicted_risk_score", res)
        self.assertIn("top_feature_contributions", res)
        self.assertGreater(len(res["top_feature_contributions"]), 0)

    def test_04_whatif_simulation(self):
        res = whatif_engine.simulate_whatif(25, delta_wind_speed_kt=20.0, new_coastal_distance_km=50.0)
        self.assertNotIn("error", res)
        self.assertEqual(res["base_id"], 25)
        self.assertIn("simulation", res)
        self.assertGreater(res["simulation"]["risk_score_delta"], 0)

    def test_05_resource_planning(self):
        res = resource_planner.get_resource_plan(district_name="Puri", severity_level="High")
        self.assertNotIn("error", res)
        self.assertIn("district_plan", res)
        plan = res["district_plan"]
        self.assertEqual(plan["district"], "Puri")
        self.assertGreater(plan["people_to_evacuate"], 0)
        self.assertGreater(plan["multipurpose_shelters_required"], 0)

    def test_06_image_analysis_pipeline(self):
        # Create synthetic image
        img = Image.fromarray((np.random.rand(128, 128) * 255).astype(np.uint8))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        res = analyze_image.analyze_uploaded_image(buf.getvalue())

        self.assertNotIn("error", res)
        self.assertIn("vmax_proxy_kt", res)
        self.assertIn("intensity_category", res)
        self.assertIn("reconstruction_error", res)
        self.assertIn("predicted_risk_score", res)

    def test_07_live_weather_feed(self):
        feed = tools.get_live_weather_feed()
        self.assertIsInstance(feed, dict)
        self.assertIn("stations", feed)
        self.assertGreaterEqual(len(feed["stations"]), 6)
        self.assertIn("max_coastal_wind_speed_kt", feed)

    def test_08_live_satellite_feed(self):
        feed = tools.get_live_satellite_feed()
        self.assertIsInstance(feed, dict)
        self.assertIn("nasa_gibs", feed)
        self.assertIn("mosdac_isro", feed)

    def test_09_live_shap_explainability(self):
        res = explainability.explain_custom_features(wind_speed_kt=75.0, coastal_distance_km=60.0)
        self.assertNotIn("error", res)
        self.assertEqual(res["mode"], "live_forecast")
        self.assertIn("predicted_risk_score", res)
        self.assertIn("top_feature_contributions", res)
        self.assertGreater(len(res["top_feature_contributions"]), 0)

    def test_10_analyze_live_satellite(self):
        feed = tools.get_live_satellite_feed()
        tile_url = feed.get("nasa_gibs", {}).get("tile_snapshot_url")
        import urllib.request
        req = urllib.request.Request(tile_url, headers={"User-Agent": "Mozilla/5.0"})
        image_bytes = urllib.request.urlopen(req, timeout=5).read()
        res = analyze_image.analyze_uploaded_image(image_bytes)
        self.assertNotIn("error", res)
        self.assertIn("vmax_proxy_kt", res)
        self.assertIn("predicted_risk_score", res)

    def test_11_unified_live_survey(self):
        from src.agent import unified_survey
        survey = unified_survey.generate_unified_live_survey()
        self.assertNotIn("error", survey)
        self.assertEqual(survey["state"], "Odisha")
        self.assertIn("district_survey_matrix", survey)
        self.assertGreaterEqual(len(survey["district_survey_matrix"]), 10)


if __name__ == "__main__":
    unittest.main()



