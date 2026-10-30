"""Bounded retrieval from the pinned corpus for one saved three-coin casting.

No network, casting, calendar calculation or new divination finding happens here.
Vietnamese AI drafts are deliberately excluded from primary source evidence.
"""
from hashlib import sha256
import json

from .maihoa import COMMIT, ROOT, IchingRepository


def _evidence(key, title, text, url):
    return {"id": key, "title": title, "text": text,
            "sha256": sha256(text.encode()).hexdigest(), "url": url, "kind": "PRIMARY_TEXT"}


def casting_sources(session):
    """Retrieve only the original/changed hexagrams, checking saved source cards."""
    corpus = IchingRepository()  # Validates all three files against the local manifest.
    evidence, documents, gaps = [], [], []
    for role, label in (("original", "Quẻ chủ"), ("changed", "Quẻ biến")):
        reading = session[role]
        if reading is None:
            continue
        chart = reading["chart"]
        row = corpus.by_bits[tuple(chart["lines_bottom_to_top"])]
        if row["id"] != chart["hexagram_id"]:
            raise ValueError("Saved hexagram ID differs from the pinned source")
        root = f"iching__{row['id']}"
        records = {}

        def add(kind, title, text, path, key, position=None):
            key_id = key + "__" + kind.lower()
            url = f"https://github.com/john-walks-slow/open-iching/blob/{COMMIT}/{path}"
            records[key_id] = (kind, text, path, key)
            evidence.append(_evidence(key_id, f"{label} #{row['id']} · {title}", text, url))
            documents.append({"evidence_id": key_id, "role": role, "hexagram_id": row["id"],
                              "text_type": kind, "position": position,
                              "moving_in_original": position in session["moving_lines"] if position else False,
                              "repository": "john-walks-slow/open-iching", "commit": COMMIT,
                              "path": path, "key": key, "source_state": "PINNED_TRANSCRIPTION"})

        add("HEXAGRAM_TEXT", "Quẻ từ", row["scripture"], "iching/iching.json", root)
        for kind, title, table, path in (
            ("TUAN_COMMENTARY", "Thoán truyện", corpus.tuan, "ichuan/tuan.json"),
            ("XIANG_COMMENTARY", "Đại Tượng truyện", corpus.xiang, "ichuan/xiang.json"),
        ):
            if root in table:
                add(kind, title, table[root], path, root)
            else:
                gaps.append({"role": role, "hexagram_id": row["id"], "text_type": kind,
                             "reason": "MISSING_FROM_PINNED_CORPUS"})
        for line in row["lines"]:
            position = line["id"]
            if position > 6 and not (role == "original" and len(session["moving_lines"]) == 6):
                continue
            key = f"{root}_{position}"
            add("LINE_TEXT", line["name"], line["scripture"], "iching/iching.json", key, position)
            if role == "original" and position in session["moving_lines"]:
                if key in corpus.xiang:
                    add("LINE_XIANG_COMMENTARY", f"Tiểu Tượng · hào {position}", corpus.xiang[key],
                        "ichuan/xiang.json", key, position)
                else:
                    gaps.append({"role": role, "position": position, "text_type": "LINE_XIANG_COMMENTARY",
                                 "reason": "MISSING_FROM_PINNED_CORPUS"})
        # A saved quotation must match the locked corpus in both text and location.
        # Never relabel a Vietnamese AI translation/overview as a primary text.
        for card in [*reading["text"]["cards"], *reading["reference_lines"]]:
            source = card["source"]
            expected = records.get(card["evidence_id"])
            if (expected != (card["text_type"], card["text"], source["path"], source["key"])
                    or source["repository"] != "john-walks-slow/open-iching"
                    or source["commit"] != COMMIT or card["language"] != "zh"):
                raise ValueError("Saved quotation differs from the pinned hexagram source")
    return evidence, documents, gaps


def method_sources(analysis, sources):
    """Select available pinned method excerpts; disclose bibliography-only gaps."""
    by_id = {s["id"]: s for s in sources}
    bindings = {"ROLES": ["ly:roles", "ly:effective"], "MONTH": ["ly:month"], "DAY": ["ly:day"]}
    evidence, documents = [], []
    target = analysis["selection"]["target"]
    prefixes = {"Phụ mẫu": "* 父母爻：", "Quan quỷ": "* 官鬼爻：", "Huynh đệ": "* 兄弟爻：",
                "Thê tài": "* 妻財爻：", "Tử tôn": "* 子孫爻："}
    if target in prefixes:
        path = ROOT / "data/reference/interpretation/zsby_8.wikitext"
        meta = json.loads(path.with_suffix(".source.json").read_text())
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != meta["sha256"]:
            raise ValueError("Use-god chapter checksum mismatch")
        paragraph = next(line for line in raw.decode().splitlines() if line.startswith(prefixes[target]))
        text = paragraph.removeprefix(prefixes[target]).split("。", 1)[0] + "。"
        key = "ly:use_target"
        evidence.append(_evidence(key, f"Tăng San Bốc Dịch · Dụng thần · {target}", text, meta["url"]))
        documents.append({"evidence_id": key, "source_state": "PINNED_TRANSCRIPTION",
                          "raw_path": str(path.relative_to(ROOT)), "revision_id": meta["revision_id"],
                          "document_sha256": meta["sha256"]})
        bindings["USE"] = [key]
    needed = {sid for f in analysis["findings"] for sid in f["source_ids"]}
    for key in dict.fromkeys(key for sid in sorted(needed) for key in bindings.get(sid, [])):
        if key == "ly:use_target":
            continue
        source = by_id[key]
        if not source.get("raw_path") or source["source_state"] != "PINNED_TRANSCRIPTION":
            raise ValueError("Liu Yao method excerpt must have a pinned local source")
        path = ROOT / source["raw_path"]
        meta = json.loads(path.with_suffix(".source.json").read_text())
        raw = path.read_bytes()
        if (sha256(raw).hexdigest() != meta["sha256"] or source["text"] not in raw.decode()
                or source["url"] != meta["url"]):
            raise ValueError("Liu Yao method quotation differs from its pinned revision")
        evidence.append({k: source[k] for k in ("id", "title", "text", "sha256", "url", "kind")})
        documents.append({"evidence_id": key, "source_state": source["source_state"],
                          "raw_path": source["raw_path"], "revision_id": meta["revision_id"],
                          "document_sha256": meta["sha256"]})
    bibliography = {s["id"]: s for s in analysis["sources"]}
    source_map = [{"finding_id": f["id"], "rules": [
        {"rule_source_id": sid, "bibliography": bibliography[sid],
         "primary_evidence_refs": bindings.get(sid, []),
         "capture_state": "PINNED_EXCERPT_AVAILABLE" if bindings.get(sid) else "BIBLIOGRAPHY_ONLY"}
        for sid in f["source_ids"]]} for f in analysis["findings"]]
    refs = {row["finding_id"]: list(dict.fromkeys(
        key for rule in row["rules"] for key in rule["primary_evidence_refs"])) for row in source_map}
    return evidence, documents, source_map, refs
