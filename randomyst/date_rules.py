"""Explicit blocking and scoped rule matches; scores never undo a block."""
import hashlib
import json
from pathlib import Path

from .date_models import DateRules
from .bazi import STEM_ELEMENTS
from .time_engine import BRANCH_ELEMENTS
from .sampling import GENERATES, CONTROLS

ROOT = Path(__file__).resolve().parents[1]
TRIPLE_GROUPS = ({0, 4, 8}, {2, 6, 10}, {3, 7, 11}, {1, 5, 9})
SIX_PAIRS = ({0, 1}, {2, 11}, {3, 10}, {4, 9}, {5, 8}, {6, 7})


def relation(stem, branch):
    s, b = STEM_ELEMENTS[stem], BRANCH_ELEMENTS[branch]
    if s == b:
        return "SAME"
    if GENERATES[s] == b:
        return "STEM_GENERATES_BRANCH"
    if GENERATES[b] == s:
        return "BRANCH_GENERATES_STEM"
    return "STEM_CONTROLS_BRANCH" if CONTROLS[s] == b else "BRANCH_CONTROLS_STEM"


def activity_status(yi, ji, token):
    yes, no = token in yi, token in ji
    all_bad = "诸事不宜" in yi or "诸事不宜" in ji
    others_bad = any(x in yi or x in ji for x in ("馀事勿取", "余事勿取"))
    if yes and (no or all_bad):
        return "UNRESOLVED"
    if no or all_bad or (others_bad and not yes):
        return "AVOID"
    return "SUPPORTED" if yes else "NOT_LISTED"


class RuleEvaluator:
    def __init__(self):
        self.config = DateRules.model_validate_json((ROOT / "config/mvp2_date_rules.json").read_text())
        for source in self.config.sources:
            if hashlib.sha256((ROOT / source.path).read_bytes()).hexdigest() != source.sha256:
                raise RuntimeError("Nguồn bảng luật ngày không đúng hash: " + source.source_id)
        self.activities = {x.activity: x for x in self.config.activities}

    def evaluate(self, facts, activity):
        # Context tables explicitly use the candidate chart, never the birth chart.
        day, month, year = facts["zhis"][2], facts["zhis"][1], facts["zhis"][0]
        group = next(g for g in TRIPLE_GROUPS if day in g)
        triple = {day, month, year} == group
        pair = any({day, x} in SIX_PAIRS for x in (month, year)) or any(x != day and x in group for x in (month, year))
        table = self.config.month_tables
        values = {"calendar_class": facts["calendar_class"], "day_relation": relation(facts["gans"][2], day),
                  "ambient_support": "FULL" if triple else "PAIR" if pair else "NONE",
                  "year_clash": (day - year) % 12 == 6, "sat_chu": day == table.sat_chu[month],
                  "tho_tu": day == table.tho_tu[month], "nguyet_pha": day == table.nguyet_pha[month]}
        found, seen = [], set()
        for rule in self.config.rules:
            if not rule.enabled or activity not in rule.activity_scope:
                continue
            if rule.when.fact not in values:
                raise RuntimeError("Luật bật thiếu evaluator: " + rule.rule_id)
            if values[rule.when.fact] == rule.when.equals and rule.dedupe_group not in seen:
                seen.add(rule.dedupe_group)
                found.append({"rule_id": rule.rule_id, "effect": rule.effect, "points": rule.points,
                              "message": rule.message, "source_id": rule.source_id, "dedupe_group": rule.dedupe_group})
        return found, values
