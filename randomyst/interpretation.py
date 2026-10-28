"""Display-only source retrieval plus explicitly labelled Vietnamese AI drafts.

This module consumes an already saved draw. It never calls the number engine,
changes a chart, samples numbers, or invokes an external model.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .maihoa import COMMIT, IchingRepository
from .bazi import SOURCE_COMMIT
from .bazi_reading import BaziInterpreter
from .maihoa_reading import DrawMaiHoaInterpreter
from .maihoa_service import MaiHoaService

ROOT = Path(__file__).resolve().parents[1]


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


class ExplanationRepository:
    def __init__(self, iching=None):
        self.iching = iching or IchingRepository()
        self.by_id = {r["id"]: r for r in self.iching.by_bits.values()}
        self.draft = json.loads((ROOT / "data/interpretation/iching_vi_draft.json").read_text())
        self.bazi = json.loads((ROOT / "data/interpretation/tinix_vi.json").read_text())
        if self.draft["source_commit"] != COMMIT or self.bazi["source_commit"] != SOURCE_COMMIT:
            raise RuntimeError("Explanation corpus belongs to another source commit")
        self.vi = {r["id"]: r for r in self.draft["hexagrams"]}
        if len(self.draft["hexagrams"]) != 64 or set(self.vi) != set(self.by_id):
            raise RuntimeError("Expected 64 unique Vietnamese hexagram records")
        for number, row in self.by_id.items():
            vi = self.vi[number]
            expected = {"judgment": digest(row["scripture"]),
                        "lines": [digest(next(l["scripture"] for l in row["lines"] if l["id"] == i))
                                  for i in range(1, 7)]}
            if vi["source_text_sha256"] != expected or len(vi["lines"]) != 6:
                raise RuntimeError("Vietnamese draft/source text binding mismatch")
        manifest = json.loads((ROOT / "data/reference/manifest.json").read_text())
        hashes = {r["path"]: r["sha256"] for r in manifest["files"]}
        for table, upstream_path in self.bazi["source_paths"].items():
            local_path = "tinix-bazi/" + upstream_path.removeprefix("backendjs/src/bazi/")
            raw = (ROOT / "data/reference" / local_path).read_bytes()
            if hashlib.sha256(raw).hexdigest() != hashes[local_path] or hashes[local_path] != self.bazi["source_sha256"][table]:
                raise RuntimeError("Bazi explanation/source checksum mismatch")
        if len(self.bazi["stems"]) != 10:
            raise RuntimeError("Expected ten upstream day-stem interpretations")
        self.bazi_interpreter = BaziInterpreter()
        self.maihoa_service = MaiHoaService(self)
        self.maihoa_interpreter = DrawMaiHoaInterpreter(self.maihoa_service)

    @staticmethod
    def source(repository, commit, path, key):
        return {"repository": repository, "commit": commit, "path": path, "key": key,
                "url": f"https://github.com/{repository}/blob/{commit}/{path}"}

    def hexagram(self, number, moving_line=None):
        row, vi = self.by_id[number], self.vi[number]
        cards, gaps = [], []
        def add(kind, title, text, path, key, translation=None):
            evidence_id = key + "__" + kind.lower()
            cards.append({"evidence_id": evidence_id, "title": title, "text_type": kind,
                          "language": "zh", "label": "SOURCE_ORIGINAL", "text": text,
                          "source": self.source("john-walks-slow/open-iching", COMMIT, path, key),
                          "translation": ({"label": "AI_TRANSLATION", "language": "vi", "text": translation,
                                           "review_status": "UNREVIEWED", "version": self.draft["version"],
                                           "references": [evidence_id], "source_text_sha256": digest(text)}
                                          if translation is not None else None)})
        key = f"iching__{number}"
        add("HEXAGRAM_TEXT", "Quẻ từ", row["scripture"], "iching/iching.json", key, vi["judgment"])
        if moving_line is not None:
            if type(moving_line) is not int or not 1 <= moving_line <= 6:
                raise ValueError("Invalid moving-line position")
            line = next(l for l in row["lines"] if l["id"] == moving_line)
            add("LINE_TEXT", f"Hào {moving_line} động · {line['name']}", line["scripture"],
                "iching/iching.json", f"{key}_{moving_line}", vi["lines"][moving_line - 1])
        for kind, title, table, path in [
            ("TUAN_COMMENTARY", "Thoán truyện", self.iching.tuan, "ichuan/tuan.json"),
            ("XIANG_COMMENTARY", "Đại Tượng truyện", self.iching.xiang, "ichuan/xiang.json"),
        ]:
            if key in table:
                add(kind, title, table[key], path, key)
            else:
                gaps.append({"text_type": kind, "message": f"Nguồn đã khóa chưa có {title} của quẻ #{number}.",
                             "source": self.source("john-walks-slow/open-iching", COMMIT, path, key)})
        line_key = f"{key}_{moving_line}"
        if moving_line is not None and line_key in self.iching.xiang:
            add("LINE_XIANG_COMMENTARY", f"Tiểu Tượng · hào {moving_line}", self.iching.xiang[line_key],
                "ichuan/xiang.json", line_key)
        return {"hexagram_id": number, "name_zh": row["name"], "name_vi": vi["name_vi"],
                "symbol": row["symbol"], "moving_line": moving_line,
                "overview": {"label": "AI_INTERPRETATION", "language": "vi", "text": vi["overview"],
                             "review_status": "UNREVIEWED", "references": [cards[0]["evidence_id"]]},
                "cards": cards, "source_gaps": gaps}

    def natal(self, bazi):
        natal = bazi["natal"]
        day = natal["pillars"][2]
        stem = day["stem_zh"]
        branch = natal["zhis"][1]
        season = "Spring" if branch in (2, 3, 4) else "Summer" if branch in (5, 6, 7) else "Autumn" if branch in (8, 9, 10) else "Winter"
        seasons_vi = {"Spring": "Xuân", "Summer": "Hạ", "Autumn": "Thu", "Winter": "Đông"}
        cards, gaps = [], []
        def add(table, key, kind, title, text):
            cards.append({"evidence_id": "tinix__" + key, "title": title, "text_type": kind,
                          "language": "vi", "label": "SOURCE_ORIGINAL", "text": text,
                          "source": self.source("vhphuoc1102/tinix-bazi", SOURCE_COMMIT,
                                               self.bazi["source_paths"][table], key), "translation": None})
        essence = self.bazi["stems"].get(stem)
        if essence:
            base = f"STEM_ESSENCE.{stem}"
            add("stems", base + ".verse", "BAZI_HAN_VIET_VERSE", f"Lời dẫn Hán Việt · Nhật Chủ {day['stem']}", essence["verse"])
            add("stems", base + ".detail", "BAZI_DAY_STEM", "Nghĩa Nhật Chủ theo tinix-bazi", essence["detail"])
            add("stems", base + ".seasonal." + season, "BAZI_BIRTH_SEASON",
                "Theo mùa sinh " + seasons_vi[season], essence["seasonal"][season])
        structure = self.bazi["structures"].get(bazi["structure"])
        if structure:
            for key, title in [("desc", "Ý nghĩa cách cục"), ("strengths", "Điểm mạnh theo nguồn"),
                               ("weaknesses", "Điểm cần lưu ý theo nguồn"), ("success_key", "Nguyên tắc phối hợp theo nguồn")]:
                add("structures", f"STRUCTURE_ANALYSIS.{bazi['structure']}.{key}", "BAZI_STRUCTURE",
                    title, structure[key])
        else:
            # Preserve the engine's pattern exactly; never invent or substitute a lookup key.
            gaps.append({"message": f"tinix-bazi chưa có mục diễn giải khớp chính xác '{bazi['structure']}'."})
        return {"day_master": day["stem"] + " (" + day["stem_zh"] + ")",
                "structure": bazi["structure"], "strength": bazi["strength"],
                "primary_used": bazi["primary_used"], "primary_calculated": bazi["primary_dung_than"],
                "overridden": bazi["overridden"], "dung_than": list(bazi["dung_than"]),
                "hy_than": list(bazi["hy_than"]), "ky_than": list(bazi["ky_than"]),
                "birth_season": seasons_vi[season], "cards": cards, "source_gaps": gaps}

    def explain(self, draw):
        trace, m = draw["trace"], draw["trace"]["maihoa"]
        row = self.by_id[m["original"]["hexagram_id"]]
        if row["array"] != m["original"]["lines_bottom_to_top"]:
            raise ValueError("Saved hexagram ID and lines do not agree")
        original = self.hexagram(row["id"], m["moving_line"])
        display = {}
        for kind in ("mutual", "changed"):
            saved = m["display_hexagrams"].get(kind)
            if saved and self.by_id[saved["hexagram_id"]]["array"] != saved["lines_bottom_to_top"]:
                raise ValueError("Saved auxiliary hexagram ID and lines do not agree")
            display[kind] = self.hexagram(saved["hexagram_id"]) if saved else None
        natal = self.natal(trace["bazi"])
        return {"schema_version": "source-explanation-v2", "context_id": draw["request_id"],
                "rules_version": draw["rules_version"], "corpus_version": self.draft["version"],
                "model_called": False, "affects_generation": False, "affects_evaluation": False,
                "original": original, "bazi": natal, "display_hexagrams": display,
                "readings": {"bazi": self.bazi_interpreter.interpret(draw, natal),
                             "maihoa": self.maihoa_interpreter.interpret(draw, original)},
                "relation": {"label": "ENGINE_EXPLANATION", "the": deepcopy(m["the"]), "dung": deepcopy(m["dung"]),
                             "state": m["state"], "remediation_target": trace["remediation"]["target"]},
                "limitations": [
                    "Nghĩa quẻ và hào tiếng Việt là bản nháp do AI soạn từ open-iching, chưa được chuyên gia hiệu đính.",
                    "Lời giải Bát Tự tiếng Việt được trích từ tinix-bazi; lời dẫn Hán Việt của repo không phải bản cổ văn Hán được khảo chứng.",
                    "Thoán truyện và Tượng truyện đang hiển thị nguyên văn Hán. Các phân loại lý số là quy ước của hệ thống, không phải dự báo chắc chắn.",
                ],
                "disclaimer": "Điểm bộ số là mức phù hợp theo quy tắc nội bộ, không phải xác suất trúng thưởng hoặc bằng chứng cải vận."}
