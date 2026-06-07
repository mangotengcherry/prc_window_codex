import unittest

from app.analysis.interaction_2d import build_interaction_heatmap
from app.analysis.ranking import rank_l3_features
from app.analysis.window_1d import analyze_single_window
from app.repository import SyntheticRepository
from app.synthetic_data import make_synthetic_frame


class PrototypeAnalysisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = make_synthetic_frame(seed=7, wafers=360)
        cls.repo = SyntheticRepository(cls.frame)

    def test_catalog_exposes_products_features_and_l3_items(self):
        catalog = self.repo.get_catalog()

        self.assertIn("P_ALPHA", catalog["products"])
        self.assertIn("cd_a", catalog["l1_features"])
        self.assertIn("l3_x", catalog["l3_items"])
        self.assertIn("cd_a", catalog["current_specs"])

    def test_ranking_puts_known_strong_feature_near_top_for_l3(self):
        ranking = rank_l3_features(
            self.frame,
            product_id="P_ALPHA",
            l3_items=["l3_x", "l3_y"],
            l1_features=["cd_a", "thk_b", "ovl_c", "time_since_pm"],
        )

        l3_x_top = ranking["by_l3"]["l3_x"][0]
        l3_y_top = ranking["by_l3"]["l3_y"][0]

        self.assertEqual("cd_a", l3_x_top["l1_feature_name"])
        self.assertEqual("thk_b", l3_y_top["l1_feature_name"])
        self.assertGreater(l3_x_top["priority_score"], 0)

    def test_single_window_finds_u_shape_center_candidate(self):
        result = analyze_single_window(
            self.frame,
            product_id="P_ALPHA",
            l1_feature_name="cd_a",
            l3_item_name="l3_x",
            bin_count=10,
            min_wafer_count=20,
            max_allowed_loss_rate=0.45,
        )

        best = result["candidate_specs"][0]

        self.assertGreaterEqual(best["target"], 43.0)
        self.assertLessEqual(best["target"], 47.0)
        self.assertGreater(best["ppm_improvement"], 0)
        self.assertEqual("wafer", result["denominators"]["production_loss"])
        self.assertEqual("chip", result["denominators"]["defect_ppm"])

    def test_interaction_heatmap_marks_unreliable_cells(self):
        heatmap = build_interaction_heatmap(
            self.frame,
            product_id="P_ALPHA",
            l1_feature_x="cd_a",
            l1_feature_y="ovl_c",
            l3_item_name="l3_z",
            x_bins=6,
            y_bins=6,
            min_wafer_count=15,
        )

        self.assertEqual(36, len(heatmap["cells"]))
        self.assertEqual(6, heatmap["x_bin_count"])
        self.assertEqual(6, heatmap["y_bin_count"])
        self.assertIn("x_center", heatmap["cells"][0])
        self.assertIn("y_center", heatmap["cells"][0])
        self.assertTrue(any(cell["unreliable"] for cell in heatmap["cells"]))
        self.assertTrue(any(cell["defect_ppm"] > 0 for cell in heatmap["cells"]))


if __name__ == "__main__":
    unittest.main()


class PrototypeApiTest(unittest.TestCase):
    def test_fastapi_rank_endpoint_returns_l3_groups(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.post(
            "/api/rank",
            json={
                "product_id": "P_ALPHA",
                "selected_l3_items": ["l3_x"],
                "selected_l1_features": ["cd_a", "thk_b", "ovl_c", "time_since_pm"],
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertIn("l3_x", response.json()["data"]["by_l3"])
