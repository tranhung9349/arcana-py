"""Real JS engine integration, calendar boundaries and shared LLM configuration."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from randomyst.ai_context import natal_context
from randomyst.bazi_engine import TinixBaziEngine
from randomyst.bazi_models import BaziRequest, BaziResponse
from randomyst.bazi_pipeline import prepare_analyst
from randomyst.bazi_service import BaziService
from randomyst.engine import EngineError
from tests.test_bazi_consultations import payload


class TinixBaziTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = BaziService()

    def consult(self, when="1994-10-08T05:00:00+07:00", gender="male", year=2026):
        request = payload(when)
        request["birth"]["gender"] = gender
        request["target_year"] = year
        return self.service.consult(BaziRequest.model_validate(request))

    def test_full_source_engine_replaces_old_natal_evaluator(self):
        with patch("randomyst.bazi_rules.BaziRules.evaluate", side_effect=AssertionError("legacy evaluator called")):
            saved = self.consult()
        result = saved["engine"]["result"]
        self.assertEqual(result["scores"]["ngu_hanh_vn"], {"Kim":18,"Mộc":21,"Thủy":10,"Hỏa":6,"Thổ":5})
        self.assertEqual(saved["assessment"]["strength"], "WEAK")
        self.assertEqual(saved["assessment"]["balance"]["preferred"], ["Hỏa"])
        self.assertEqual(len(result["luck_cycles"]), 12)
        self.assertTrue(all(len(c["luu_nien"]) == 10 for c in result["luck_cycles"]))
        self.assertEqual(result["annual"]["ganzhiVN"], "Bính Ngọ")
        self.assertIn("tu_binh_chan_thuyen", result["analysis"]["phan_tich_nang_cao"])
        self.assertTrue(result["classics"])
        self.assertTrue(result["interpretation"])

    def test_midnight_late_rat_hour_and_jie_seconds_match_existing_calendar(self):
        for when in ("2024-02-09T21:59:59+07:00", "2024-02-09T22:00:00+07:00",
                     "2024-02-09T23:00:00+07:00", "2026-02-04T03:02:07+07:00",
                     "2026-02-04T03:02:08+07:00", "1950-01-01T00:00:00+07:00"):
            with self.subTest(when=when):
                saved = self.consult(when)
                self.assertEqual(saved["engine"]["result"]["pillars"],
                    [p["stem"]["zh"] + p["branch_zh"] for p in saved["chart"]["pillars"]])

    def test_gender_reverses_cycles_and_year_changes_annual_without_changing_pillars(self):
        male, female, later = self.consult(), self.consult(gender="female"), self.consult(year=2027)
        first = male["engine"]["result"]
        self.assertEqual(first["luck_cycles"][0]["can_chi"], "Giáp Tuất")
        self.assertEqual(female["engine"]["result"]["luck_cycles"][0]["can_chi"], "Nhâm Thân")
        self.assertEqual(first["pillars"], later["engine"]["result"]["pillars"])
        self.assertEqual(later["engine"]["result"]["annual"]["ganzhiVN"], "Đinh Mùi")

    def test_september_first_1994_keeps_fire_year_na_yin_separate_from_metal_day_master(self):
        saved = self.consult("1994-09-01T07:00:00+07:00")
        self.assertEqual(saved["engine"]["result"]["pillars"], ["甲戌", "壬申", "庚寅", "庚辰"])
        self.assertEqual(saved["engine"]["result"]["chart"][0]["nap_am"], "Sơn Đầu Hỏa")
        day = saved["chart"]["pillars"][2]["stem"]
        self.assertEqual((day["name"], day["element"]), ("Canh", "Kim"))
        source = json.dumps(saved["engine"]["result"]["interpretation"], ensure_ascii=False)
        self.assertIn("Sơn Đầu Hỏa", source)
        self.assertIn("Hành của Nhật chủ: Kim", source)
        self.assertNotIn("Kim mệnh:", source)
        context = natal_context(saved)
        prepared = prepare_analyst(context)
        identity = json.loads(prepared["messages"][-1]["content"])["element_identity"]
        self.assertEqual(identity["year_na_yin"], "Sơn Đầu Hỏa")
        self.assertEqual(identity["day_master"], {"stem": "Canh", "element": "Kim", "polarity": "Dương"})
        self.assertNotIn("civil_datetime", prepared["messages"][-1]["content"])
        january = self.consult("1994-01-09T07:00:00+07:00")
        self.assertNotEqual(january["engine"]["result"]["pillars"], saved["engine"]["result"]["pillars"])

    def test_source_random_prose_is_reproducible_and_does_not_keep_personal_cache(self):
        first, second = self.consult(), self.consult()
        self.assertEqual(first["engine"], second["engine"])
        self.assertEqual(first["findings"], second["findings"])
        self.assertFalse(hasattr(self.service.rules, "_cache"))

    def test_snapshot_detects_changed_engine_data_and_mismatched_chart(self):
        saved = self.consult()
        changed = deepcopy(saved)
        changed["engine"]["result"]["scores"]["ngu_hanh_vn"]["Hỏa"] += 1
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            BaziResponse.model_validate(changed)
        changed = deepcopy(saved)
        changed["chart"]["pillars"][0]["stem"]["zh"] = "乙"
        with self.assertRaisesRegex(ValueError, "pillars differ"):
            BaziResponse.model_validate(changed)

    def test_llm_receives_engine_luck_and_provenance_without_birth_identity(self):
        saved = self.consult()
        context = natal_context(saved)
        prepared = prepare_analyst(context)
        message = json.loads(prepared["messages"][-1]["content"])
        self.assertEqual(message["luck_cycles"]["status"], "AVAILABLE")
        self.assertIn("engine:provenance", {f.id for f in context.facts})
        self.assertIn("engine:tu_binh_chan_thuyen", {f.id for f in context.facts})
        self.assertNotIn("civil_datetime", prepared["messages"][-1]["content"])
        self.assertNotIn(saved["display_name"], prepared["messages"][-1]["content"])
        self.assertNotIn("openrouter", prepared["messages"][-1]["content"].casefold())

    def test_subprocess_failure_returns_controlled_error(self):
        with patch("randomyst.bazi_engine.subprocess.run", side_effect=subprocess.TimeoutExpired("private", 15)):
            with self.assertRaises(EngineError) as raised:
                self.consult()
        self.assertEqual(raised.exception.code, "BAZI_ENGINE_FAILED")
        self.assertNotIn("private", str(raised.exception))

    def test_supported_features_are_advertised(self):
        self.assertEqual(self.service.rules.overview()["features"],
            ["Homepage", "BaziChart", "LuckCycles", "Interpretation", "Consultant", "ConsultationHistory"])


if __name__ == "__main__":
    unittest.main()
