"""Natal facts, conditional reasoning, immutable storage and integration coverage."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

from tests.browser_client import TestClient
from jsonschema import Draft202012Validator
from lunar_python.util import LunarUtil

from randomyst.api import create_app
from randomyst.bazi_facts import chart_from_birth, facts_for, stem_fact, ten_god, relations_for, ELEMENT_ZH
from randomyst.bazi_models import BaziRequest, BaziResponse, BaziReadingRequest, BaziReadingSnapshot, NatalChart
from randomyst.bazi_rules import BaziRules, digest
from randomyst.bazi_service import BaziService
from randomyst.bazi_narrative import compose, NARRATIVE_VERSION
from randomyst.engine import EngineError
from randomyst.sampling import GENERATES, CONTROLS, ELEMENTS
from randomyst.time_engine import STEMS_ZH, BRANCHES, BRANCHES_ZH

ROOT = Path(__file__).resolve().parents[1]


def payload(time="1994-10-08T05:00:00+07:00", topic="GENERAL"):
    return {"request_id": str(uuid4()), "display_name": "Hồ sơ kiểm thử", "birth": {"civil_datetime": time}, "topic": topic, "question": ""}


def synthetic_chart(gans, zhis):
    """Synthetic rules fixture, deliberately distinct from calendar integration tests."""
    chart = chart_from_birth(BaziRequest.model_validate(payload()).birth).model_dump(mode="json")
    for i, (p, g, z) in enumerate(zip(chart["pillars"], gans, zhis)):
        p.update(stem=stem_fact(g, gans[2], "stem:"+p["position"], i == 2), branch_index=z,
                 branch=BRANCHES[z], branch_zh=BRANCHES_ZH[z], branch_element=ELEMENT_ZH[LunarUtil.WU_XING_ZHI[BRANCHES_ZH[z]]],
                 hidden_stems=[stem_fact(STEMS_ZH.index(h), gans[2], f"hidden:{p['position']}:{j}") for j, h in enumerate(LunarUtil.ZHI_HIDE_GAN[BRANCHES_ZH[z]])])
    e = chart["pillars"][1]["branch_element"];day = chart["pillars"][2]["stem"]["element"]
    chart["month"].update(branch=BRANCHES[zhis[1]], branch_index=zhis[1], element=e, seasonal_support=e == day or GENERATES[e] == day)
    return NatalChart.model_validate(chart)


class BaziConsultationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = BaziService()
        cls.legacy_rules = BaziRules()

    def assess(self, gans, zhis):
        chart = synthetic_chart(gans, zhis)
        facts = facts_for(chart, self.service.rules.config["tables"])
        # Keep archived rule regressions separate from the new Tinix service.
        assessment, findings = self.legacy_rules.evaluate(chart, facts)
        return chart, facts, assessment, {f.finding_id: f for f in findings}

    def test_ten_gods_all_100_pairs_against_independent_five_element_polarity_formula(self):
        for day in range(10):
            for other in range(10):
                a, b, same = ELEMENTS[day//2], ELEMENTS[other//2], day % 2 == other % 2
                if a == b: expected = "PEER" if same else "ROB_WEALTH"
                elif GENERATES[a] == b: expected = "EATING_GOD" if same else "HURTING_OFFICER"
                elif CONTROLS[a] == b: expected = "INDIRECT_WEALTH" if same else "DIRECT_WEALTH"
                elif GENERATES[b] == a: expected = "INDIRECT_RESOURCE" if same else "DIRECT_RESOURCE"
                else: expected = "SEVEN_KILLINGS" if same else "DIRECT_OFFICER"
                self.assertEqual(ten_god(day, other)[0], expected, (day, other))
        self.assertEqual(ten_god(0, 4), ("INDIRECT_WEALTH", "Thiên Tài"))
        self.assertEqual(ten_god(0, 5), ("DIRECT_WEALTH", "Chính Tài"))

    def test_twelve_hidden_stem_tables_and_main_qi_order(self):
        expected = ["癸", "己癸辛", "甲丙戊", "乙", "戊乙癸", "丙庚戊", "丁己", "己丁乙", "庚壬戊", "辛", "戊辛丁", "壬甲"]
        for z in range(12):
            chart = synthetic_chart([0, 0, 0, 0], [z]*4)
            self.assertEqual("".join(h.zh for h in chart.pillars[1].hidden_stems), expected[z])
            facts = facts_for(chart, self.service.rules.config["tables"])
            for root in facts.roots:
                self.assertEqual(root.level, "MAIN_QI" if root.stem_ref.endswith(":0") else "OTHER_QI")
        # Nhật chủ is not counted as an extra peer stem.
        self.assertEqual(chart.pillars[2].stem.ten_god, "DAY_MASTER")

    def test_calendar_instant_and_day_hour_jie_boundaries(self):
        def chart(t): return chart_from_birth(BaziRequest.model_validate(payload(t)).birth)
        c = chart("1994-10-08T05:00:00+07:00")
        self.assertEqual(c.beijing_datetime.hour, 6)
        self.assertEqual(c.civil_datetime, c.beijing_datetime)
        self.assertEqual("".join(p.stem.zh+p.branch_zh for p in c.pillars), "甲戌癸酉丁卯癸卯")
        before, after = chart("2024-02-09T21:59:59+07:00"), chart("2024-02-09T22:00:00+07:00")
        self.assertNotEqual(before.pillars[2].stem.index, after.pillars[2].stem.index)
        self.assertNotEqual(before.pillars[3].branch_index, after.pillars[3].branch_index)
        at_midnight = chart("2024-02-09T23:00:00+07:00")
        self.assertEqual(after.pillars[2].stem.index, at_midnight.pillars[2].stem.index)
        b, a = chart("2026-02-04T03:02:07+07:00"), chart("2026-02-04T03:02:08+07:00")
        self.assertNotEqual(b.pillars[0].branch_index, a.pillars[0].branch_index)
        self.assertNotEqual(b.pillars[1].branch_index, a.pillars[1].branch_index)
        for t in ("1950-01-01T00:00:00+07:00", "2026-12-31T23:59:59+07:00", "2000-02-29T00:00:00+07:00"):
            self.assertEqual(len(chart(t).pillars), 4)

    def test_all_branch_pairs_and_groups_require_distinct_tokens(self):
        tables = self.service.rules.config["tables"]
        harms = [{0,7},{1,6},{2,5},{3,4},{8,11},{9,10}]
        combinations = [{0,1},{2,11},{3,10},{4,9},{5,8},{6,7}]
        for x in range(12):
            for y in range(12):
                ps = [SimpleNamespace(stem=SimpleNamespace(index=0, name="Giáp"), branch_index=z,
                                      branch=BRANCHES[z], fact_id="pillar:"+str(i)) for i,z in enumerate([x,y])]
                kinds = {r["kind"] for r in relations_for(SimpleNamespace(pillars=ps), tables)}
                self.assertEqual("CLASH" in kinds, (x-y) % 12 == 6)
                self.assertEqual("HARM" in kinds, {x,y} in harms)
                self.assertEqual("SIX_COMBINATION" in kinds, {x,y} in combinations)
                self.assertEqual("SELF_PUNISHMENT" in kinds, x == y and x in (4,6,9,11))
        for zhis, expected in [([8,0,0,0],False), ([8,0,4,0],True)]:
            facts = facts_for(synthetic_chart([0]*4, zhis), tables)
            self.assertEqual(any(r.kind == "THREE_COMBINATION" for r in facts.relations), expected)
        c = synthetic_chart([0]*4,[2,3,4,4]);f = facts_for(c,tables)
        meeting = [r for r in f.relations if r.kind == "THREE_MEETING"]
        self.assertEqual(len(meeting),1);self.assertEqual(len(meeting[0].pillar_refs),4)
        self.assertFalse(any(r.transformation_assumed for r in f.relations))
        for branches, full in [([2,5,0,0],False),([2,5,8,0],True)]:
            f=facts_for(synthetic_chart([0]*4,branches),tables)
            self.assertEqual(any(r.kind=="PUNISHMENT" and len(r.tokens)==3 for r in f.relations),full)

    def test_strength_conjunctions_following_and_climate_conflict(self):
        _, _, strong, _ = self.assess([0,2,0,8],[2,2,4,0])
        self.assertEqual(strong.strength,"STRONG");self.assertEqual(strong.balance.preferred,["Hỏa"])
        _, _, weak, findings = self.assess([0,2,6,8],[2,0,3,11])
        self.assertEqual(weak.strength,"WEAK");self.assertTrue(weak.climate_conflict)
        self.assertIn("khác",findings["climate"].text)
        _, _, follow, _ = self.assess([4,6,0,8],[8,9,1,6])
        # Resource can be hidden in Sửu; that prevents a false all-opposition verdict.
        self.assertFalse(follow.possible_following)
        _, _, follow, findings = self.assess([4,6,0,6],[5,9,10,6])
        self.assertTrue(follow.possible_following);self.assertEqual(follow.strength,"MIXED")
        self.assertEqual(follow.balance.preferred,[]);self.assertEqual(findings["special_caution"].state,"UNRESOLVED")
        _, _, mixed, _ = self.assess([0,8,0,6],[2,9,4,6])
        self.assertEqual(mixed.strength,"MIXED");self.assertEqual(mixed.balance.restrain,[])

    def test_structure_uses_month_hidden_stems_and_never_falls_back_to_officer(self):
        _, _, assessment, _ = self.assess([2,9,0,1],[6,8,3,0])
        names = [c.ten_god for c in assessment.structures]
        self.assertIn("SEVEN_KILLINGS",names) # Geng in Shen, not Gui month stem.
        self.assertNotIn("DIRECT_RESOURCE",names)
        self.assertTrue(all(c.state=="CONDITIONAL" for c in assessment.structures))
        _, _, wealth, _ = self.assess([4,5,0,2],[6,4,3,0])
        self.assertEqual(wealth.structures[0].ten_god,"INDIRECT_WEALTH")
        self.assertIn("Thiên Tài",wealth.structures[0].name)
        self.assertIn("stem:year",wealth.structures[0].exposed_refs)
        _, _, lu, _ = self.assess([4,2,0,8],[0,2,4,6])
        self.assertIn("Kiến Lộc",lu.structures[0].name)

    def test_topic_and_question_change_prose_not_natal_facts(self):
        p = payload(); first = self.service.consult(BaziRequest.model_validate(p))
        for topic in ("CAREER","WEALTH","STUDY","RELATIONSHIPS"):
            second = self.service.consult(BaziRequest.model_validate({**p,"topic":topic,"question":"<script>ghi chú</script>"}))
            for key in ("chart","facts","assessment","findings"): self.assertEqual(first[key],second[key])
            self.assertNotEqual(first["reading"]["sections"],second["reading"]["sections"])
            self.assertEqual(second["reading"]["question"],"<script>ghi chú</script>")
            BaziResponse.model_validate(second)
        self.assertEqual(p["question"],"")

    def test_plain_takeaway_and_actions_cover_strength_states_without_personality_claims(self):
        summaries = []
        for gans, zhis, state in (([0,2,0,8],[2,2,4,0],"STRONG"),
                                  ([0,2,6,8],[2,0,3,11],"WEAK"),
                                  ([0,8,0,6],[2,9,4,6],"MIXED")):
            chart, facts, assessment, by_id = self.assess(gans, zhis)
            self.assertEqual(assessment.strength, state)
            findings = list(by_id.values())
            before = [value.model_dump() for value in (chart, facts, assessment, *findings)]
            actions = set()
            for topic in ("GENERAL", "CAREER", "WEALTH", "STUDY", "RELATIONSHIPS"):
                reading = compose(chart, facts, assessment, findings, topic, "Câu hỏi đang mở")
                self.assertEqual(reading.narrative_version, NARRATIVE_VERSION)
                self.assertEqual(reading.question, "Câu hỏi đang mở")
                takeaway = reading.summary + " " + reading.sections[0].text + " " + reading.sections[1].text
                self.assertNotRegex(takeaway, r"Nhật chủ|Thập Thần|tàng can|phù ức|Điều hậu|sinh xuất|nguyệt lệnh|khí thế")
                self.assertLessEqual(len(takeaway.split()), 130)
                self.assertEqual(reading.sections[0].title, "Bạn có thể làm gì?")
                self.assertIn("không phải dự báo", reading.sections[1].text)
                self.assertTrue(all(set(section.finding_refs) <= by_id.keys() for section in reading.sections))
                actions.add(reading.sections[0].text)
            self.assertEqual(len(actions), 5)
            summaries.append(reading.summary)
            self.assertEqual([value.model_dump() for value in (chart, facts, assessment, *findings)], before)
        self.assertEqual(len(set(summaries)), 3)

    def test_uncertainty_crossing_real_boundaries_is_rejected_without_silent_hour_choice(self):
        p=payload("2026-02-04T03:02:08+07:00");p["birth"]["clock_uncertainty_seconds"]=1
        with self.assertRaisesRegex(EngineError,"ranh đổi lá số"):
            self.service.consult(BaziRequest.model_validate(p))
        p=payload();p["birth"]["clock_uncertainty_seconds"]=30
        self.service.consult(BaziRequest.model_validate(p))
        # No warning is fabricated for an unspecified error bound.
        self.assertNotIn("warnings",self.service.consult(BaziRequest.model_validate(payload())))

    def test_reading_has_bound_references_and_rejects_tampering(self):
        result=self.service.consult(BaziRequest.model_validate(payload()))
        BaziResponse.model_validate(result)
        bad=deepcopy(result);bad["findings"][0]["fact_refs"]=["made-up"]
        with self.assertRaises(ValueError):BaziResponse.model_validate(bad)
        bad=deepcopy(result);bad["reading"]["sections"][0]["finding_refs"]=["made-up"]
        with self.assertRaises(ValueError):BaziResponse.model_validate(bad)
        result["evidence"][0]["text"]="mutated"
        self.assertNotEqual(self.service.consult(BaziRequest.model_validate(payload()))["evidence"][0]["text"],"mutated")

    def test_rules_and_raw_source_tampering_fail_closed(self):
        for relative in ("config/bazi_rules.json","data/reference/bazi/dtt_month.wikitext"):
            with tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)
                manifest=json.loads((ROOT/"data/reference/bazi/manifest.json").read_text())
                target=folder/"data/reference/bazi";target.mkdir(parents=True)
                (target/"manifest.json").write_text(json.dumps(manifest))
                for row in manifest["files"]:
                    path=folder/row["path"];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/row["path"]).read_bytes())
                path=folder/relative;path.write_bytes(path.read_bytes()+b" ")
                with patch("randomyst.bazi_rules.ROOT",folder),patch("randomyst.bazi_rules.DIRECTORY",target),patch("randomyst.bazi_rules.RULES_PATH",folder/"config/bazi_rules.json"):
                    with self.assertRaisesRegex(RuntimeError,"checksum"):BaziRules()

    def test_calendar_is_built_once_and_never_uses_draw_or_legacy_analysis(self):
        with patch("randomyst.bazi_facts.pillars",wraps=__import__("randomyst.time_engine",fromlist=["pillars"]).pillars) as calculate, \
             patch("randomyst.engine.NumberEngine.draw",side_effect=AssertionError("draw called")), \
             patch("randomyst.bazi.analyze",side_effect=AssertionError("legacy analysis called")):
            session=self.service.consult(BaziRequest.model_validate(payload()))
            self.assertEqual(calculate.call_count,1)
            with patch("randomyst.bazi_service.chart_from_birth",side_effect=AssertionError("chart recomputed")):
                row=self.service.reinterpret(session,BaziReadingRequest(reading_id=uuid4(),topic="WEALTH"))
            self.assertEqual(row["chart_sha256"],digest(session["chart"]))
            self.assertEqual(calculate.call_count,1)

    def test_api_idempotency_rereading_restart_and_history_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"runtime.sqlite3";app=create_app(path)
            with TestClient(app) as client:
                histories=["/api/v1/history","/api/v1/maihoa/history","/api/v1/coins/history"]
                before=[client.get(url).json() for url in histories]
                p=payload();url="/api/v1/bazi/consultations";response=client.post(url,json=p)
                self.assertEqual(response.status_code,200,response.text);first=response.json();BaziResponse.model_validate(first)
                with patch.object(app.state.bazi,"consult",side_effect=AssertionError("recomputed")):
                    self.assertEqual(client.post(url,json=p).json(),first)
                    self.assertEqual(client.get(url+"/"+p["request_id"]).json(),first)
                changed=deepcopy(p);changed["topic"]="CAREER"
                self.assertEqual(client.post(url,json=changed).status_code,409)
                context={"reading_id":str(uuid4()),"topic":"WEALTH","question":"Cách phối hợp nguồn lực?"}
                reading_url=url+"/"+p["request_id"]+"/readings"
                with patch("randomyst.bazi_service.chart_from_birth",side_effect=AssertionError("chart recomputed")):
                    r=client.post(reading_url,json=context);self.assertEqual(r.status_code,200,r.text);reading=r.json()
                with patch.object(app.state.bazi,"reinterpret",side_effect=AssertionError("reading recomputed")):
                    self.assertEqual(client.post(reading_url,json=context).json(),reading)
                self.assertEqual(client.post(reading_url,json={**context,"topic":"STUDY"}).status_code,409)
                self.assertEqual(client.get(url+"/"+p["request_id"]).json(),first)
                self.assertEqual(len(client.get(reading_url).json()["readings"]),2)
                self.assertEqual([client.get(u).json() for u in histories],before)
                self.assertEqual(len(client.get("/api/v1/bazi/history").json()["consultations"]),1)
                self.assertEqual(client.get(url+"/"+str(uuid4())).status_code,404)
                self.assertEqual(client.get(url+"/not-a-uuid").status_code,422)
                BaziReadingSnapshot.model_validate(reading)
            with TestClient(create_app(path), storage=client.storage) as restarted:
                self.assertEqual(restarted.get(url+"/"+p["request_id"]).json(),first)
                self.assertEqual(restarted.get(reading_url).json()["readings"][1],reading)

    def test_concurrent_retries_save_one_chart_and_one_extra_reading(self):
        with tempfile.TemporaryDirectory() as tmp,TestClient(create_app(Path(tmp)/"runtime.sqlite3")) as client:
            p=payload();url="/api/v1/bazi/consultations"
            with ThreadPoolExecutor(max_workers=3) as pool:
                results=list(pool.map(lambda _:client.post(url,json=p).json(),range(3)))
            self.assertEqual(results[0],results[1]);self.assertEqual(results[1],results[2])
            self.assertEqual(len(client.get("/api/v1/bazi/history").json()["consultations"]),1)
            context={"reading_id":str(uuid4()),"topic":"STUDY"};url+="/"+p["request_id"]+"/readings"
            with ThreadPoolExecutor(max_workers=3) as pool:
                results=list(pool.map(lambda _:client.post(url,json=context).json(),range(3)))
            self.assertEqual(results[0],results[1]);self.assertEqual(results[1],results[2])
            self.assertEqual(len(client.get(url).json()["readings"]),2)

    def test_invalid_birth_context_and_legacy_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp,TestClient(create_app(Path(tmp)/"runtime.sqlite3")) as client:
            bad=[]
            for time in ("1949-12-31T23:00:00+07:00","2027-01-01T00:00:00+07:00","2026-02-29T12:00:00+07:00", "2000-01-01T12:00:00", "2000-01-01T12:00:00+08:00", "2000-01-01T12:00:00.1+07:00"):
                bad.append(payload(time))
            for key,value in (("topic","HEALTH"),("casting",{}),("override_dung_than","Hỏa")):
                p=payload();p[key]=value;bad.append(p)
            p=payload();p["birth"]["civil_datetime"]="1994-10-08";bad.append(p)
            for p in bad:
                r=client.post("/api/v1/bazi/consultations",json=p);self.assertEqual(r.status_code,422,r.text)

    def test_exported_json_schemas_validate_real_responses(self):
        result=self.service.consult(BaziRequest.model_validate(payload()))
        for model,row in [(BaziRequest,payload()),(BaziResponse,result)]:
            validator=Draft202012Validator(model.model_json_schema());validator.validate(row)


if __name__ == "__main__":
    unittest.main()
