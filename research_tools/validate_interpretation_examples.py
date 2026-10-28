"""Validate schemas/examples and reject representative contract violations.

Requires jsonschema==4.25.1 in a development environment; not a runtime dependency
of the calendar adapter or exponential experiment.
"""

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
FACT_REFERENCES = {
    "facts:bazi.primary_useful_element", "facts:maihoa.original", "facts:maihoa.moving_line",
    "facts:maihoa.the_dung_relation", "facts:number_result", "facts:time_context",
}


def main():
    validators = {}
    examples = {}
    for kind in ("context", "response"):
        schema = json.loads((ROOT / f"schemas/interpretation_{kind}.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        validators[kind] = Draft202012Validator(schema)
        examples[kind] = json.loads((ROOT / f"schemas/examples/interpretation_{kind}.example.json").read_text())
        validators[kind].validate(examples[kind])
    context, response = examples["context"], examples["response"]
    evidence_ids = {item["evidence_id"] for item in context["evidence"]}
    assert len(evidence_ids) == len(context["evidence"])
    assert response["context_id"] == context["context_id"]
    assert all(row["evidence_id"] in evidence_ids for row in response["translations"])
    for row in [response["summary"], *response["interpretations"]]:
        assert all(ref in evidence_ids | FACT_REFERENCES for ref in row["references"])

    # Cross-field sanity for this known fixture, beyond JSON Schema shape checks.
    maihoa = context["computed_facts"]["maihoa"]
    v = maihoa["variables"]
    upper_sum = v["Y"] + v["M"] + v["D"]
    lower_sum = upper_sum + v["H"]
    assert maihoa["upper"] == (upper_sum - 1) % 8 + 1
    assert maihoa["lower"] == (lower_sum - 1) % 8 + 1
    assert maihoa["moving_line"] == (lower_sum - 1) % 6 + 1
    lines = maihoa["original"]["lines_bottom_to_top"]
    assert context["display_hexagrams"]["mutual"]["lines_bottom_to_top"] == lines[1:4] + lines[2:5]
    changed = list(lines)
    changed[maihoa["moving_line"] - 1] ^= 1
    assert context["display_hexagrams"]["changed"]["lines_bottom_to_top"] == changed

    invalid = []
    altered = copy.deepcopy(context)
    altered["display_hexagrams"]["affects_generation"] = True
    invalid.append(("context", altered))
    altered = copy.deepcopy(context)
    altered["computed_facts"]["number_result"]["remediation"]["quota_max"] = 5
    invalid.append(("context", altered))
    altered = copy.deepcopy(context)
    altered["computed_facts"]["maihoa"]["variables"]["seconds"] = 42
    invalid.append(("context", altered))
    altered = copy.deepcopy(context)
    altered["computed_facts"]["number_result"]["numbers"] = ["01"] * 6
    invalid.append(("context", altered))
    altered = copy.deepcopy(response)
    altered["translations"][0]["label"] = "SOURCE_ORIGINAL"
    invalid.append(("response", altered))
    altered = copy.deepcopy(response)
    altered["numbers"] = ["01", "02", "03", "04", "05", "06"]
    invalid.append(("response", altered))
    for kind, bad_example in invalid:
        try:
            validators[kind].validate(bad_example)
        except ValidationError:
            continue
        raise AssertionError("Invalid fixture unexpectedly accepted")
    print(json.dumps({"schema_definitions_valid": 2, "valid_examples": 2,
                      "rejected_invalid_examples": len(invalid), "fixture_references_and_cross_fields_valid": True}))


if __name__ == "__main__":
    main()
