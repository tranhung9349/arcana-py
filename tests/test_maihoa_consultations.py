from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from tests.browser_client import TestClient

from randomyst.api import create_app
from randomyst.interpretation import ExplanationRepository
from randomyst.maihoa import IchingRepository
from randomyst.maihoa_models import MaiHoaRequest, MaiHoaResponse
from randomyst.maihoa_service import MaiHoaRules, MaiHoaService, relation

ROOT = Path(__file__).resolve().parents[1]


def payload(time="2026-10-25T09:00:00+07:00", topic="TRADE"):
    return {"request_id": str(uuid4()), "question": "Việc giao dịch tôi đang chuẩn bị có những điểm gì cần cân nhắc?",
            "topic": topic, "casting": {"mode": "CUSTOM", "custom_timestamp": time}}


class MaiHoaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.explanations = ExplanationRepository()
        cls.repository = cls.explanations.iching
        cls.service = MaiHoaService(cls.explanations)

    def test_classical_examples_and_pure_hexagram_exceptions(self):
        for values, expected in [
            ((5,12,17,9), (49,1,31,44)),  # Quan Mai, vol. 1
            ((6,3,16,4), (44,5,50,1)),    # Mau Don, vol. 1
            ((1,1,7,8), (1,5,14,43)),    # Qian -> Da You; mutual from changed
            ((1,1,6,8), (2,4,16,39)),    # Kun -> Yu; mutual from changed
        ]:
            variables = dict(zip(("Y","M","D","H"), values))
            result = self.repository.calculate_source(variables)
            self.assertEqual((result["original"]["hexagram_id"],result["moving_line"],
                              result["display_hexagrams"]["changed"]["hexagram_id"],
                              result["display_hexagrams"]["mutual"]["hexagram_id"]), expected)
            legacy = self.repository.calculate(variables)
            self.assertEqual(legacy["core_version"], "maihoa-ymdh-v1")
            self.assertEqual(result["original"], legacy["original"])
            self.assertEqual(result["the"], legacy["the"])
            if expected[0] in (1,2):
                self.assertEqual(legacy["display_hexagrams"]["mutual"]["hexagram_id"], expected[0])
                self.assertEqual(result["mutual_basis"], "CHANGED_FOR_PURE")

    def test_relationship_direction_is_not_reversed(self):
        self.assertEqual(relation("Mộc","Mộc"), "SAME")
        self.assertEqual(relation("Mộc","Thủy"), "USE_GENERATES_BODY")
        self.assertEqual(relation("Mộc","Thổ"), "BODY_CONTROLS_USE")
        self.assertEqual(relation("Mộc","Hỏa"), "BODY_GENERATES_USE")
        self.assertEqual(relation("Mộc","Kim"), "USE_CONTROLS_BODY")

    def test_thirty_topic_rules_bind_to_distinct_source_evidence(self):
        rules = self.service.rules
        for topic in rules.config["topics"].values():
            self.assertEqual(len(topic["relations"]),5)
            for rule in topic["relations"].values():
                evidence = rules.evidence[rule["evidence_id"]]
                self.assertEqual(rule["quote"], evidence["text"])
                self.assertEqual(evidence["section"], topic["section"])
        wealth = rules.config["topics"]["WEALTH"]["relations"]
        self.assertEqual(wealth["BODY_CONTROLS_USE"]["indication"], "FAVOURABLE")
        self.assertEqual(wealth["SAME"]["indication"], "FAVOURABLE")
        self.assertEqual(wealth["BODY_GENERATES_USE"]["indication"], "CAUTION")

    def test_missing_or_tampered_source_fails_closed(self):
        source = ROOT / "data/reference/maihoa"
        for filename in ("volume_2.wikitext", "compiled.json"):
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp)
                for p in source.iterdir():
                    if p.is_file(): shutil.copyfile(p, target/p.name)
                if filename.endswith("wikitext"):
                    (target/filename).write_text((target/filename).read_text()+"改")
                else:
                    data=json.loads((target/filename).read_text())
                    data["evidence"]["WEALTH_SAME"]["text"]="invented"
                    data["evidence"]["WEALTH_SAME"]["text_sha256"]=sha256(b"invented").hexdigest()
                    (target/filename).write_text(json.dumps(data))
                with patch("randomyst.maihoa_service.DIRECTORY",target), self.assertRaises(RuntimeError):
                    MaiHoaRules()

    def test_chart_roles_remain_tied_to_original_body_for_both_positions(self):
        seen = set()
        for hour in range(0,24,2):
            request=MaiHoaRequest.model_validate(payload(f"2026-10-25T{hour:02}:00:00+07:00"))
            result=self.service.consult(request)
            chart=result["chart"]; seen.add(chart["the"]["position"])
            self.assertEqual(chart["the"]["position"],"UPPER" if chart["moving_line"]<=3 else "LOWER")
            self.assertEqual(chart["mutual_body"]["position"],chart["the"]["position"])
            self.assertEqual(chart["mutual_use"]["position"],chart["dung"]["position"])
            self.assertEqual(chart["changed_use"]["position"],chart["dung"]["position"])
            self.assertEqual(sum(a!=b for a,b in zip(chart["original"]["lines_bottom_to_top"],chart["changed"]["lines_bottom_to_top"])),1)
        self.assertEqual(seen,{"UPPER","LOWER"})

    def test_topic_changes_reading_not_cast_or_birth_personalization(self):
        base=payload(topic="WEALTH")
        first=self.service.consult(MaiHoaRequest.model_validate(base))
        changed={**base,"topic":"PLANNING","question":"Tôi đang tính một việc khác, có điểm nào cần xem xét?"}
        second=self.service.consult(MaiHoaRequest.model_validate(changed))
        self.assertEqual(first["chart"],second["chart"])
        self.assertNotEqual(first["findings"][0]["rule_id"],second["findings"][0]["rule_id"])
        self.assertNotEqual(first["findings"][0]["evidence_refs"],second["findings"][0]["evidence_refs"])
        self.assertEqual(first["findings"][1:],second["findings"][1:])

    def test_season_is_casting_jie_context_not_lunar_month_or_birth(self):
        before=self.service.consult(MaiHoaRequest.model_validate(payload("2026-02-04T03:02:07+07:00")))
        after=self.service.consult(MaiHoaRequest.model_validate(payload("2026-02-04T03:02:08+07:00")))
        self.assertEqual(before["season"]["period"],"EARTH_MONTH")
        self.assertEqual(after["season"]["period"],"SPRING")
        self.assertEqual(before["season"]["strong_element"],"Thổ")
        self.assertEqual(after["season"]["strong_element"],"Mộc")
        self.assertEqual(before["calendar"]["maihoa_inputs"],after["calendar"]["maihoa_inputs"])
        self.assertEqual(after["calendar_policy"]["provenance"],"PRODUCT_CONVENTION")

    def test_midnight_beijing_and_clock_uncertainty_are_preserved(self):
        first=self.service.consult(MaiHoaRequest.model_validate(payload("2026-10-25T22:59:59+07:00")))
        p=payload("2026-10-25T23:00:00+07:00");p["casting"]["clock_uncertainty_seconds"]=1
        second=self.service.consult(MaiHoaRequest.model_validate(p))
        self.assertNotEqual(first["calendar"]["effective_date"],second["calendar"]["effective_date"])
        self.assertIn("CLOCK_BOUNDARY",[w["code"] for w in second["warnings"]])
        self.assertEqual(second["calendar"]["civil_datetime"],p["casting"]["custom_timestamp"])

    def test_current_uses_clicked_time_and_reports_skew_without_substitution(self):
        p=payload();clicked=p["casting"]["custom_timestamp"]
        p["casting"]={"mode":"CURRENT","clicked_at":clicked}
        received=datetime.fromisoformat(clicked)+timedelta(seconds=45)
        result=self.service.consult(MaiHoaRequest.model_validate(p),received_at=received)
        self.assertEqual(result["calendar"]["civil_datetime"],clicked)
        self.assertEqual(result["created_at"],received.isoformat())
        self.assertIn("CLIENT_CLOCK_SKEW",[w["code"] for w in result["warnings"]])

    def test_reading_does_not_call_number_generation_or_claim_full_verdict(self):
        with patch("randomyst.engine.NumberEngine.draw",side_effect=AssertionError("Number generation called")):
            result=self.service.consult(MaiHoaRequest.model_validate(payload()))
        MaiHoaResponse.model_validate(result)
        self.assertNotIn("score",result)
        self.assertFalse(result["summary"]["is_full_divination_verdict"])
        self.assertEqual(result["automated_scope"],"INTERNAL_TRIGRAM_RELATIONS")
        self.assertEqual(result["interpretation_review_status"],"AI_DRAFT_UNREVIEWED")

    def test_response_rejects_unbound_evidence(self):
        result=self.service.consult(MaiHoaRequest.model_validate(payload()))
        result["findings"][0]["evidence_refs"]=["invented"]
        with self.assertRaises(ValueError): MaiHoaResponse.model_validate(result)

    def test_api_idempotency_history_replay_and_number_history_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=create_app(Path(tmp)/"draws.sqlite3")
            with TestClient(app) as client:
                p=payload();before=client.get("/api/v1/history").json()
                response=client.post("/api/v1/maihoa/consultations",json=p)
                self.assertEqual(response.status_code,200,response.text)
                first=response.json()
                with patch.object(app.state.maihoa,"consult",side_effect=AssertionError("Saved session recomputed")):
                    self.assertEqual(client.post("/api/v1/maihoa/consultations",json=p).json(),first)
                    self.assertEqual(client.get("/api/v1/maihoa/consultations/"+p["request_id"]).json(),first)
                self.assertEqual(client.get("/api/v1/history").json(),before)
                self.assertEqual(len(client.get("/api/v1/maihoa/history").json()["consultations"]),1)
                changed=deepcopy(p);changed["question"]="Tôi muốn hỏi một việc khác, cần cân nhắc gì?"
                self.assertEqual(client.post("/api/v1/maihoa/consultations",json=changed).status_code,409)
                self.assertEqual(client.get("/api/v1/maihoa/consultations/"+str(uuid4())).status_code,404)
                self.assertEqual(client.get("/api/v1/maihoa/consultations/not-a-uuid").status_code,422)
                deferred=client.get("/api/v1/maihoa/rules").json()["deferred_features"]
                self.assertEqual({v["status"] for v in deferred},{"FUTURE_FEATURE"})
            with TestClient(create_app(Path(tmp)/"draws.sqlite3"), storage=client.storage) as restarted:
                self.assertEqual(restarted.get("/api/v1/maihoa/consultations/"+p["request_id"]).json(),first)

    def test_concurrent_retries_save_one_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=create_app(Path(tmp)/"draws.sqlite3")
            with TestClient(app) as client:
                p=payload()
                with ThreadPoolExecutor(max_workers=3) as pool:
                    rows=list(pool.map(lambda _:client.post("/api/v1/maihoa/consultations",json=p).json(),range(3)))
                self.assertEqual(rows[0],rows[1]);self.assertEqual(rows[1],rows[2])
                self.assertEqual(len(client.get("/api/v1/maihoa/history").json()["consultations"]),1)

    def test_api_rejects_unsupported_methods_topics_birth_and_invalid_clock(self):
        with tempfile.TemporaryDirectory() as tmp, TestClient(create_app(Path(tmp)/"draws.sqlite3")) as client:
            invalid=[]
            for field,value in [("question","   "),("topic","LIU_YAO"),("casting_method","THREE_COINS"),("birth",{"year":1994})]:
                p=payload();p[field]=value;invalid.append(p)
            for time in ("2026-10-25T09:00:00","2026-10-25T09:00:00+08:00","2031-01-01T09:00:00+07:00"):
                invalid.append(payload(time))
            p=payload();p["casting"]={"mode":"CURRENT"};invalid.append(p)
            for p in invalid:
                self.assertEqual(client.post("/api/v1/maihoa/consultations",json=p).status_code,422)


if __name__ == "__main__":
    unittest.main()
