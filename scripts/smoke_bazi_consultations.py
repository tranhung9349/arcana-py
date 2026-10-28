"""Live HTTP smoke with explicitly synthetic natal profiles; records immutable replay."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from randomyst.bazi_models import BaziResponse, BaziReadingSnapshot


def run(base="http://127.0.0.1:8765"):
    def call(path, payload=None):
        request = Request(base+path, data=json.dumps(payload).encode() if payload is not None else None,
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=20) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)
    paths = ["/api/v1/history", "/api/v1/maihoa/history", "/api/v1/coins/history"]
    before = [call(p)[1] for p in paths]
    p = {"request_id": str(uuid4()), "display_name": "Kiểm chứng HTTP · Bát Tự",
         "birth": {"civil_datetime": "2000-02-29T09:30:00+07:00"}, "topic": "STUDY", "question": ""}
    start = time.perf_counter()
    status, result = call("/api/v1/bazi/consultations", p)
    elapsed = time.perf_counter()-start
    assert status == 200, result
    BaziResponse.model_validate(result)
    path = "/api/v1/bazi/consultations/"+p["request_id"]
    assert call(path)[1] == result
    assert call("/api/v1/bazi/consultations", p)[1] == result
    assert call("/api/v1/bazi/consultations", {**p, "topic": "CAREER"})[0] == 409
    context = {"reading_id": str(uuid4()), "topic": "WEALTH", "question": "Ghi chú kiểm thử, không phải dữ liệu cá nhân."}
    status, reading = call(path+"/readings", context)
    assert status == 200, reading
    BaziReadingSnapshot.model_validate(reading)
    assert call(path+"/readings", context)[1] == reading
    assert call(path)[1] == result
    assert [call(u)[1] for u in paths] == before
    report = {"result": "PASS", "request_id": p["request_id"], "reading_id": context["reading_id"],
              "schema_version": result["schema_version"], "rules_version": result["rules_version"],
              "rules_sha256": result["rules_sha256"], "chart_sha256": reading["chart_sha256"],
              "findings": len(result["findings"]), "sections": len(result["reading"]["sections"]),
              "create_seconds": round(elapsed, 6), "same_uuid_replay": True,
              "changed_payload_409": True, "reread_keeps_chart": True, "original_snapshot_unchanged": True,
              "other_histories_unchanged": True, "model_called": result["model_called"]}
    target=ROOT/"docs/research/bazi_http_smoke.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv)>1 else "http://127.0.0.1:8765")
