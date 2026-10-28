"""Offline Mai Hoa source/coverage audit; never opens SQLite or creates a draw."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

from randomyst.interpretation import ExplanationRepository
from randomyst.maihoa_models import MaiHoaRequest, MaiHoaResponse
from randomyst.maihoa_service import MaiHoaService
from randomyst.time_engine import resolve_maihoa

ROOT = Path(__file__).resolve().parents[1]


def run():
    service = MaiHoaService(ExplanationRepository())  # Verifies all source/quote hashes.
    original_ids, states = set(), set()
    differences = 0
    count = 0
    for y,m,d,h in product(range(1,13),range(1,13),range(1,31),range(1,13)):
        variables = dict(zip(("Y","M","D","H"),(y,m,d,h)))
        old = service.iching.calculate(variables)
        new = service.iching.calculate_source(variables)
        for key in ("original","upper","lower","moving_line","the","dung"):
            if old[key] != new[key]: raise RuntimeError("Casting changed outside the source mutual policy")
        if old["display_hexagrams"]["changed"] != new["display_hexagrams"]["changed"]:
            raise RuntimeError("Changed hexagram drift")
        if old["display_hexagrams"]["mutual"] != new["display_hexagrams"]["mutual"]:
            differences += 1
            if new["original"]["hexagram_id"] not in (1,2):
                raise RuntimeError("Mutual changed for a non-pure original")
        original_ids.add(new["original"]["hexagram_id"])
        states.add((new["original"]["hexagram_id"],new["moving_line"]))
        count += 1
    real_cases = {}
    instant = datetime(2026,1,1,tzinfo=timezone(timedelta(hours=7)))
    for offset in range(366*12):
        candidate = instant + timedelta(hours=offset*2)
        core = service.iching.calculate_source(resolve_maihoa(candidate)["maihoa_inputs"])
        key = (core["original"]["hexagram_id"],core["moving_line"])
        real_cases.setdefault(key,candidate.isoformat())
        if len(real_cases) == len(states): break
    evaluated = 0
    for timestamp in real_cases.values():
        for topic in service.rules.config["topics"]:
            request = MaiHoaRequest.model_validate({"request_id":"ed0601b7-c172-47f9-a945-dc65b7f7c8a5",
                "question":"Tình huống mẫu kiểm chứng phạm vi phép luận Mai Hoa.","topic":topic,
                "casting":{"mode":"CUSTOM","custom_timestamp":timestamp}})
            result = service.consult(request)
            MaiHoaResponse.model_validate(result)
            if result["summary"]["is_full_divination_verdict"] or "score" in result:
                raise RuntimeError("Unsupported verdict or score")
            evaluated += 1
    if len(real_cases) != 192 or count != 51840 or len(original_ids) != 64:
        raise RuntimeError("Unexpected Mai Hoa state-space coverage")
    paths = ["config/maihoa_rules.json","randomyst/maihoa.py","randomyst/maihoa_service.py",
             "randomyst/maihoa_models.py","data/reference/maihoa/manifest.json",
             "data/reference/maihoa/compiled.json"]
    return {"checked_date_utc7":"2026-10-25","rules_version":service.rules.config["rules_version"],
        "corpus_version":service.rules.config["corpus_version"],
        "sha256":{p:sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        "source_revisions_verified":3,"bound_evidence_quotes":len(service.rules.evidence),
        "topic_relation_entries":sum(len(t["relations"]) for t in service.rules.config["topics"].values()),
        "auxiliary_relation_entries":len(service.rules.config["auxiliary_relations"]),
        "integer_input_tuples_audited":count,"original_hexagrams":len(original_ids),
        "distinct_original_moving_states":len(states),"source_mutual_differs_from_legacy_tuples":differences,
        "casting_unchanged_except_source_mutual_policy":True,
        "real_time_representatives":len(real_cases),"topic_readings_schema_validated":evaluated,
        "last_representative_timestamp":max(real_cases.values()),
        "database_accessed":False,"api_called":False,"number_generation_called":False,
        "predictive_accuracy_tested":False,"expert_semantic_review_completed":False,
        "limitations":["Exhaustive tuples are arithmetic coverage, not calendar frequencies.",
                       "Topic/schema coverage verifies implementation, not truth of divination.",
                       "Season precedence, timezone and leap-month handling remain declared product conventions."]}


if __name__ == "__main__":
    result = run()
    target = ROOT / "docs/research/maihoa_source_validation.json"
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"output":str(target),"tuples":result["integer_input_tuples_audited"],
                      "readings":result["topic_readings_schema_validated"]},ensure_ascii=False))
