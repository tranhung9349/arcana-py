"""Synthetic stage outputs for contract tests; not validated divination examples."""
from copy import deepcopy

from randomyst.bazi_pipeline import DISCLAIMER, digest
from randomyst.bazi_portrait import period_plan, portrait_outline
from types import SimpleNamespace


def analysis_for(context, *, whole_life=False):
    facts = [row["id"] for row in context["facts"][:2]]
    evidence = [context["evidence"][0]["id"]]
    basis = {"text": "Hai dữ kiện được dùng làm căn cứ kiểm thử.", "fact_refs": facts, "evidence_refs": evidence}
    patterns = []
    for index, (name, domain) in enumerate((("Chuẩn bị trước khi thử", "LEARNING"), ("Kiểm tra khi phối hợp", "WORK"), ("Cân nhắc các lựa chọn", "DECISIONS")), 1):
        pid = f"P{index:02}"
        patterns.append({"id": pid, "name": name, "thesis": "Một giả thuyết truyền thống được nêu để kiểm tra hợp đồng.",
            "basis": [deepcopy(basis), deepcopy(basis)], "mechanism": "Nhật chủ và các quan hệ được cân cùng điều kiện của toàn lá số.",
            "manifestations": [{"id": pid+"-M01", "domain": domain, "hypothesis": "Muốn biết điều kiện trước khi thử một việc mới.",
                "everyday_example": "Khi gặp một nhiệm vụ mới, hỏi rõ yêu cầu rồi thử một phần nhỏ.",
                "upside": "Chuẩn bị đủ giúp tránh hiểu sai yêu cầu.", "downside": "Chuẩn bị quá lâu có thể làm chậm bước thử.", "status": "TRADITIONAL_HYPOTHESIS"}],
            "conditions": [{"id": pid+"-C01", "text": "Biểu hiện phụ thuộc mức quen thuộc với việc đang làm."}],
            "limits": [{"id": pid+"-L01", "text": "Chưa có dữ kiện để xác nhận thói quen thực tế của người đọc."}],
            "counter_evidence": "Dữ kiện khác có thể giới hạn giả thuyết này.", "alternative_explanation": "Hoàn cảnh và kinh nghiệm có thể giải thích cách phản ứng.", "argument_strength": "MEDIUM"})
    result = {"schema_version": "bazi-structural-analysis-v1", "context_id": context["context_id"], "topic": context["topic"], "question": context["question"],
        "sufficiency": "SUFFICIENT", "technical_overview": basis, "patterns": patterns,
        "relationships": [{"pattern_ids": ["P01", "P02"], "kind": "TENSION", "explanation": "Chuẩn bị và thử nhanh có thể cùng tồn tại.", "conditions": "Mức quen việc làm thay đổi cách biểu hiện."}],
        "synthesis": {"central_theme": "Tìm cách chuẩn bị vừa đủ trước khi thử.", "key_tendencies": ["Chuẩn bị trước, rồi so kết quả."],
            "favorable_conditions": ["Yêu cầu rõ ràng."], "unfavorable_conditions": ["Yêu cầu thay đổi."], "unresolved": ["Chưa xác nhận thói quen thực tế."]},
        "source_limitations": context["limitations"]}
    if whole_life:
        def claim(id,text,refs=None):
            return {"id":id,"status":"LIMITED","text":text,"opportunity":"Nguồn lực cần được xét cùng khả năng sử dụng.",
                "challenge":"Kết quả phụ thuộc cách phối hợp các nguồn lực.","condition":"Cần đối chiếu với hoàn cảnh và các quan hệ đã phân tích.",
                "limit":"Không xác nhận sự kiện đã xảy ra hoặc kết quả chắc chắn.","fact_refs":refs or facts,"evidence_refs":evidence}
        plan=period_plan(SimpleNamespace(facts=[SimpleNamespace(**row) for row in context['facts']]))
        result['whole_life']={"overview":claim('O01','Toàn mệnh được xét qua sự nghiệp, tài chính, quan hệ và sự đổi khác giữa các chặng vận.'),
            "areas":[{**claim(f'L{i:02}',text),'area':area} for i,(area,text) in enumerate([
                ('CAREER','Đường phát triển nghề nghiệp được xem từ nền tảng nguồn lực và cách đảm nhận trách nhiệm.'),
                ('FINANCES','Tạo nguồn thu và giữ phần tích lũy được xem riêng từ cấu trúc tài chính trong lá số.'),
                ('RELATIONSHIPS','Tình cảm và gia đình được xem riêng với hợp tác trong công việc, chưa xác nhận tình trạng hôn nhân.')],1)],
            "periods":[{**claim(row['id'],'Các vận trong chặng này có thể thay đổi lực hỗ trợ và áp lực so với nền lá số.',
                                 ['engine:luck_cycles',facts[0]]),**row} for row in plan],
            "timing_status":"AVAILABLE" if plan else "NOT_AVAILABLE",
            "timing_note":"Các mốc là phạm vi Đại vận đã tính, không phải lịch sự kiện hay giới hạn tuổi thọ." if plan else 'Chưa có Đại vận nên chưa chia chặng cuộc đời.'}
    return result


def life_for(analysis):
    def block(text, ids=None):
        ids = list(ids if ids is not None else [p["id"] for p in analysis["patterns"]])
        return {"text": text, "pattern_refs": ids,
            "manifestation_refs": [m["id"] for p in analysis["patterns"] if p["id"] in ids for m in p["manifestations"]],
            "condition_refs": [c["id"] for p in analysis["patterns"] if p["id"] in ids for c in p["conditions"]],
            "limit_refs": [c["id"] for p in analysis["patterns"] if p["id"] in ids for c in p["limits"]]}
    tendencies = [{"pattern_id": p["id"], "title": p["name"], **block(
        "Khi bắt đầu một việc mới, bạn có thể muốn biết rõ yêu cầu rồi mới thử. Cách chuẩn bị này giúp tránh hiểu sai, nhưng chuẩn bị quá lâu cũng có thể làm chậm bước thử. Việc quen hay lạ sẽ làm cách phản ứng thay đổi; lá số chưa xác nhận đây là thói quen thực tế của bạn.", [p["id"]])} for p in analysis["patterns"]]
    result = {"schema_version": "bazi-life-reading-v1", "context_id": analysis["context_id"], "analysis_sha256": digest(analysis),
        "overview": block("Một điểm để bạn đối chiếu là cách chuẩn bị trước khi thử việc mới. Các khuynh hướng dưới đây là giả thuyết theo cách đọc truyền thống; chúng có thể thay đổi theo hoàn cảnh và kinh nghiệm."),
        "tendencies": tendencies, "in_life": [], "contradictions": [block("Bạn có thể muốn chuẩn bị kỹ khi gặp việc lạ nhưng thử nhanh hơn với việc đã quen. Hai cách phản ứng này phụ thuộc mức quen thuộc của nhiệm vụ, không nhất thiết trái ngược nhau.", ["P01", "P02"])] if len(analysis['patterns'])>=2 and analysis['relationships'] else [],
        "takeaway": block("Bạn có thể thử một phần nhỏ sau khi đã hiểu yêu cầu, rồi dùng kết quả để quyết định cần chuẩn bị thêm điều gì. Cách này giúp tránh cả việc làm vội lẫn chờ đợi quá lâu."),
        "limits": [{"text": "Chưa xác nhận thói quen thực tế hoặc thời điểm một việc sẽ xảy ra.", "source_refs": ["G01"]}], "disclaimer": DISCLAIMER}
    if analysis.get('whole_life'):
        from randomyst.bazi_portrait import WholeLifeAnalysis
        result['whole_life']=portrait_outline(WholeLifeAnalysis.model_validate(analysis['whole_life']))
        for target,source in zip(result['whole_life']['areas'],analysis['whole_life']['areas']):
            target['text']=source['text']+' '+source['condition']+' '+source['limit']
        for target,source in zip(result['whole_life']['periods'],analysis['whole_life']['periods']):
            target['text']=source['text']+' '+source['condition']
        result['overview']['text']='Bức tranh đường đời trong bản kiểm thử này liên kết sự nghiệp, tài chính và các mối gắn bó, rồi xét chúng qua những chặng vận đã tính. Chưa xác nhận đây là hoàn cảnh ngoài đời của người đọc.'
        result['takeaway']['text']='Điểm tựa của toàn mệnh cần được xem đồng thời với trách nhiệm, việc giữ nguồn lực và sự cân bằng giữa các mối gắn bó.'
        result.update(tendencies=[],in_life=[],contradictions=[])
    return result


def prose_for(analysis):
    portrait=analysis['whole_life']
    return {"schema_version": "bazi-whole-life-prose-v1",
            "overview":"Bức tranh đường đời trong bản kiểm thử này liên kết sự nghiệp, tài chính và các mối gắn bó qua những chặng đã tính.",
            "areas": [{"source_id": row["id"], "text": row["text"]+' '+row['condition']+' '+row['limit']} for row in portrait["areas"]],
            "periods": [{"id": row["id"], "text": row["text"]+' '+row['condition']} for row in portrait["periods"]],
            "takeaway":"Điểm tựa cần được xem đồng thời với trách nhiệm, việc giữ nguồn lực và sự cân bằng giữa các mối gắn bó.",
            "limit":"Chưa xác nhận sự kiện thực tế hoặc thời điểm cụ thể."}
