"""Choose an editorial focus, never derive or change a divination finding."""
import re
import unicodedata


def question_intent(question):
    """A bounded writing hint; neither a topic classifier nor a use-god selector."""
    text = unicodedata.normalize("NFD", question.lower()).replace("đ", "d")
    text = " ".join("".join(c for c in text if unicodedata.category(c) != "Mn").split())
    patterns = (
        ("TIMING", r"\b(khi nao|bao gio|nam nay|thang nay|tuan nay|nam 20\d\d)\b"),
        ("COMPARISON", r"\b(so sanh|lua chon|phuong an)\b|\bnen\b.{1,160}\bhay\b"),
        ("EXPLANATION", r"\b(vi sao|tai sao|nghia la|co nghia gi)\b"),
        ("PREPARATION", r"\b(can|nen) (chuan bi|ra soat|chu y|thay doi|kiem tra)\b"),
        ("OUTCOME", r"\b(thanh cong|duoc duyet|co duoc|ket qua)\b|\bco\b.{1,160}\bkhong\b"),
    )
    return next((key for key, pattern in patterns if re.search(pattern, text)), "OPEN")


def plan_reading(context, playbook):
    """Only adapter tags and fixed templates affect the trusted instructions.

    Never copy question/fact/source prose into a system message. Missing tags
    choose the conservative default; they do not imply a negative assessment.
    """
    method = playbook["methods"][context.method]
    signals = set(context.signals)
    applicable = [r for r in method["routes"] if not r["when_any"] or signals.intersection(r["when_any"])]
    primary = applicable[0]
    qualifiers = [r for r in applicable[1:] if r["when_any"]][:2]
    intent = question_intent(context.question)
    topic = context.topic if context.topic in method["topics"] else "GENERAL"
    sources = list(dict.fromkeys(s for row in [primary, *qualifiers] for s in row["source_ids"]))
    instruction = "\n".join([
        "TRỌNG TÂM BIÊN TẬP CỦA PHIÊN (không phải kết luận mệnh lý mới)",
        "Chọn thứ tự và dung lượng đoạn theo trọng tâm dưới đây. Không in tên nhánh, dàn ý hoặc mã nội bộ.",
        primary["instruction"],
        *("Điều kiện đi kèm: " + r["instruction"] for r in qualifiers),
        "Mục đích câu hỏi: " + playbook["intents"][intent],
        "Chủ đề đã chọn: " + method["topics"][topic],
        "Chỉ khai triển các quan hệ đã có trong findings; chỉ dẫn này không cho phép tự tính hiệu lực, cứu ứng, hóa cục hoặc ứng kỳ.",
    ])
    return {"version": playbook["version"], "primary_id": primary["id"],
            "qualifier_ids": [r["id"] for r in qualifiers], "intent": intent,
            "topic": topic, "source_ids": sources, "instruction": instruction}
