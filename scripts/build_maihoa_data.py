"""Build source-bound Mai Hoa rules from pinned Wikisource revisions, offline."""
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/reference/maihoa"


def digest(raw):
    return sha256(raw).hexdigest()


def build():
    manifest = json.loads((DIRECTORY / "manifest.json").read_text())
    headings = {}
    for item in manifest["files"]:
        raw = (DIRECTORY / item["path"]).read_bytes()
        if digest(raw) != item["sha256"]:
            raise RuntimeError("Mai Hoa source checksum mismatch")
        volume = int(item["path"].split("_")[1].split(".")[0])
        parts = re.split(r"(?m)^={2,5}\s*(.*?)\s*={2,5}\s*$", raw.decode())
        for heading, body in zip(parts[1::2], parts[2::2]):
            # Retain wording/punctuation. Only trim each line and empty boundaries.
            text = "\n".join(line.strip() for line in body.strip().splitlines())
            headings[(volume, heading)] = (text, item)
    rules_path = ROOT / "config/maihoa_rules.json"
    rules_raw = rules_path.read_bytes()
    rules = json.loads(rules_raw)
    evidence = {}
    for key, entry in rules["evidence"].items():
        section, source = headings[(entry["volume"], entry["section"])]
        if entry["quote"] not in section:
            raise RuntimeError("Quote not found in pinned section: " + key)
        evidence[key] = {
            "evidence_id": key, "title": entry["title"], "text": entry["quote"],
            "text_sha256": digest(entry["quote"].encode()),
            "section_sha256": digest(section.encode()), "section": entry["section"],
            "volume": entry["volume"], "source": source,
        }
    for topic, row in rules["topics"].items():
        if set(row["relations"]) != {"SAME", "USE_GENERATES_BODY", "BODY_CONTROLS_USE", "BODY_GENERATES_USE", "USE_CONTROLS_BODY"}:
            raise RuntimeError("Incomplete topic relation table: " + topic)
        for value in row["relations"].values():
            if value["quote"] not in headings[(2, row["section"])][0]:
                raise RuntimeError("Topic quote not found: " + topic)
            if value["quote"] != evidence[value["evidence_id"]]["text"] or evidence[value["evidence_id"]]["section"] != row["section"]:
                raise RuntimeError("Topic evidence mismatch: " + topic)
    for entry in rules["auxiliary_relations"].values():
        if entry["quote"] != evidence[entry["evidence_id"]]["text"]:
            raise RuntimeError("Auxiliary rule quotation mismatch")
    result = {"corpus_version": manifest["corpus_version"], "rules_version": rules["rules_version"],
              "rules_sha256": digest(rules_raw), "evidence": evidence}
    target = DIRECTORY / "compiled.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"rules_version": rules["rules_version"], "source_revisions": len(manifest["files"]),
                      "evidence": len(evidence), "topics": len(rules["topics"]),
                      "compiled_sha256": digest(target.read_bytes())}, ensure_ascii=False))


if __name__ == "__main__":
    build()
