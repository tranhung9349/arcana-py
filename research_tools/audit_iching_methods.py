"""Read-only arithmetic/corpus research; does not cast a consultation or draw numbers.

Run from the project root with:
    .venv/bin/python -m research_tools.audit_iching_methods
"""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

from randomyst.maihoa import IchingRepository

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/research/iching_methods_audit.json"
INPUTS = (
    "research_tools/audit_iching_methods.py",
    "randomyst/maihoa.py", "randomyst/sampling.py", "randomyst/interpretation.py",
    "randomyst/time_engine.py", "config/mvp1_rules.json",
    "data/reference/open-iching/iching.json",
    "data/reference/open-iching/tuan.json",
    "data/reference/open-iching/xiang.json",
    "data/interpretation/iching_vi_draft.json",
)


def hashes():
    return {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in INPUTS}


def probability(value):
    return {"fraction": str(value), "percent": float(value * 100)}


def run():
    before = hashes()
    repository = IchingRepository()
    coin_counts = Counter(sum(coins) for coins in product((2, 3), repeat=3))
    coin_p = {value: Fraction(count, 8) for value, count in coin_counts.items()}
    moving_count_p = Counter()
    original_ids, pairs = set(), set()
    for values in product((6, 7, 8, 9), repeat=6):
        bits = tuple(value % 2 for value in values)
        moving = tuple(i for i, value in enumerate(values) if value in (6, 9))
        changed = tuple(bit ^ (i in moving) for i, bit in enumerate(bits))
        original = repository.by_bits[bits]["id"]
        target = repository.by_bits[changed]["id"]
        original_ids.add(original)
        pairs.add((original, target))
        p = Fraction(1)
        for value in values:
            p *= coin_p[value]
        moving_count_p[len(moving)] += p
    if len(original_ids) != 64 or len(pairs) != 4096 or sum(moving_count_p.values()) != 1:
        raise RuntimeError("Incomplete coin state space or probability mass")

    maihoa_states, maihoa_ids = set(), set()
    parity_mismatches = 0
    for year, month, day, hour in product(range(1, 13), range(1, 13), range(1, 31), range(1, 13)):
        result = repository.calculate({"Y": year, "M": month, "D": day, "H": hour})
        number, moving = result["original"]["hexagram_id"], result["moving_line"]
        maihoa_ids.add(number)
        maihoa_states.add((number, moving))
        parity_mismatches += result["lower"] % 2 != moving % 2

    fixtures = []
    # Classical narrative examples in Meihua Yishu, vol. 1. The stories do not
    # supply Gregorian instants, so these fixtures verify arithmetic, not time conversion.
    for name, variables, expected in (
        ("觀梅占", {"Y": 5, "M": 12, "D": 17, "H": 9}, (49, 1, 31, 44)),
        ("牡丹占", {"Y": 6, "M": 3, "D": 16, "H": 4}, (44, 5, 50, 1)),
    ):
        result = repository.calculate(variables)
        observed = (result["original"]["hexagram_id"], result["moving_line"],
                    result["display_hexagrams"]["changed"]["hexagram_id"],
                    result["display_hexagrams"]["mutual"]["hexagram_id"])
        fixtures.append({"source_section": name, "variables": variables,
                         "expected_original_moving_changed_mutual": list(expected),
                         "observed_original_moving_changed_mutual": list(observed),
                         "matches": observed == expected})
    if not all(fixture["matches"] for fixture in fixtures):
        raise RuntimeError("Classical arithmetic fixture mismatch")

    raw = json.loads((ROOT / "data/reference/open-iching/iching.json").read_text())
    extra = [{"hexagram_id": row["id"], "line_id": line["id"], "name": line["name"]}
             for row in raw for line in row["lines"] if line["id"] > 6]
    draft = json.loads((ROOT / "data/interpretation/iching_vi_draft.json").read_text())
    if hashes() != before:
        raise RuntimeError("Research inputs changed during audit")
    return {
        "research_date_utc7": "2026-10-24", "status": "RESEARCH_ONLY",
        "input_sha256": before,
        "scope": {
            "calendar_conversion_audited": False, "historical_prediction_tested": False,
            "consultation_created": False, "database_accessed": False,
            "runtime_or_rules_modified": False,
            "note": "Arithmetic/corpus coverage only; no evidence of predictive or financial accuracy.",
        },
        "coins": {
            "assumptions": "Three independent fair coins per line, six independent throws; faces worth 2 and 3.",
            "ordered_single_throw_outcomes": 8,
            "single_line_counts": {str(k): coin_counts[k] for k in sorted(coin_counts)},
            "line_probabilities": {str(k): probability(coin_p[k]) for k in sorted(coin_p)},
            "line_state_vectors": 4096, "original_hexagrams": len(original_ids),
            "original_changed_pairs": len(pairs),
            "moving_count_probabilities": {str(k): probability(moving_count_p[k]) for k in range(7)},
            "two_or_more_moving_probability": probability(sum(moving_count_p[k] for k in range(2, 7))),
            "expected_moving_count": str(sum(k * p for k, p in moving_count_p.items())),
        },
        "yarrow_conventional_probability_model": {
            "status": "DECLARED_COMPARISON_MODEL_NOT_A_STALK_SIMULATION",
            "weights_for_6_7_8_9": [1, 5, 7, 3], "denominator": 16,
            "assumptions": "Conventional idealized remainder model, not every physical splitting procedure.",
            "physical_division_algorithm_verified": False,
            "production_recommendation": "Do not label a coin simulation as yarrow; defer physical stalk simulation.",
        },
        "maihoa": {
            "core_version": "maihoa-ymdh-v1", "integer_input_tuples": 51840,
            "input_domain": "Y=1..12, M=1..12, D=1..30, H=1..12; not a sequence of real calendar dates.",
            "original_hexagrams": len(maihoa_ids),
            "distinct_original_moving_pairs": len(maihoa_states),
            "moving_positions_per_hexagram": sorted(set(Counter(n for n, _ in maihoa_states).values())),
            "parity_invariant": "lower_trigram_index % 2 == moving_line % 2",
            "parity_mismatches": parity_mismatches,
            "always_one_moving_line": True,
            "birth_or_question_text_is_an_input_to_core": False,
            "classical_arithmetic_fixtures": fixtures,
            "pure_hexagram_mutual_policy": {
                "runtime": "Always extract lines 2-3-4 and 3-4-5, including Qian/Kun.",
                "source_variant": "Meihua vol. 1 also states 乾坤無互，互其變卦; requires a separately versioned policy.",
            },
        },
        "corpus": {
            "hexagrams": len(raw), "ordinary_lines": sum(min(6, len(row["lines"])) for row in raw),
            "special_source_entries": extra,
            "vi_draft_line_lengths": sorted(set(len(row["lines"]) for row in draft["hexagrams"])),
            "vi_special_use_nine_six_display_supported": False,
            "current_explanation_accepts_one_moving_line_only": True,
        },
    }


if __name__ == "__main__":
    report = run()
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(OUTPUT), "coin_states": report["coins"]["line_state_vectors"],
                      "maihoa_states": report["maihoa"]["distinct_original_moving_pairs"],
                      "classical_fixtures_match": all(f["matches"] for f in report["maihoa"]["classical_arithmetic_fixtures"])},
                     ensure_ascii=False))
