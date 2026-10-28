"""A separate prompt pack for saved date decisions, reusing the AI contract."""
from hashlib import sha256
import json

from .interpretation_prompt import ROOT, Response, validate_response
from randomyst.date_ai_context import DateReadingContext

DATE_PACK = ROOT / "data/interpretation/date_v1"


def load_date_pack(directory=DATE_PACK):
    manifest = json.loads((directory / "manifest.json").read_text())
    for item in manifest["files"]:
        if sha256((ROOT / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Date prompt file changed: " + item["path"])
    cases = json.loads((directory / "cases.json").read_text())
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate date teaching case")
    for c in cases:
        if c["review_status"] != "EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED":
            raise ValueError("Unexpected date example review status")
        validate_response(c["response"], DateReadingContext.model_validate(c["context"]))
    return manifest, cases


def build_date_messages(context, limit=2):
    ctx = DateReadingContext.model_validate(context)
    manifest, cases = load_date_pack()
    signals = set(ctx.signals)
    # Explicit state/mode gates prevent a favorable or hour-based teaching case
    # from setting the tone for a blocked, unresolved or day-only consultation.
    state = next(s for s in ("UNRESOLVED", "GOOD", "NORMAL", "BAD") if s in signals)
    mode = "DAY_ONLY" if "DAY_ONLY" in signals else "DAY_AND_HOUR"
    compatible = [c for c in cases if state in c["context"]["signals"] and mode in c["context"]["signals"]]
    selected = sorted(compatible, key=lambda c: (-len(signals.intersection(c["context"]["signals"])), c["id"]))[:limit]
    prompt = (ROOT / manifest["system_prompt"]).read_text()
    # Only fixed instructions selected by trusted adapter signals enter system.
    focus = ("Kết quả còn chưa rõ: giải thích nút thiếu/mâu thuẫn trước, không đề xuất dùng ngày."
             if state == "UNRESOLVED" else
             "Có điều kiện loại trừ: mở đầu bằng lý do chặn, sau đó giải thích tại sao điểm thô không cứu được."
             if "HARD_EXCLUSION" in signals else
             "Có khoảng Ngày Đẹp: giải thích điều kiện đủ đã đạt và giới hạn của đúng khoảng được chọn."
             if state == "GOOD" else
             "Chưa đạt Ngày Đẹp: làm rõ điều kiện còn thiếu hoặc mức trừ quyết định, không đổi nhãn kết quả.")
    prompt += "\nTRỌNG TÂM PHIÊN: " + focus
    prompt += "\nCHẾ ĐỘ: " + ("Chỉ xét ngày. Không đưa ra giờ đẹp." if mode == "DAY_ONLY" else "Đã xét ngày và giờ bắt đầu trong lịch đã chọn.")
    messages = [{"role": "system", "content": prompt + "\nresponse_schema=" + json.dumps(Response.model_json_schema(), ensure_ascii=False)}]
    for case in selected:
        messages += [{"role": "user", "content": json.dumps(case["context"], ensure_ascii=False)},
                     {"role": "assistant", "content": json.dumps(case["response"], ensure_ascii=False)}]
    messages.append({"role": "user", "content": ctx.model_dump_json()})
    return {"pack_version": manifest["version"], "case_ids": [c["id"] for c in selected], "messages": messages,
            "messages_sha256": sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()}
