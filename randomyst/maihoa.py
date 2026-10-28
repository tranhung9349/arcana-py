import hashlib
import json
from pathlib import Path

from .sampling import state_of

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "4c5f00f8cb62c6e0d2471243d28150b473ef592f"
# All arrays are bottom-to-top. Lower trigram comes first in a hexagram.
TRIGRAMS = {
    1: ("Càn", "Kim", (1,1,1)), 2: ("Đoài", "Kim", (1,1,0)),
    3: ("Ly", "Hỏa", (1,0,1)), 4: ("Chấn", "Mộc", (1,0,0)),
    5: ("Tốn", "Mộc", (0,1,1)), 6: ("Khảm", "Thủy", (0,1,0)),
    7: ("Cấn", "Thổ", (0,0,1)), 8: ("Khôn", "Thổ", (0,0,0)),
}


class IchingRepository:
    def __init__(self):
        directory = ROOT / "data/reference/open-iching"
        manifest = json.loads((ROOT / "data/reference/manifest.json").read_text())
        for entry in manifest["files"]:
            if entry["path"].startswith("open-iching/"):
                path = ROOT / "data/reference" / entry["path"]
                if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                    raise RuntimeError("I Ching source checksum mismatch")
        rows = json.loads((directory / "iching.json").read_text())
        self.by_bits = {tuple(row["array"]): row for row in rows}
        if len(rows) != 64 or len(self.by_bits) != 64 or len({r["id"] for r in rows}) != 64:
            raise RuntimeError("Expected 64 unique hexagrams")
        for row in rows:
            lines = {line["id"]: line for line in row["lines"]}
            if any(i not in lines or lines[i]["type"] != row["array"][i-1] for i in range(1,7)):
                raise RuntimeError("Source line structure mismatch")
        self.tuan = json.loads((directory / "tuan.json").read_text())
        self.xiang = json.loads((directory / "xiang.json").read_text())

    def metadata(self, bits):
        row = self.by_bits[tuple(bits)]
        return {"hexagram_id": row["id"], "name_zh": row["name"], "symbol": row["symbol"], "lines_bottom_to_top": list(bits)}

    def calculate_source(self, variables):
        """Source profile for consultations; keep the locked MVP1 profile replayable.

        Meihua vol. 1: 乾坤無互，互其變卦. Apply this once to the
        original pure Qian/Kun, never recursively to the resulting mutual.
        """
        result = self.calculate(variables)
        pure = result["original"]["hexagram_id"] in (1, 2)
        basis = result["display_hexagrams"]["changed"] if pure else result["original"]
        bits = basis["lines_bottom_to_top"]
        result["display_hexagrams"]["mutual"] = self.metadata(bits[1:4] + bits[2:5])
        result["core_version"] = "maihoa-ymdh-source-v2"
        result["mutual_basis"] = "CHANGED_FOR_PURE" if pure else "ORIGINAL"
        return result

    def calculate(self, variables):
        if set(variables) != {"Y", "M", "D", "H"} or any(type(v) is not int for v in variables.values()):
            raise ValueError("Mai Hoa core takes only four integer Y/M/D/H variables")
        y,m,d,h = (variables[k] for k in ("Y","M","D","H"))
        if not (1 <= y <= 12 and 1 <= m <= 12 and 1 <= d <= 30 and 1 <= h <= 12):
            raise ValueError("Mai Hoa variable outside its range")
        upper, lower, moving = (y+m+d-1)%8+1, (y+m+d+h-1)%8+1, (y+m+d+h-1)%6+1
        bits = TRIGRAMS[lower][2] + TRIGRAMS[upper][2]
        the, dung = (upper, lower) if moving <= 3 else (lower, upper)
        mutual = bits[1:4] + bits[2:5]
        changed = list(bits); changed[moving-1] ^= 1
        original = self.metadata(bits)
        row = self.by_bits[bits]
        line = next(item for item in row["lines"] if item["id"] == moving)
        evidence = []
        def add(kind, text, path, key):
            evidence.append({"evidence_id": key, "label": "SOURCE_ORIGINAL", "text_type": kind, "language": "zh", "text": text,
                             "source": {"repository": "john-walks-slow/open-iching", "commit": COMMIT, "path": path, "key": key,
                                        "url": f"https://github.com/john-walks-slow/open-iching/blob/{COMMIT}/{path}"}})
        add("HEXAGRAM_TEXT", row["scripture"], "iching/iching.json", f"iching__{row['id']}")
        add("LINE_TEXT", line["scripture"], "iching/iching.json", f"iching__{row['id']}_{moving}")
        gaps = []
        # Auxiliary source ids are strings such as iching__17, not integer ids.
        key = f"iching__{row['id']}"
        if key in self.tuan:
            add("TUAN_COMMENTARY", self.tuan[key], "ichuan/tuan.json", key+"_tuan")
        else:
            gaps.append({"source": "ichuan/tuan.json", "hexagram_id": row["id"], "reason": "Missing source entry"})
        if key in self.xiang:
            add("XIANG_COMMENTARY", self.xiang[key], "ichuan/xiang.json", key+"_xiang")
        return {"core_version": "maihoa-ymdh-v1", "variables": variables, "upper": upper, "lower": lower, "moving_line": moving,
                "original": original, "the": {"trigram": the, "name": TRIGRAMS[the][0], "element": TRIGRAMS[the][1]},
                "dung": {"trigram": dung, "name": TRIGRAMS[dung][0], "element": TRIGRAMS[dung][1]},
                "state": state_of(TRIGRAMS[the][1], TRIGRAMS[dung][1]),
                "display_hexagrams": {"mutual": self.metadata(mutual), "changed": self.metadata(changed),
                                      "affects_generation": False, "affects_evaluation": False, "display_on_demand": True},
                "evidence": evidence, "source_gaps": gaps}
