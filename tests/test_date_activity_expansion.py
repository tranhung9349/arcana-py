from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.browser_client import TestClient
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from randomyst.api import create_app
from randomyst.date_activities import ACTIVITIES, BY_ACTIVITY, GROUPS
from randomyst.date_engine import DateEngine, analyze, pillars
from randomyst.date_models import DateRules, DateSearchRequest, DateSearchResponse

ROOT = Path(__file__).resolve().parents[1]


def request(activity, start="2026-10-08", end=None, details=True):
    roles = BY_ACTIVITY[activity]["subject_count"]
    births = ("1994-10-08T05:00:00+07:00", "1990-06-15T09:30:00+07:00")
    return {"activity": activity, "subjects": [
        {"subject_id": f"person_{i}", "birth": {"civil_datetime": births[i]}}
        for i in range(roles)], "date_range": {"start": start, "end": end or start}, "include_details": details}


class MajorDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = DateEngine()

    def search(self, payload):
        data = self.engine.search(DateSearchRequest.model_validate(payload))
        DateSearchResponse.model_validate(data)
        return data

    def test_seven_groups_eighteen_enabled_and_literal_hour_tokens(self):
        config = self.engine.evaluator.config
        enabled = [a for a in config.activities if a.enabled]
        self.assertEqual(len(enabled), 18)
        self.assertEqual({a.group_id for a in enabled}, {g["group_id"] for g in GROUPS})
        self.assertEqual(sum(a.hour_evaluation_mode == "DAY_ONLY" for a in enabled), 9)
        for a in enabled:
            self.assertEqual(a.subject_count, len(a.subject_roles))
            if a.hour_evaluation_mode == "DAY_ONLY":
                self.assertIsNone(a.provider_hour_token)
            else:
                self.assertEqual(a.provider_hour_token, a.provider_token)
        for key in ("BETROTHAL_NACAI", "BETROTHAL_COVENANT", "RECEIVE_ASSETS"):
            self.assertIsNone(BY_ACTIVITY[key]["provider_hour_token"])

    def test_all_enabled_activities_response_schema_and_subject_roles(self):
        schema = Draft202012Validator(json.loads((ROOT/"schemas/date_search_response.schema.json").read_text()))
        for a in ACTIVITIES:
            if not a["enabled"]:
                continue
            with self.subTest(activity=a["activity"]):
                result = self.search(request(a["activity"]))
                schema.validate(result)
                self.assertEqual(result["activity_spec"]["event_anchor"], a["event_anchor"])
                self.assertEqual([p["role"] for p in result["subject_summaries"]], a["subject_roles"])
                if a["hour_evaluation_mode"] == "DAY_ONLY":
                    self.assertEqual(result["evaluated_windows"], 0)
                    self.assertEqual(result["days"][0]["hour_evaluation"], "NOT_SUPPORTED")
                    self.assertEqual(result["days"][0]["recommended_minutes"], 0)
                    for p in result["days"][0]["day_periods"]:
                        self.assertNotIn("hour_branch", p)
                        self.assertNotIn("hour_activity_status", p)
                        self.assertNotIn("hour_yi", p["facts"])
                        self.assertTrue(all(len(person["elements"]) == 2 for person in p["subject_assessments"]))

    def test_day_only_does_not_read_hour_pillars_or_yiji(self):
        engine = self.engine
        data = DateSearchRequest.model_validate(request("LAND_BREAKING"))
        profile = engine.profile(data.subjects[0])
        start = datetime.fromisoformat("2026-10-08T08:00:00+07:00")
        end = start + timedelta(hours=1)
        original = engine.day_period(start, end, data.activity, [profile])
        facts = deepcopy(engine.calendar.at(start))
        facts.pop("civil_hour")
        facts["gans"] = facts["gans"][:3]
        facts["zhis"] = facts["zhis"][:3]
        facts["pillars_zh"] = facts["pillars_zh"][:3]
        with patch.object(engine.calendar, "at", return_value=facts):
            self.assertEqual(original, engine.day_period(start, end, data.activity, [profile]))

    def test_new_hours_require_direct_support_legacy_keeps_its_gate(self):
        engine = self.engine
        start = datetime.fromisoformat("2026-10-12T08:00:00+07:00")
        facts = deepcopy(engine.calendar.at(start))
        facts.update(gans=(0,0,0,0), zhis=(0,0,0,0))
        facts["civil_day"].update(yi=["交易", "开市"], ji=[])
        facts["civil_hour"].update(yi=[], ji=[])
        profile = {"subject_id": "a", "primary": "Mộc", "hy": ("Thủy",), "ky": (),
                   "natal_branches": (1,1,1,1), "birth_boundary": "CLEAR_WITHIN_BOUND"}
        with patch.object(engine.calendar, "at", return_value=facts), patch.object(engine.evaluator, "evaluate", return_value=([], {})):
            modern = engine.window(start, start+timedelta(hours=1), "TRADE", [profile])
            legacy = engine.window(start, start+timedelta(hours=1), "BUSINESS_OPENING", [profile])
            self.assertGreaterEqual(modern["score"], 75)
            self.assertEqual(modern["hour_activity_status"], "NOT_LISTED")
            self.assertEqual(modern["grade"], "NORMAL")
            self.assertEqual(legacy["grade"], "GOOD")
            facts["civil_hour"]["yi"] = ["交易"]
            self.assertEqual(engine.window(start,start+timedelta(hours=1),"TRADE",[profile])["grade"], "GOOD")

    def test_new_scopes_do_not_inherit_natal_taboo_blocks_and_rites_warn_month_clash(self):
        evaluator = self.engine.evaluator
        for fact, table in (("sat_chu", evaluator.config.month_tables.sat_chu), ("tho_tu", evaluator.config.month_tables.tho_tu)):
            for month, target in enumerate(table):
                facts = {"gans":(0,0,0,0), "zhis":(0,month,target,0), "calendar_class":"HOANG_DAO"}
                for activity in ("HOME_ENTRY", "LAND_BREAKING", "ANCESTOR_RITE"):
                    matches, values = evaluator.evaluate(facts, activity)
                    self.assertTrue(values[fact])
                    self.assertTrue(any(m["effect"] == "WARN" and m["rule_id"].endswith("_V2_NOTE") for m in matches))
                    self.assertFalse(any(m["effect"] == "BLOCK" and m["rule_id"].startswith(("SAT_CHU", "THO_TU")) for m in matches))
        facts = {"gans":(0,0,0,0), "zhis":(0,0,6,0), "calendar_class":"HOANG_DAO"}
        rites,_ = evaluator.evaluate(facts,"ANCESTOR_RITE")
        construction,_ = evaluator.evaluate(facts,"LAND_BREAKING")
        self.assertEqual(next(r["effect"] for r in rites if r["dedupe_group"] == "MONTH_CLASH"), "WARN")
        self.assertEqual(next(r["effect"] for r in construction if r["dedupe_group"] == "MONTH_CLASH"), "BLOCK")

    def test_day_validity_boundaries_jie_and_final_year_padding(self):
        for day in ("2026-10-08", "2030-12-31"):
            periods = self.search(request("CONTRACT_RITE",day))["days"][0]["day_periods"]
            self.assertEqual(sum(p["duration_seconds"] for p in periods), 86400)
            self.assertEqual(periods[0]["start_at"], day+"T00:00:00+07:00")
            for a,b in zip(periods,periods[1:]):
                self.assertEqual(a["end_at"],b["start_at"])
            self.assertTrue(any("T22:00:00" in p["start_at"] for p in periods))
            self.assertTrue(any("T23:00:00" in p["start_at"] for p in periods))
            if day == "2026-10-08":
                self.assertEqual(len(periods),4)
                self.assertIn("2026-10-08T13:29:17+07:00",[p["start_at"] for p in periods])

    def test_day_only_rejects_hour_filters_and_betrothal_needs_two_people(self):
        for activity in ("LAND_BREAKING", "BETROTHAL_NACAI", "BETROTHAL_COVENANT"):
            data = request(activity)
            data["allowed_hours"] = {"start":"06:00", "end":"22:00"}
            with self.assertRaises(ValidationError):
                DateSearchRequest.model_validate(data)
        for activity in ("BETROTHAL_NACAI", "BETROTHAL_COVENANT"):
            data = request(activity)
            data["subjects"].pop()
            with self.assertRaises(ValidationError):
                DateSearchRequest.model_validate(data)

    def test_day_summary_keeps_all_validity_periods_and_filtered_is_distinct(self):
        original = self.engine.day_period
        def good(*args):
            result = original(*args)
            result.update(grade="GOOD",score=85,raw_score=85,assessment_state="COMPLETE",hard_exclusions=[])
            return result
        data = request("LAND_BREAKING", details=False)
        with patch.object(self.engine,"day_period",side_effect=good):
            day = self.search(data)["days"][0]
            self.assertEqual(len(day["day_periods"]),3)
            self.assertEqual(len(day["recommended_day_periods"]),4)
            self.assertEqual(day["recommended_windows"],[])
        data["allowed_weekdays"] = [0]  # 8 Oct 2026 is a Thursday.
        day = self.search(data)["days"][0]
        self.assertEqual(day["assessment_state"],"FILTERED")
        self.assertEqual(day["hour_evaluation"],"NOT_EVALUATED")
        self.assertEqual(day["evaluated_periods"],0)

    def test_conflicting_raw_trade_and_contract_data_stays_unresolved(self):
        for key in ("TRADE", "CONTRACT_RITE"):
            result = self.search(request(key,"2026-02-09"))
            periods = result["days"][0]["windows" if key == "TRADE" else "day_periods"]
            unresolved = [p for p in periods if p["day_activity_status"] == "UNRESOLVED"]
            self.assertTrue(unresolved)
            self.assertTrue(all(p["score"] is None and p["grade"] is None for p in unresolved))

    def test_93_day_betrothal_builds_each_natal_once_outside_period_loop(self):
        with patch("randomyst.date_engine.analyze",wraps=analyze) as a, patch("randomyst.date_engine.pillars",wraps=pillars) as p:
            result = self.search(request("BETROTHAL_NACAI","2026-10-12","2027-01-12",False))
        self.assertEqual((a.call_count,p.call_count),(2,2))
        self.assertEqual(len(result["days"]),93)
        self.assertEqual(result["evaluated_windows"],0)
        self.assertGreaterEqual(result["evaluated_periods"],279)
        self.assertEqual(result["personal_comparisons"],2*result["evaluated_periods"])

    def test_response_rejects_fake_hour_capability_and_wrong_totals(self):
        result = self.search(request("LAND_BREAKING"))
        for field, value in (("evaluation_mode","DAY_AND_HOUR"),("personal_comparisons",0)):
            bad = deepcopy(result);bad[field] = value
            with self.assertRaises(ValidationError):DateSearchResponse.model_validate(bad)
        bad = deepcopy(result)
        bad["days"][0]["recommended_windows"] = [{"start_at":"x","end_at":"y","hour_branch":"子"}]
        with self.assertRaises(ValidationError):DateSearchResponse.model_validate(bad)

    def test_registry_tampering_rejected(self):
        rules = json.loads((ROOT/"config/mvp2_date_rules.json").read_text())
        rules["activities"][1]["provider_hour_token"] = "订婚"
        with self.assertRaises(ValidationError):DateRules.model_validate(rules)

    def test_api_all_groups_no_draw_or_maihoa_side_effects_and_disabled_422(self):
        with tempfile.TemporaryDirectory() as tmp, TestClient(create_app(Path(tmp)/"test.sqlite3")) as client:
            before = [client.get(url).json() for url in ("/api/v1/history","/api/v1/maihoa/history")]
            registry = client.get("/api/v2/auspicious-dates/rules").json()
            self.assertEqual(len(registry["groups"]),7)
            self.assertEqual(sum(a["enabled"] for a in registry["activities"]),18)
            with patch.object(client.app.state.engine,"draw",side_effect=AssertionError("No draws")), patch.object(client.app.state.maihoa,"consult",side_effect=AssertionError("No Mai Hoa")):
                for activity in ACTIVITIES:
                    response = client.post("/api/v2/auspicious-dates/search",json=request(activity["activity"]))
                    self.assertEqual(response.status_code,200 if activity["enabled"] else 422,response.text)
            after = [client.get(url).json() for url in ("/api/v1/history","/api/v1/maihoa/history")]
            self.assertEqual(before,after)


if __name__ == "__main__":
    unittest.main()
