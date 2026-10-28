"""Audit a research-only major-event catalog against the pinned raw calendar.

Does not load proposed categories into the runtime, score dates, or certify a
traditional method. Reuses the historical audit's status/count definitions.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from randomyst.date_calendar import DateCalendar
from research_tools.audit_activity_categories import summarize

CATALOG = ROOT / "docs/research/mvp2_major_event_catalog.json"
OUTPUT = ROOT / "docs/research/mvp2_major_event_coverage.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit():
    raw = CATALOG.read_bytes()
    catalog = json.loads(raw)
    runtime = json.loads((ROOT / "config/mvp2_date_rules.json").read_text())
    # The proposal records the three activities live at research time; v2 can
    # enable more without rewriting that historical observation.
    live = {item["activity"]: item for item in runtime["activities"]
            if item.get("rule_profile", "LEGACY_V1") == "LEGACY_V1"}
    groups = {item["group_id"] for item in catalog["groups"]}
    sources = {item["source_id"] for item in catalog["sources"]}
    items = catalog["activities"]
    require(catalog["runtime_loaded"] is False, "Research catalog must not claim runtime activation")
    require(len(groups) == len(catalog["groups"]), "Duplicate group")
    require(len(sources) == len(catalog["sources"]), "Duplicate source")
    require(len({item["activity"] for item in items}) == len(items), "Duplicate activity")
    require({item["activity"] for item in items if item["runtime_enabled_as_of_research"]} == set(live), "Live catalog/runtime mismatch")
    calendar = DateCalendar()  # Verifies pinned provider/corpus hashes.
    days = sorted((key, row) for key, row in calendar.data["days"].items()
                  if "2024-01-01" <= key <= "2030-12-31")
    hours = [(f"{key}T{row['anchor_hour']:02}:00+08:00", row)
             for key, day in days for row in day["hours"]]
    require(len(days) == 2557 and len(hours) == 33241, "Unexpected corpus range")
    day_inventory = Counter(token for _, row in days for side in ("yi", "ji") for token in row[side])
    hour_inventory = Counter(token for _, row in hours for side in ("yi", "ji") for token in row[side])
    cache = {}

    def coverage(token):
        if token not in cache:
            cache[token] = {
                "token": token,
                "day": summarize(days, token),
                "hour": summarize(hours, token),
                "annual": {
                    str(year): {
                        "day": summarize([row for row in days if row[0].startswith(str(year))], token),
                        "hour": summarize([row for row in hours if row[0].startswith(str(year))], token),
                    } for year in range(2024, 2031)
                },
            }
        return cache[token]

    evidence = []
    for item in items:
        key = item["activity"]
        require(item["group_id"] in groups, f"Unknown group: {key}")
        require(set(item.get("related_group_ids", [])) <= groups, f"Unknown related group: {key}")
        require(set(item["source_ids"]) <= sources, f"Unknown source: {key}")
        require(bool(item["source_ids"]) and bool(item["event_anchor"]), f"Missing basis: {key}")
        require(item["phase"] in catalog["phases"], f"Unknown phase: {key}")
        require(item["tier"] in ("CORE", "CONTEXTUAL"), f"Unknown tier: {key}")
        require(len(item["subject_roles_proposed"]) in (1, 2), f"Review subject roles: {key}")
        day_token, hour_token = item["day_token"], item["hour_token"]
        require(day_token in day_inventory, f"Missing day token: {key}")
        if hour_token is not None:
            require(hour_token in hour_inventory, f"Missing hour token: {key}")
        day = coverage(day_token)["day"]
        hour = coverage(hour_token)["hour"] if hour_token else None
        mode = item["hour_mode_proposal"]
        if mode in ("DIRECT_YI_JI", "LEGACY_V1"):
            require(hour is not None and hour["yi_mentions"] > 0, f"No positive hour evidence: {key}")
        elif mode == "DAY_ONLY":
            require(hour is None or hour["yi_mentions"] == 0, f"Review DAY_ONLY choice: {key}")
            require(coverage(day_token)["hour"]["yi_mentions"] == 0, f"Direct positive hour token was overlooked: {key}")
        elif mode == "MAPPING_PENDING":
            require(hour is None and bool(item["hour_token_candidates"]), f"Pending mapping was activated: {key}")
        else:
            raise ValueError(f"Unknown hour mode: {key}")
        for candidate in item["hour_token_candidates"]:
            require(candidate in hour_inventory, f"Missing proposed hour token: {key}")
            coverage(candidate)
        if key in live:
            require(item["phase"] == "LIVE" and mode == "LEGACY_V1", f"Changed live policy: {key}")
            require(day_token == hour_token == live[key]["provider_token"], f"Changed live mapping: {key}")
            require(len(item["subject_roles_proposed"]) == live[key]["subject_count"], f"Changed live subjects: {key}")
        else:
            require(item["phase"] != "LIVE" and item["rule_profile_review"] == "REQUIRED", f"Unreviewed rule profile: {key}")
        evidence.append({
            "activity": key, "group_id": item["group_id"], "tier": item["tier"], "phase": item["phase"],
            "day_token": day_token, "day_yi_mentions": day["yi_mentions"],
            "day_ji_mentions": day["ji_mentions"], "day_unresolved": day["statuses"]["UNRESOLVED"],
            "hour_token": hour_token, "hour_yi_mentions": hour["yi_mentions"] if hour else None,
            "hour_ji_mentions": hour["ji_mentions"] if hour else None,
            "hour_mode_proposal": mode, "unreviewed_hour_token_candidates": item["hour_token_candidates"],
        })
    for domain in catalog["specialist_domains"]:
        for token in domain["provider_tokens_to_research"]:
            coverage(token)
    # Confirm old shared-token counts still agree; preserve the 14/10 artifact.
    previous = json.loads((ROOT / "docs/research/mvp2_activity_token_coverage.json").read_text())
    compared = 0
    for item in previous["candidates"]:
        for field in ("day", "hour"):
            token = item[f"{field}_token"]
            if token in cache:
                require(coverage(token)[field] == item[field], f"Historical count mismatch: {token}/{field}")
                compared += 1
    return {
        "schema_version": "mvp2-major-event-coverage-v1",
        "research_date_utc7": catalog["research_date_utc7"],
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "corpus_gzip_sha256": calendar.manifest["sha256"],
        "provider": "lunar-python==1.4.8", "runtime_rules_version": runtime["rules_version"],
        "basis": "Beijing civil dates 2024-01-01..2030-12-31; 13 hour anchors/day; excludes 2031 padding. Not Vietnamese civil-day frequencies or personalized GOOD results.",
        "day_count": len(days), "hour_anchor_count": len(hours),
        "inventory": {"day_token_count": len(day_inventory), "hour_token_count": len(hour_inventory)},
        "group_count": len(groups), "core_count": sum(item["tier"] == "CORE" for item in items),
        "contextual_count": sum(item["tier"] == "CONTEXTUAL" for item in items),
        "core_phases": dict(Counter(item["phase"] for item in items if item["tier"] == "CORE")),
        "historical_coverage_comparisons": compared,
        "meaning": "Counts include direct Yi/Ji mentions and existing activity_status with global taboos; NOT_LISTED is not missing data. No scores, demand estimates, tradition certification, runtime changes or activated candidate mappings.",
        "activities": evidence,
        "token_coverage": {token: cache[token] for token in sorted(cache)},
    }


if __name__ == "__main__":
    result = audit()
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in (
        "group_count", "core_count", "contextual_count", "core_phases", "day_count",
        "hour_anchor_count", "historical_coverage_comparisons")}, ensure_ascii=False))
    print(f"Written: {OUTPUT}")
