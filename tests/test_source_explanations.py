from copy import deepcopy
import json
from pathlib import Path
from random import Random
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from tests.browser_client import TestClient
from pydantic import ValidationError

from randomyst.api import create_app
from randomyst.engine import NumberEngine
from randomyst.interpretation import ExplanationRepository
from randomyst.models import DrawRequest, SourceCard, SourceExplanation

ROOT = Path(__file__).resolve().parents[1]


class SourceExplanationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = NumberEngine()
        cls.repository = ExplanationRepository(cls.engine.iching)
        request = DrawRequest.model_validate(json.loads((ROOT / "examples/draw_request.json").read_text()))
        cls.draw = cls.engine.draw(request, rng=Random(1102))

    def test_all_64_hexagrams_and_384_lines_bind_to_exact_original(self):
        for number, row in self.repository.by_id.items():
            for position in range(1, 7):
                result = self.repository.hexagram(number, position)
                judgment, line = result["cards"][:2]
                self.assertEqual(judgment["text"], row["scripture"])
                self.assertEqual(line["text"], next(l["scripture"] for l in row["lines"] if l["id"] == position))
                self.assertEqual(line["source"]["key"], f"iching__{number}_{position}")
                for card in (judgment, line):
                    SourceCard.model_validate(card)
                    self.assertEqual(card["translation"]["label"], "AI_TRANSLATION")
                    self.assertEqual(card["translation"]["review_status"], "UNREVIEWED")
                    self.assertTrue(card["translation"]["text"])

    def test_missing_thoan_32_is_not_filled_or_disguised_as_a_translation(self):
        result = self.repository.hexagram(32, 2)
        self.assertTrue(any(g["text_type"] == "TUAN_COMMENTARY" for g in result["source_gaps"]))
        self.assertFalse(any(c["text_type"] == "TUAN_COMMENTARY" for c in result["cards"]))
        # Xiang for the moving line is retrieved with its own position key.
        xiang = next(c for c in result["cards"] if c["text_type"] == "LINE_XIANG_COMMENTARY")
        self.assertEqual(xiang["source"]["key"], "iching__32_2")
        self.assertIsNone(xiang["translation"])

    def test_bazi_stem_and_birth_season_match_source_without_casting_season(self):
        base = self.draw["trace"]["bazi"]
        for stem, essence in self.repository.bazi["stems"].items():
            for branch, season in [(2, "Spring"), (5, "Summer"), (8, "Autumn"), (11, "Winter")]:
                bazi = deepcopy(base)
                bazi["natal"]["pillars"][2]["stem_zh"] = stem
                bazi["natal"]["zhis"][1] = branch
                result = self.repository.natal(bazi)
                self.assertEqual(result["cards"][0]["text"], essence["verse"])
                self.assertEqual(result["cards"][1]["text"], essence["detail"])
                self.assertEqual(result["cards"][2]["text"], essence["seasonal"][season])
                self.assertTrue(all(c["source"]["repository"] == "vhphuoc1102/tinix-bazi" for c in result["cards"]))
                self.assertTrue(all(c["label"] == "SOURCE_ORIGINAL" and c["translation"] is None for c in result["cards"]))

    def test_unknown_structure_is_a_gap_and_override_does_not_rewrite_source(self):
        bazi = deepcopy(self.draw["trace"]["bazi"])
        bazi.update(structure="Sát Cách", primary_used="Kim", overridden=True)
        result = self.repository.natal(bazi)
        self.assertEqual(result["structure"], "Sát Cách")
        self.assertEqual(len(result["cards"]), 3)
        self.assertTrue(result["source_gaps"])
        self.assertEqual(result["primary_used"], "Kim")
        self.assertEqual(result["primary_calculated"], bazi["primary_dung_than"])

    def test_reading_does_not_mutate_saved_numbers_or_computed_context(self):
        before = deepcopy(self.draw)
        result = self.repository.explain(self.draw)
        SourceExplanation.model_validate(result)
        self.assertEqual(self.draw, before)
        self.assertFalse(result["model_called"])
        self.assertFalse(result["affects_generation"])
        self.assertFalse(result["affects_evaluation"])
        result["relation"]["the"]["element"] = "fake"
        self.assertEqual(self.draw, before)

    def test_response_validation_rejects_wrong_references_hash_and_source_url(self):
        card = self.repository.hexagram(17, 2)["cards"][1]
        for field in ("references", "source_text_sha256"):
            changed = deepcopy(card)
            changed["translation"][field] = ["another-evidence"] if field == "references" else "0" * 64
            with self.assertRaises(ValidationError):
                SourceCard.model_validate(changed)
        changed = deepcopy(card)
        changed["source"]["url"] = "https://example.com/invented"
        with self.assertRaises(ValidationError):
            SourceCard.model_validate(changed)
        changed = deepcopy(self.draw)
        changed["trace"]["maihoa"]["original"]["lines_bottom_to_top"][0] ^= 1
        with self.assertRaises(ValueError):
            self.repository.explain(changed)

    def test_api_readonly_idempotent_and_historical_v3_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app(Path(directory) / "draws.sqlite3")
            with TestClient(app) as client:
                payload = json.loads((ROOT / "examples/draw_request.json").read_text())
                payload["request_id"] = str(uuid4())
                first = client.post("/api/v1/draw", json=payload).json()
                before = client.get("/api/v1/history").json()
                with patch.object(app.state.engine, "draw", side_effect=AssertionError("Must not reroll")):
                    for _ in range(2):
                        response = client.get("/api/v1/interpretation/" + payload["request_id"])
                        self.assertEqual(response.status_code, 200, response.text)
                        self.assertEqual(response.json()["context_id"], payload["request_id"])
                        SourceExplanation.model_validate(response.json())
                        self.assertEqual(client.get("/api/v1/draw/" + payload["request_id"]).json(), first)
                self.assertEqual(client.get("/api/v1/history").json(), before)
                self.assertEqual(client.post("/api/v1/draw", json=payload).json(), first)
                missing = client.get("/api/v1/interpretation/" + str(uuid4()))
                self.assertEqual(missing.status_code, 404)
                self.assertEqual(client.get("/api/v1/interpretation/invalid-id").status_code, 422)
                archived = json.loads((ROOT / "docs/archive/draw_response_v3.json").read_text())
                client.storage.append({'kind':'DRAW','key':archived['request_id'],'data':archived,
                                       'signature':app.state.signer.sign('DRAW',archived),'identity':None})
                old = client.get("/api/v1/interpretation/" + archived["request_id"])
                self.assertEqual(old.status_code, 200, old.text)
                self.assertEqual(old.json()["rules_version"], archived["rules_version"])
                self.assertEqual(client.get("/api/v1/draw/" + archived["request_id"]).json(), archived)


if __name__ == "__main__":
    unittest.main()
