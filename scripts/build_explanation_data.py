"""Build the display-only corpus from pinned, checksum-verified source files.

Node is a build tool for the upstream constant tables, never a runtime dependency.
Vietnamese I Ching translations are authored drafts; this script only binds their
IDs/positions to the exact Hán text so later source changes fail validation.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data/reference"


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def build():
    manifest = json.loads((REFERENCE / "manifest.json").read_text())
    for item in manifest["files"]:
        if hashlib.sha256((REFERENCE / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError("Pinned source checksum mismatch: " + item["path"])
    sources = {
        "stems": "tinix-bazi/phan_tich/data/dich_thien_tuy_data.js",
        "structures": "tinix-bazi/phan_tich/data/ngu_hanh_data.js",
    }
    script = "const a=require(process.argv[1]);const b=require(process.argv[2]);process.stdout.write(JSON.stringify({stems:a.STEM_ESSENCE,structures:b.STRUCTURE_ANALYSIS}));"
    process = subprocess.run(["node", "-e", script, *[str(REFERENCE / p) for p in sources.values()]],
                             check=True, capture_output=True, text=True)
    data = json.loads(process.stdout)
    if len(data["stems"]) != 10 or not data["structures"]:
        raise RuntimeError("Unexpected upstream interpretation tables")
    data.update(version="tinix-source-prose-v1", label="SOURCE_ORIGINAL",
                source_commit=manifest["tinix_commit"],
                source_sha256={key: hashlib.sha256((REFERENCE / path).read_bytes()).hexdigest()
                               for key, path in sources.items()},
                source_paths={key: "backendjs/src/bazi/" + path.removeprefix("tinix-bazi/")
                              for key, path in sources.items()})
    target = ROOT / "data/interpretation/tinix_vi.json"
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    draft_path = ROOT / "data/interpretation/iching_vi_draft.json"
    draft = json.loads(draft_path.read_text())
    if draft["source_commit"] != manifest["iching_commit"]:
        raise RuntimeError("Translation draft belongs to another source commit")
    original = {r["id"]: r for r in json.loads((REFERENCE / "open-iching/iching.json").read_text())}
    if {r["id"] for r in draft["hexagrams"]} != set(original) or len(draft["hexagrams"]) != 64:
        raise RuntimeError("Expected exactly 64 translation records")
    for row in draft["hexagrams"]:
        source = original[row["id"]]
        if len(row["lines"]) != 6:
            raise RuntimeError("Expected six line translations per hexagram")
        binding = {"judgment": digest(source["scripture"]),
                   "lines": [digest(next(l["scripture"] for l in source["lines"] if l["id"] == i))
                             for i in range(1, 7)]}
        if row.get("source_text_sha256", binding) != binding:
            raise RuntimeError("Source text changed; review the translation before rebinding")
        row["source_text_sha256"] = binding
    draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"hexagrams": 64, "line_translations": 384, "bazi_stems": len(data["stems"]),
                      "bazi_structures": len(data["structures"])}, ensure_ascii=False))


if __name__ == "__main__":
    build()
