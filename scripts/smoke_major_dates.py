"""Read-only localhost integration checks with synthetic birth profiles.

Uses an existing preview server; never creates a draw or consultation.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlparse

import httpx
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from randomyst.date_models import DateSearchRequest, DateSearchResponse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8766")
    parser.add_argument("--legacy-baseline", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT/"docs/research/mvp2_major_events_runtime_validation.json")
    args = parser.parse_args()
    url = urlparse(args.base_url)
    if url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost"):
        raise ValueError("This check only submits synthetic data to a local preview.")
    request_schema = Draft202012Validator(json.loads((ROOT/"schemas/date_search_request.schema.json").read_text()))
    response_schema = Draft202012Validator(json.loads((ROOT/"schemas/date_search_response.schema.json").read_text()))
    measurements = []
    with httpx.Client(base_url=args.base_url, timeout=30, trust_env=False) as client:
        registry = client.get("/api/v2/auspicious-dates/rules").json()
        enabled = [a for a in registry["activities"] if a["enabled"]]
        assert len(enabled) == 18 and len(registry["groups"]) == 7
        before = [client.get(path).json() for path in ("/api/v1/history", "/api/v1/maihoa/history")]

        def call(payload, label, target=5):
            DateSearchRequest.model_validate(payload)
            request_schema.validate(payload)
            started = time.perf_counter()
            response = client.post("/api/v2/auspicious-dates/search", json=payload)
            elapsed = time.perf_counter()-started
            response.raise_for_status()
            data = response.json()
            DateSearchResponse.model_validate(data)
            response_schema.validate(data)
            assert elapsed < target, (label, elapsed, target)
            measurements.append({"case":label, "http_seconds":round(elapsed,4), "target_seconds":target,
                                 "response_bytes":len(response.content), "days":len(data["days"]),
                                 "natal_analysis_count":data["natal_analysis_count"],
                                 "evaluation_mode":data["evaluation_mode"],
                                 "evaluated_windows":data["evaluated_windows"],
                                 "evaluated_periods":data["evaluated_periods"],
                                 "good_days":sum(d["grade"] == "GOOD" for d in data["days"])})
            return data

        for a in enabled:
            subjects = [{"subject_id":"person_1", "birth":{"civil_datetime":"1994-10-08T05:00:00+07:00"}}]
            if a["subject_count"] == 2:
                subjects.append({"subject_id":"person_2", "birth":{"civil_datetime":"1990-06-15T09:30:00+07:00"}})
            payload = {"activity":a["activity"], "subjects":subjects,
                       "date_range":{"start":"2026-10-08", "end":"2026-10-08"}, "include_details":True}
            result = call(payload,a["activity"]+"_jie_day")
            if a["activity"] in ("HOME_ENTRY", "LAND_BREAKING"):
                destination = ROOT/("examples/home_entry_date_response.json" if a["activity"] == "HOME_ENTRY" else "examples/day_only_date_response.json")
                destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
                destination.with_name(destination.name.replace("_response", "_request")).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
            if a["activity"] in ("MARRIAGE", "HOME_ENTRY", "BETROTHAL_NACAI", "LAND_BREAKING"):
                payload["date_range"] = {"start":"2026-10-12", "end":"2027-01-12"}
                payload["include_details"] = False
                result = call(payload,a["activity"]+"_93_days")
                assert len(result["days"]) == 93
                repeated = client.post("/api/v2/auspicious-dates/search",json=payload)
                repeated.raise_for_status()
                assert repeated.json() == result

        baseline_checks = 0
        if args.legacy_baseline:
            for case in json.loads(args.legacy_baseline.read_text()):
                result = call(case["request"],"legacy_"+case["request"]["activity"])
                for previous, current in zip(case["response"]["days"],result["days"]):
                    for key in previous:
                        value = current[key]
                        if key == "windows":
                            value = [{k:v for k,v in row.items() if k != "rule_warnings"} for row in value]
                        assert previous[key] == value, (key,case["request"]["activity"])
                baseline_checks += 1
        valid = {"activity":"LAND_BREAKING", "subjects":[{"subject_id":"a", "birth":{"civil_datetime":"1994-10-08T05:00:00+07:00"}}],
                 "date_range":{"start":"2030-12-31", "end":"2030-12-31"}}
        call(valid,"day_only_final_year_padding")
        for change in ({"allowed_hours":{"start":"06:00", "end":"22:00"}}, {"activity":"DEMOLITION"}):
            bad = deepcopy(valid);bad.update(change)
            assert client.post("/api/v2/auspicious-dates/search",json=bad).status_code == 422
        after = [client.get(path).json() for path in ("/api/v1/history", "/api/v1/maihoa/history")]
        assert before == after
    report = {"checked_at_utc":datetime.now(timezone.utc).isoformat(),
              "rules_version":registry["rules_version"], "activity_registry_version":registry["activity_registry_version"],
              "rules_sha256":hashlib.sha256((ROOT/"config/mvp2_date_rules.json").read_bytes()).hexdigest(),
              "corpus_sha256":json.loads((ROOT/"data/date_calendar/manifest.json").read_text())["sha256"],
              "enabled_activities":len(enabled), "groups":len(registry["groups"]),
              "legacy_baselines_compared":baseline_checks, "http_measurements":measurements,
              "checks":{"schemas":True,"day_only_no_hour_filter_422":True,"deferred_category_422":True,
                        "deterministic_replay":True,"draw_and_maihoa_history_unchanged":True,"latency_targets_passed":True},
              "scope":"Existing localhost server with synthetic profiles; 18 activities, 93-day searches, boundaries and schemas. Timings include HTTP serialization/transfer; no load/P95 test or traditional predictive validation."}
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"groups":report["groups"], "enabled":len(enabled), "cases":len(measurements),
                      "legacy_baselines":baseline_checks, "max_http_seconds":max(m["http_seconds"] for m in measurements)},ensure_ascii=False))
    print(args.output)


if __name__ == "__main__":
    main()
