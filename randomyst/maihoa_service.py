"""Source-bound time-based Mai Hoa consultations, no RNG and no number scoring."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

from .engine import EngineError
from .maihoa import TRIGRAMS
from .maihoa_models import MaiHoaResponse
from .sampling import CONTROLS, GENERATES
from .time_engine import beijing_clock, resolve_maihoa, solar_month

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/reference/maihoa"
BITS_TO_TRIGRAM = {row[2]: number for number, row in TRIGRAMS.items()}


def relation(body, other):
    if body == other:
        return "SAME"
    if GENERATES[other] == body:
        return "USE_GENERATES_BODY"
    if CONTROLS[body] == other:
        return "BODY_CONTROLS_USE"
    if GENERATES[body] == other:
        return "BODY_GENERATES_USE"
    return "USE_CONTROLS_BODY"


class MaiHoaRules:
    def __init__(self):
        raw = (ROOT / "config/maihoa_rules.json").read_bytes()
        self.config = json.loads(raw)
        compiled = json.loads((DIRECTORY / "compiled.json").read_text())
        manifest = json.loads((DIRECTORY / "manifest.json").read_text())
        if (compiled["rules_sha256"] != sha256(raw).hexdigest()
                or compiled["rules_version"] != self.config["rules_version"]
                or compiled["corpus_version"] != manifest["corpus_version"]
                or self.config["corpus_version"] != manifest["corpus_version"]):
            raise RuntimeError("Mai Hoa rules/corpus binding mismatch; rebuild explicitly")
        sections = {}
        sources = {}
        for source in manifest["files"]:
            data = (DIRECTORY / source["path"]).read_bytes()
            if sha256(data).hexdigest() != source["sha256"]:
                raise RuntimeError("Mai Hoa source checksum mismatch")
            volume = int(source["path"].split("_")[1].split(".")[0])
            sources[volume] = source
            parts = re.split(r"(?m)^={2,5}\s*(.*?)\s*={2,5}\s*$", data.decode())
            for heading, body in zip(parts[1::2], parts[2::2]):
                sections[(volume, heading)] = "\n".join(line.strip() for line in body.strip().splitlines())
        if set(compiled["evidence"]) != set(self.config["evidence"]):
            raise RuntimeError("Mai Hoa evidence registry mismatch")
        for key, entry in compiled["evidence"].items():
            declared = self.config["evidence"][key]
            section = sections[(entry["volume"], entry["section"])]
            if (entry["source"] != sources[entry["volume"]]
                    or entry["volume"] != declared["volume"] or entry["section"] != declared["section"]
                    or entry["text"] != declared["quote"] or entry["text"] not in section
                    or sha256(entry["text"].encode()).hexdigest() != entry["text_sha256"]
                    or sha256(section.encode()).hexdigest() != entry["section_sha256"]):
                raise RuntimeError("Mai Hoa evidence not bound to the pinned text: " + key)
        self.evidence = compiled["evidence"]
        for topic in self.config["topics"].values():
            for entry in topic["relations"].values():
                evidence = self.evidence[entry["evidence_id"]]
                if entry["quote"] != evidence["text"] or topic["section"] != evidence["section"]:
                    raise RuntimeError("Mai Hoa topic/evidence binding mismatch")
        for entry in self.config["auxiliary_relations"].values():
            if entry["quote"] != self.evidence[entry["evidence_id"]]["text"]:
                raise RuntimeError("Mai Hoa auxiliary/evidence binding mismatch")
        self.sha256 = sha256(raw).hexdigest()

    def overview(self):
        return {"rules_version": self.config["rules_version"], "core_version": self.config["core_version"],
                "corpus_version": self.config["corpus_version"], "rules_sha256": self.sha256,
                "calendar_policy": self.config["calendar_policy"],
                "topics": [{"id": key, "name": row["name"]} for key, row in self.config["topics"].items()],
                "deferred_features": self.config["deferred_features"]}


class MaiHoaService:
    def __init__(self, explanations, rules=None):
        self.explanations = explanations
        self.iching = explanations.iching
        self.rules = rules or MaiHoaRules()

    def interpret_chart(self, core, month, topic="GENERAL"):
        """Interpret an existing chart; no calendar calculation, RNG or storage."""
        branch = month["month_branch_index"]
        # Product convention: a named earth month is more specific than the season.
        period = "EARTH_MONTH" if branch in (1, 4, 7, 10) else (
            "SPRING" if branch in (2, 3) else "SUMMER" if branch in (5, 6)
            else "AUTUMN" if branch in (8, 9) else "WINTER")
        config = self.rules.config
        upper_body = core["moving_line"] <= 3
        body_position = "UPPER" if upper_body else "LOWER"
        use_position = "LOWER" if upper_body else "UPPER"

        def trigram(number, position):
            name, element, _ = TRIGRAMS[number]
            strength = ("STRONG" if element == config["strength"]["strong"][period]
                        else "WEAK" if element == config["strength"]["weak"][period] else "NOT_SPECIFIED")
            return {"trigram": number, "name": name, "element": element, "position": position, "strength": strength}

        def half(hexagram, position):
            if hexagram is None:
                return None
            bits = hexagram["lines_bottom_to_top"]
            return trigram(BITS_TO_TRIGRAM[tuple(bits[3:] if position == "UPPER" else bits[:3])], position)

        for role, position in (("the", body_position), ("dung", use_position)):
            expected = half(core["original"], position)
            if any(core[role][key] != expected[key] for key in ("trigram", "name", "element")):
                raise ValueError("Saved body/use does not agree with the original chart")
        chart = {key: core[key] for key in ("core_version", "variables", "upper", "lower", "moving_line", "original")}
        chart["mutual_basis"] = core.get("mutual_basis", "ORIGINAL")
        chart.update(mutual=core["display_hexagrams"]["mutual"], changed=core["display_hexagrams"]["changed"],
                     the=trigram(core["the"]["trigram"], body_position),
                     dung=trigram(core["dung"]["trigram"], use_position))
        chart.update(mutual_body=half(chart["mutual"], body_position), mutual_use=half(chart["mutual"], use_position),
                     changed_use=half(chart["changed"], use_position))
        evidence_ids = {"TRIGRAMS", "ELEMENTS", "GENERATES", "STRONG", "WEAK", "MOD8", "MOD6", "TIME",
                        "BODY_USE", "MUTUAL", "PHASES", "FINAL", "STRENGTH", "CONTEXT", "TEXT_METHOD", "SYNTHESIS"}
        if chart["mutual_basis"] == "CHANGED_FOR_PURE":
            evidence_ids.add("MUTUAL_PURE")
        findings = []
        for phase, title, other in (
            ("BEGINNING", "Dụng · việc đang hỏi", chart["dung"]),
            ("MIDDLE_BODY", "Thể hỗ · diễn tiến trung gian", chart["mutual_body"]),
            ("MIDDLE_USE", "Dụng hỗ · diễn tiến trung gian", chart["mutual_use"]),
            ("ENDING", "Dụng biến · chiều cuối việc", chart["changed_use"]),
        ):
            if other is None:
                continue
            code = relation(chart["the"]["element"], other["element"])
            phase_topic = topic if phase == "BEGINNING" else "AUX"
            row = config["topics"][phase_topic]["relations"][code] if phase == "BEGINNING" else config["auxiliary_relations"][code]
            evidence_ids.add(row["evidence_id"])
            refs = [row["evidence_id"]] + (["PHASES"] if phase != "BEGINNING" else [])
            findings.append({"rule_id": f"MH.{phase_topic}.{code}", "phase": phase, "title": title,
                             "relation": code, "indication": row["indication"], "text_vi": row["text_vi"],
                             "translation_status": "AI_DRAFT_UNREVIEWED", "evidence_refs": refs})
        signs = {finding["indication"] for finding in findings}
        pattern = "MIXED_INDICATIONS" if len(signs) > 1 else (
            "FAVOURABLE_RELATIONS" if "FAVOURABLE" in signs else "CAUTION_RELATIONS")
        summary_text = {"MIXED_INDICATIONS": "Các quan hệ trong quẻ có cả chiều thuận và trở ngại.",
                        "FAVOURABLE_RELATIONS": "Các quan hệ trong quẻ đang có chiều thuận.",
                        "CAUTION_RELATIONS": "Các quan hệ trong quẻ đang có chiều trở ngại."}[pattern]
        beginning, ending = findings[0]["indication"], findings[-1]["indication"]
        sequence = {("FAVOURABLE", "CAUTION"): "Đầu thuận, cuối có trở ngại theo quan hệ Dụng và Dụng biến.",
                    ("CAUTION", "FAVOURABLE"): "Đầu có trở ngại, cuối có chiều thuận theo quan hệ Dụng và Dụng biến.",
                    ("FAVOURABLE", "FAVOURABLE"): "Quan hệ đầu và cuối đều có chiều thuận; vẫn cần xem phần trung gian và vượng suy.",
                    ("CAUTION", "CAUTION"): "Quan hệ đầu và cuối đều có trở ngại; vẫn cần xem các dấu hiệu hỗ trợ khác."}[(beginning, ending)]
        if chart["changed_use"] is None:
            sequence = "Phiên đã lưu thiếu quẻ biến, chưa luận chiều cuối của việc."
        warnings = []
        if chart["the"]["strength"] == "WEAK":
            warnings.append({"code": "BODY_WEAK", "message": "Thể thuộc nhóm suy theo thời khí đang xét; không chỉ dựa vào quan hệ sinh để kết luận thuận."})
        for key in ("dung", "mutual_body", "mutual_use", "changed_use"):
            t = chart[key]
            if t is not None and relation(chart["the"]["element"], t["element"]) == "USE_CONTROLS_BODY" and t["strength"] == "STRONG":
                warnings.append({"code": "STRONG_CONTROLLING_TRIGRAM", "role": key,
                                 "message": f"Quái {t['name']} khắc Thể và thuộc nhóm vượng; cần xét kỹ dấu hiệu trở ngại này."})
        return {
            "chart": chart, "findings": findings,
            "season": {**month, "period": period, "strong_element": config["strength"]["strong"][period],
                       "weak_element": config["strength"]["weak"][period], "provenance": "PRODUCT_CONVENTION"},
            "summary": {"pattern": pattern, "text": summary_text, "sequence": sequence,
                        "provenance": "PRODUCT_DERIVED", "is_full_divination_verdict": False,
                        "priority": ["BEGINNING", "MIDDLE_BODY", "MIDDLE_USE", "ENDING"]},
            "evidence": [deepcopy(self.rules.evidence[key]) for key in sorted(evidence_ids)],
            "warnings": warnings,
        }

    def consult(self, request, received_at=None):
        received_at = received_at or datetime.now(timezone.utc)
        instant = request.casting.clicked_at if request.casting.mode == "CURRENT" else request.casting.custom_timestamp
        calendar = resolve_maihoa(instant)
        clock = beijing_clock(instant, request.casting.clock_uncertainty_seconds)
        month = solar_month(instant)
        config = self.rules.config
        core = self.iching.calculate_source(calendar["maihoa_inputs"])
        reading = self.interpret_chart(core, month, request.topic)
        chart, findings, warnings = reading["chart"], reading["findings"], reading["warnings"]
        if clock["boundary"]["status"] == "BOUNDARY":
            warnings.append({"code": "CLOCK_BOUNDARY", "message": "Sai số giờ đã nhập chạm ranh giờ/ngày; quẻ ở phía ranh còn lại có thể khác."})
        if request.casting.mode == "CURRENT" and abs((received_at - instant).total_seconds()) > 30:
            warnings.append({"code": "CLIENT_CLOCK_SKEW", "message": "Giờ bấm nút lệch giờ nhận trên 30 giây; giữ nguyên mốc đã gửi để kiểm chứng."})
        result = {
            "schema_version": "maihoa-consultation-v1", "request_id": str(request.request_id),
            "created_at": received_at.isoformat(), "rules_version": config["rules_version"],
            "corpus_version": config["corpus_version"], "question": request.question,
            "topic": request.topic, "topic_name": config["topics"][request.topic]["name"],
            "calendar": {**calendar, "clock": clock}, "calendar_policy": config["calendar_policy"],
            "season": reading["season"], "chart": chart, "findings": findings,
            "summary": reading["summary"], "evidence": reading["evidence"],
            "texts": {key: self.explanations.hexagram(chart[key]["hexagram_id"], core["moving_line"] if key == "original" else None)
                      for key in ("original", "mutual", "changed")},
            "warnings": warnings, "automated_scope": "INTERNAL_TRIGRAM_RELATIONS",
            "interpretation_review_status": "AI_DRAFT_UNREVIEWED",
            "limitations": [
                "Phần tự động xét Thể–Dụng, Thể hỗ/Dụng hỗ, Dụng biến và vượng suy; chưa thay thế người luận toàn bộ ngữ cảnh.",
                "Ngoại ứng, động tĩnh thực tế và cách ứng kỳ cụ thể chưa được tự động suy đoán; không trả ngày có tiền hay số tiền dự kiến.",
                "Quẻ/hào từ được trình bày để đối chiếu, không chấm cát hung bằng cách dò từ khóa trong kinh văn.",
                "Lời Việt là bản nháp AI chưa hiệu đính; nguồn Mai Hoa là bản chép điện tử có thể có dị văn, không phải bản khảo đính.",
                "Múi giờ, tháng nhuận và cách xác định thời khí là quy ước phiên bản đã ghi; cùng đầu vào Y/M/D/H sẽ cùng quẻ.",
                "Các chỉ báo phản ánh phép luận truyền thống, không phải xác suất thành công hoặc lợi nhuận.",
            ],
        }
        return MaiHoaResponse.model_validate(result).model_dump(mode="json")


class MaiHoaStore:
    """Independent table; never alters number draw records or their history."""
    def __init__(self, store):
        self.store = store
        with self.store.connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS maihoa_sessions (request_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, response TEXT NOT NULL)")

    def execute(self, request, builder):
        payload = json.dumps(request.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = sha256(payload.encode()).hexdigest()
        with self.store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT payload_hash, response FROM maihoa_sessions WHERE request_id=?", (str(request.request_id),)).fetchone()
            if row:
                if row[0] != digest:
                    raise EngineError("MAIHOA_REQUEST_CONFLICT", "Mã phiên đã dùng cho câu hỏi khác. Hãy lập phiên mới.", 409)
                return json.loads(row[1])
            result = builder()
            connection.execute("INSERT INTO maihoa_sessions VALUES (?, ?, ?, ?)",
                               (str(request.request_id), digest, result["created_at"], json.dumps(result, ensure_ascii=False)))
            return result

    def get(self, request_id):
        with self.store.connect() as connection:
            row = connection.execute("SELECT response FROM maihoa_sessions WHERE request_id=?", (str(request_id),)).fetchone()
        if row is None:
            raise EngineError("MAIHOA_NOT_FOUND", "Không tìm thấy phiên luận Mai Hoa.", 404)
        return json.loads(row[0])

    def history(self, limit=10):
        with self.store.connect() as connection:
            rows = connection.execute("SELECT response FROM maihoa_sessions ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
        return [{key: data[key] for key in ("request_id", "question", "topic_name", "created_at", "rules_version")}
                for data in (json.loads(row[0]) for row in rows)]
