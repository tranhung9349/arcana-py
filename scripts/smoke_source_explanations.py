"""Read-only smoke check against the running localhost MVP."""
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from randomyst.models import SourceExplanation


def get(path):
    with urllib.request.urlopen("http://127.0.0.1:8765" + path, timeout=15) as response:
        return json.load(response)


def main():
    saved = json.loads((ROOT / "examples/draw_response.json").read_text())
    before = get("/api/v1/history")
    explanation = get("/api/v1/interpretation/" + saved["request_id"])
    SourceExplanation.model_validate(explanation)
    assert explanation['schema_version']=='source-explanation-v2'
    assert explanation['readings']['bazi']['module']=='BAZI'
    assert explanation['readings']['maihoa']['module']=='MAIHOA'
    assert explanation['readings']['maihoa']['facts']['chart']['original']==saved['trace']['maihoa']['original']
    assert explanation['readings']['bazi']['facts']['natal']==saved['trace']['bazi']['natal']
    assert explanation == get("/api/v1/interpretation/" + saved["request_id"])
    assert get("/api/v1/draw/" + saved["request_id"]) == saved
    assert get("/api/v1/history") == before
    (ROOT / "examples/source_explanation.json").write_text(json.dumps(explanation, ensure_ascii=False, indent=2) + "\n")
    report = {"context_id": explanation["context_id"], "hexagram": explanation["original"]["name_vi"],
              "moving_line": explanation["original"]["moving_line"],
              "source_cards": len(explanation["original"]["cards"]), "bazi_cards": len(explanation["bazi"]["cards"]),
              "saved_draw_preserved": True, "history_unchanged": True, "same_read_same_explanation": True,
              "schema_valid": True, "model_called": explanation["model_called"],
              "schema_version":explanation['schema_version'],
              "module_versions":{key:value['version'] for key,value in explanation['readings'].items()},
              "bazi_sections":len(explanation['readings']['bazi']['sections']),
              "maihoa_sections":len(explanation['readings']['maihoa']['sections']),
              "saved_birth_and_casting_charts_preserved":True}
    (ROOT / "docs/research/draw_deep_reading_http_smoke.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
