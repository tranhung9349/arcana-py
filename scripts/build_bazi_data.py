"""Offline build of the natal rule registry and pinned source manifest."""
from hashlib import sha256
import importlib
import inspect
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/reference/bazi"


def build():
    evidence, sources = [], []
    quotes = {
        "text:strength": ("dtt_strength", "Địch Thiên Tủy · Suy vượng", "旺則宜洩宜傷，衰則喜幫喜助，子平之理也，然旺中有衰者存，不可損也。衰中有旺者存，不可益也。"),
        "text:month": ("dtt_month", "Địch Thiên Tủy · Nguyệt lệnh", "月令提綱，譬之宅也，人元用事之神，宅之向也，不可以不卜。"),
        "text:climate": ("dtt_climate", "Địch Thiên Tủy · Hàn noãn", "天道有寒暖，發育萬物，人道得之，不可過也。"),
        "text:relations": ("smt_relations", "Tam Mệnh Thông Hội · Hợp, hại, hình và xung", "凡见刑不可便以凶论"),
    }
    for key, (filename, title, quote) in quotes.items():
        raw_path = DIRECTORY / (filename + ".wikitext")
        meta = json.loads((DIRECTORY / (filename + ".source.json")).read_text())
        if quote not in raw_path.read_text():
            raise RuntimeError("Missing exact source quotation: " + key)
        evidence.append({"evidence_id": key, "kind": "PRIMARY_TEXT", "title": title, "text": quote,
                         "url": meta["url"], "sha256": sha256(quote.encode()).hexdigest()})
        sources.append({"source_id": key, "path": str(raw_path.relative_to(ROOT)), **meta})
    policies = {
        "provider:tables": ("PROVIDER", "Bảng tra 6tail · bản 1.4.8", "Tứ Trụ sect 1; tàng can, Âm Dương, ngũ hành, 100 cặp Thập Thần; bảng ngũ hợp Can, lục hợp Chi và lục xung. Mã cài được kiểm hash lúc khởi tạo.", "https://github.com/6tail/lunar-python"),
        "policy:strength": ("PRODUCT_POLICY", "Quy ước xét khí thế natal v1", "Thiên vượng khi cùng có trợ lực hành tháng, căn bản khí và ít nhất một can sinh trợ ngoài Nhật chủ. Thiên nhược khi không có trợ lực hành tháng, không có căn cùng hành, không có can sinh trợ lộ nhưng có Ấn trong tàng can. Các trường hợp còn lại giữ MIXED. Không có căn, Ấn và can trợ thì giữ nghi vấn thuận thế; không tự chốt ngoại cách. Đây là bộ điều kiện định tính của sản phẩm, chưa phải toàn bộ phép luận cổ thư.", None),
        "policy:structure": ("PRODUCT_POLICY", "Quy ước nguyệt lệnh và ứng viên cách cục", "Xét bản khí chi tháng cùng tàng can thấu đúng Can ở năm/tháng/giờ. Kiến Lộc và Dương Nhận chỉ nhận diện theo bảng điều kiện. Mọi tên cách giữ ở mức ứng viên; chưa xét đủ thành bại, cứu ứng, tư lệnh theo số ngày trong tiết hoặc tòng hóa.", None),
        "policy:balance": ("PRODUCT_POLICY", "Quy ước phù ức và Điều hậu", "Thiên vượng: khảo sát sinh xuất trước, Tài theo sau; thiên nhược: khảo sát Ấn và đồng hành. MIXED hoặc nghi ngoại cách không chốt Dụng/Hỷ/Kỵ. Gợi ý mùa lạnh Hỏa/mùa nóng Thủy tách riêng, không coi là bảng Điều hậu 120 trường hợp và không ghi đè hướng phù ức.", None),
        "policy:relations": ("PRODUCT_POLICY", "Phạm vi nhận diện quan hệ", "Mỗi cặp vị trí chỉ ghi một lần cho từng loại quan hệ. Tam hợp/tam hội cần đủ ba chi khác nhau; ghi cả các vị trí chi lặp, không suy hóa hành. Nhóm hình Dần–Tỵ–Thân và Sửu–Tuất–Mùi chỉ ghi khi đủ bộ; cặp Tý–Mão và tự hình Thìn/Ngọ/Dậu/Hợi ghi riêng. Chưa xét bán hình, phá và chuỗi cứu giải toàn cục.", None),
        "policy:narrative": ("PRODUCT_POLICY", "Phạm vi diễn giải theo chủ đề", "Thập Thần được đọc tương đối với Nhật chủ. Chủ đề sắp xếp dữ kiện và các lực phối hợp, không thay lá số. Câu hỏi tự do được lưu làm ngữ cảnh; chưa phân tích ngữ nghĩa để trả lời sự kiện hoặc thời điểm. Không dự đoán bệnh, tử, mức giàu có hoặc hôn kỳ từ một nhãn đơn.", None),
    }
    for key, (kind, title, text, url) in policies.items():
        evidence.append({"evidence_id": key, "kind": kind, "title": title, "text": text, "url": url, "sha256": sha256(text.encode()).hexdigest()})
    rule_refs = {
        "NATAL_CONTEXT": ["provider:tables", "text:month"], "ROOTS": ["provider:tables", "policy:strength"],
        "STRENGTH": ["text:strength", "policy:strength"], "STRUCTURE": ["text:month", "policy:structure"],
        "BALANCE": ["text:strength", "policy:balance"], "CLIMATE": ["text:climate", "policy:balance"],
        "RELATIONS": ["policy:relations", "text:relations"], "TEN_GODS": ["provider:tables", "policy:narrative"],
        "SPECIAL_CAUTION": ["text:strength", "policy:strength"],
    }
    coverage = [
        {"feature": "Tứ Trụ, tàng can và Thập Thần", "status": "SUPPORTED", "detail": "Theo provider 1.4.8 đã ghim, giờ Việt Nam chuyển cùng thời điểm sang Bắc Kinh, sect 1."},
        {"feature": "Thông căn, can lộ và quan hệ Can Chi", "status": "SUPPORTED", "detail": "Nhận diện theo bảng; chưa kết luận hợp hóa hay dùng một quan hệ để phán cát hung toàn cục."},
        {"feature": "Vượng nhược và hướng phù ức", "status": "PARTIAL", "detail": "Bộ điều kiện định tính; giữ kết luận mở khi tín hiệu khác hướng hoặc nghi ngoại cách."},
        {"feature": "Cách cục và Điều hậu", "status": "PARTIAL", "detail": "Ứng viên nguyệt lệnh và gợi ý mùa; chưa đủ thành bại/cứu ứng, tòng hóa và bảng Điều hậu 120 trường hợp."},
        {"feature": "Phá, bán hình và cứu giải toàn cục", "status": "DEFERRED", "detail": "Chưa có quy tắc đã đối chiếu đủ; không coi phần chưa xét là không có."},
        {"feature": "Đại vận, Lưu niên và hợp hai lá số", "status": "DEFERRED", "detail": "Bản đầu đọc mệnh cục sinh; chưa xác định thời điểm sự kiện."},
        {"feature": "Không rõ giờ sinh và nhận diện ý hỏi", "status": "DEFERRED", "detail": "Cần giờ sinh xác định. Chủ đề chọn trực tiếp; câu hỏi được giữ nguyên làm ngữ cảnh."},
    ]
    rules = {"rules_version": "bazi-natal-2026-10-26-v1", "analysis_profile": "bazi_natal_v1",
             "topics": [{"id": key, "name": name} for key, name in [("GENERAL", "Tổng quan"), ("CAREER", "Công việc"), ("WEALTH", "Tài chính"), ("STUDY", "Học tập"), ("RELATIONSHIPS", "Quan hệ")]],
             "tables": {"harms": [[0, 7], [1, 6], [2, 5], [3, 4], [8, 11], [9, 10]], "self_punishments": [4, 6, 9, 11],
                        "three_combinations": [[8, 0, 4], [2, 6, 10], [5, 9, 1], [11, 3, 7]],
                        "three_meetings": [[2, 3, 4], [5, 6, 7], [8, 9, 10], [11, 0, 1]],
                        "three_punishments": [[2, 5, 8], [1, 10, 7]]},
             "rules": {key: {"evidence_refs": refs, "review_status": "IMPLEMENTATION_TESTED_NOT_EXPERT_REVIEWED"} for key, refs in rule_refs.items()},
             "coverage": coverage, "evidence": evidence}
    rules_path = ROOT / "config/bazi_rules.json"
    rules_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n")
    files = [rules_path, *sorted(DIRECTORY.glob("*.wikitext")), *sorted(DIRECTORY.glob("*.source.json"))]
    manifest = {"corpus_version": "bazi-corpus-2026-10-26-v1", "sources": sources,
                "files": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p.read_bytes()).hexdigest()} for p in files],
                "provider_sources": [{"module": module, "sha256": sha256(Path(inspect.getfile(importlib.import_module(module))).read_bytes()).hexdigest()}
                                     for module in ("lunar_python.EightChar", "lunar_python.Lunar", "lunar_python.util.LunarUtil")]}
    (DIRECTORY / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"sources": len(sources), "rules": len(rule_refs), "evidence": len(evidence), "rules_sha256": sha256(rules_path.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    build()
