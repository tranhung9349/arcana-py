"""Exercise the public Tử Vi route against the pinned chart engine."""
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from randomyst.ai_client import AIConfig, CompatibleAIClient
from randomyst.api import create_app
from randomyst.snapshots import SignedSnapshot


class ZiweiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(ai_config=AIConfig())
        cls.client = TestClient(cls.app)

    def post(self, civil_datetime, gender="male"):
        return self.client.post("/api/v1/ziwei/consultations", json={
            "request_id": str(uuid4()), "civil_datetime": civil_datetime, "gender": gender,
        })

    def consultation(self, civil_datetime, gender="male"):
        response = self.post(civil_datetime, gender)
        self.assertEqual(response.status_code, 200, response.json())
        signed = SignedSnapshot(kind="ZIWEI", data=response.json(), signature=response.headers["X-Arcana-Signature"])
        return self.app.state.signer.verify(signed, "ZIWEI")

    def test_chart_and_reading_are_bound_to_the_same_palaces(self):
        with patch.object(CompatibleAIClient, "complete", side_effect=AssertionError("LLM called")):
            saved = self.consultation("1990-01-03T18:00:00+07:00")
        self.assertFalse(saved["model_called"])
        self.assertEqual(saved["engine"]["commit"], "78eafbf54d4b571833c78b921b1898be256e7dac")
        chart = saved["chart"]
        by_branch = {p["branch"]: p for p in chart["palaces"]}
        self.assertEqual(set(by_branch), set(range(12)))
        ming = by_branch[chart["ming_branch"]]
        self.assertEqual(ming["branch_name"], "Thìn")
        self.assertEqual([star["name"] for star in ming["stars"] if star["type"] == "major"], ["Thất Sát"])
        self.assertIn("Hỏa Tham", {p["title"] for p in saved["reading"]["patterns"]})
        for section in saved["reading"]["sections"]:
            self.assertIn(by_branch[section["palace_branch"]]["name"], section["text"])

    def test_late_rat_hour_uses_the_next_date(self):
        earlier = self.consultation("1990-01-03T22:59:59+07:00")
        later = self.consultation("1990-01-03T23:00:00+07:00")
        midnight = self.consultation("1990-01-04T00:00:00+07:00")
        self.assertEqual((earlier["effective_date"], earlier["hour_branch"]), ("1990-01-03", "Hợi"))
        self.assertEqual((later["effective_date"], later["hour_branch"]), ("1990-01-04", "Tý"))
        self.assertEqual(later["chart"], midnight["chart"])

    def test_leap_birth_preserves_the_calendar_date_and_uses_the_split_month(self):
        saved = self.consultation("2023-04-06T12:00:00+07:00")
        chart = saved["chart"]
        self.assertEqual(chart["lunar_date"], {"year": 2023, "month": 2, "day": 16, "leap": True})
        self.assertEqual(chart["chart_lunar_month"], 3)

    def test_invalid_dates_and_timezones_do_not_reach_the_engine(self):
        with patch.object(self.app.state.ziwei, "consult", side_effect=AssertionError("engine called")):
            for civil in ("1990-02-30T08:00:00+07:00", "1990-01-03T08:00:00+08:00"):
                self.assertEqual(self.post(civil).status_code, 422)
