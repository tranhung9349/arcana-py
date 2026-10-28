"""Conservative natal rules: explicit product conventions, source-bound findings."""
from hashlib import sha256
import importlib
import inspect
import json
from pathlib import Path

from .bazi_models import BaziEvidence, BaziFinding, NatalAssessment
from .sampling import GENERATES, CONTROLS
from .time_engine import check_provider

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/reference/bazi"
RULES_PATH = ROOT / "config/bazi_rules.json"
GROUP_GODS = {
    "SELF": {"PEER", "ROB_WEALTH"}, "OUTPUT": {"EATING_GOD", "HURTING_OFFICER"},
    "WEALTH": {"DIRECT_WEALTH", "INDIRECT_WEALTH"}, "OFFICER": {"DIRECT_OFFICER", "SEVEN_KILLINGS"},
    "RESOURCE": {"DIRECT_RESOURCE", "INDIRECT_RESOURCE"},
}
GROUP_NAMES = {"SELF": "Tỷ Kiếp", "OUTPUT": "Thực Thương", "WEALTH": "Tài",
               "OFFICER": "Quan Sát", "RESOURCE": "Ấn"}
RELATION_NAMES = {"STEM_COMBINATION": "hợp Can", "SIX_COMBINATION": "lục hợp", "CLASH": "lục xung",
                  "THREE_COMBINATION": "tam hợp đủ bộ", "THREE_MEETING": "tam hội đủ bộ", "HARM": "tương hại",
                  "PUNISHMENT": "tương hình", "SELF_PUNISHMENT": "tự hình"}


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class BaziRules:
    def __init__(self):
        check_provider()
        manifest = json.loads((DIRECTORY / "manifest.json").read_text())
        for row in manifest["files"]:
            path = ROOT / row["path"]
            if sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                raise RuntimeError("Bazi corpus/rules checksum mismatch: " + row["path"])
        for row in manifest["provider_sources"]:
            raw = Path(inspect.getfile(importlib.import_module(row["module"]))).read_bytes()
            if sha256(raw).hexdigest() != row["sha256"]:
                raise RuntimeError("Bazi provider source differs from pinned 1.4.8")
        self.config = json.loads(RULES_PATH.read_text())
        self.rules_sha256 = sha256(RULES_PATH.read_bytes()).hexdigest()
        self.corpus_version = manifest["corpus_version"]
        self.evidence = [BaziEvidence.model_validate(row) for row in self.config["evidence"]]
        sources = {row["source_id"]: row for row in manifest["sources"]}
        for row in self.config["evidence"]:
            if sha256(row["text"].encode()).hexdigest() != row["sha256"]:
                raise RuntimeError("Bazi evidence text hash mismatch")
            if row["kind"] == "PRIMARY_TEXT":
                source = sources[row["evidence_id"]]
                if row["url"] != source["url"] or row["text"] not in (ROOT / source["path"]).read_text():
                    raise RuntimeError("Bazi quotation not bound to pinned source")
        required = {"NATAL_CONTEXT", "ROOTS", "STRENGTH", "STRUCTURE", "BALANCE", "CLIMATE", "RELATIONS", "TEN_GODS", "SPECIAL_CAUTION"}
        if set(self.config["rules"]) != required:
            raise RuntimeError("Incomplete Bazi rule registry")
        ids = {e.evidence_id for e in self.evidence}
        if len(ids) != len(self.evidence) or any(not set(r["evidence_refs"]) <= ids for r in self.config["rules"].values()):
            raise RuntimeError("Invalid Bazi rule references")

    @property
    def version(self):
        return self.config["rules_version"]

    def overview(self):
        return {"analysis_profile": "bazi_natal_v1", "rules_version": self.version,
                "rules_sha256": self.rules_sha256, "corpus_version": self.corpus_version,
                "topics": self.config["topics"], "calendar_policy": "VN_INSTANT_TO_BEIJING_SECT1",
                "birth_years": [1950, 2026], "coverage": self.config["coverage"], "rules": self.config["rules"],
                "review_status": "RULES_TESTED_NOT_EXPERT_REVIEWED"}

    def evaluate(self, chart, facts):
        findings = []
        def add(key, title, text, refs, state="SUPPORTED", suffix=None, extra_evidence=()):
            findings.append(BaziFinding(finding_id=suffix or key.lower(), rule_id=key, title=title, text=text,
                state=state, fact_refs=list(dict.fromkeys(refs)),
                evidence_refs=list(dict.fromkeys(self.config["rules"][key]["evidence_refs"] + list(extra_evidence)))))

        day = chart.pillars[2].stem
        month = chart.pillars[1]
        resource = next(e for e, child in GENERATES.items() if child == day.element)
        output, wealth = GENERATES[day.element], CONTROLS[day.element]
        officer = next(e for e, target in CONTROLS.items() if target == day.element)
        root_refs = [r.fact_id for r in facts.roots]
        support = facts.visible_support_refs
        main_roots = [r for r in facts.roots if r.level == "MAIN_QI"]
        refs = ["stem:day", "facts:season", *root_refs, *support, *facts.visible_drain_refs]
        add("NATAL_CONTEXT", f"Nhật chủ {day.name} · {day.polarity} {day.element}",
            f"Nhật chủ {day.name} ({day.polarity} {day.element}) là điểm quy chiếu của lá số. "
            f"Bạn sinh tháng {month.branch}, sau tiết {chart.month.jie_name}; bản khí của chi tháng là "
            f"{month.hidden_stems[0].name} ({month.hidden_stems[0].ten_god_name}). "
            f"Các quan hệ được đọc theo Nhật chủ và tháng tiết khí này, không theo tháng âm lịch hoặc ngày đang xem.",
            ["stem:day", "pillar:month", "facts:season", month.hidden_stems[0].fact_id])
        if facts.roots:
            root_text = "; ".join(f"{next(p.label.lower() for p in chart.pillars if p.position == r.pillar)} có {r.stem} "
                                  + ("ở bản khí" if r.level == "MAIN_QI" else "trong tàng can") for r in facts.roots)
            root_text = f"Hành {day.element} có gốc ở chi: {root_text}. "
        else:
            root_text = f"Không thấy tàng can cùng hành {day.element} trong bốn chi, nên chưa có căn cùng hành theo bảng tra này. "
        root_text += f"Ngoài Nhật chủ, có {len(support)} can sinh trợ và {len(facts.visible_drain_refs)} can thuộc nhóm khắc, tiết hoặc hao. "
        root_text += "Căn bản khí và căn trong tàng can được ghi riêng; số lần hiện diện không phải điểm mạnh yếu."
        add("ROOTS", "Gốc khí và sinh trợ", root_text, ["stem:day", *root_refs, *support, *facts.visible_drain_refs, *[p.fact_id for p in chart.pillars]])

        possible_following = not facts.roots and not facts.resource_refs and not support
        # Qualitative conjunctions are an explicit, deliberately narrow product model.
        if chart.month.seasonal_support and main_roots and support:
            strength, label = "STRONG", "Thiên về vượng"
            reason = "Trợ lực theo tháng, căn bản khí và can sinh trợ cùng hiện diện. Ba dấu hiệu này cùng hướng về phía Nhật chủ."
        elif not chart.month.seasonal_support and not facts.roots and not support and not possible_following:
            strength, label = "WEAK", "Thiên về nhược"
            reason = "Tháng không thuộc nhóm sinh trợ, chưa có căn cùng hành và không có can sinh trợ lộ ra. Tuy vậy, Ấn vẫn có trong tàng can, nên chưa bỏ phép xét nội cách."
        else:
            strength, label = "MIXED", "Khí thế có tín hiệu đan xen"
            reason = "Các dấu hiệu về mùa sinh, căn khí và can sinh trợ chưa cùng một hướng đủ rõ để chốt vượng hoặc nhược bằng bộ điều kiện hiện tại."
        season_text = (f"Hành tháng {chart.month.element} cùng hành hoặc sinh {day.element}. " if chart.month.seasonal_support
                       else f"Hành tháng {chart.month.element} không cùng hành và không sinh {day.element}. ")
        add("STRENGTH", label, season_text + reason + " Cần đọc thêm các quan hệ phối hợp để hiểu bên nào đang được trợ lực hoặc bị điều tiết.", refs, "CONDITIONAL")

        candidates = []
        month_hidden = month.hidden_stems
        for h in month_hidden:
            exposed = [p.stem.fact_id for p in chart.pillars if p.position != "day" and p.stem.index == h.index]
            if exposed or h is month_hidden[0]:
                candidates.append({"name": h.ten_god_name + " ở nguyệt lệnh", "ten_god": h.ten_god,
                                   "hidden_stem_ref": h.fact_id, "exposed_refs": exposed})
        jian_lu = (2, 3, 5, 6, 5, 6, 8, 9, 11, 0)
        yang_blade = {0: 3, 2: 6, 4: 6, 6: 9, 8: 0}
        named = "Kiến Lộc" if month.branch_index == jian_lu[day.index] else "Dương Nhận" if yang_blade.get(day.index) == month.branch_index else None
        if named:
            candidates[0]["name"] = named + " · ứng viên"
        details = []
        for c in candidates:
            exposed_labels = [p.label.lower() for p in chart.pillars if p.stem.fact_id in c["exposed_refs"]]
            details.append(c["name"] + (": thấu ở can " + ", ".join(exposed_labels) if exposed_labels else ": chưa thấu ra các can năm, tháng, giờ"))
        add("STRUCTURE", "Nguyệt lệnh và ứng viên cách cục", "; ".join(details) + ". "
            "Bản khí được xét cùng tàng can có thấu. Đây là các trục cần khảo sát, chưa xác nhận thành cách, phá cách hay hóa cách; không lấy riêng can tháng để chốt tên cách.",
            ["pillar:month", *[h.fact_id for h in month_hidden], *[p.stem.fact_id for p in chart.pillars]], "CONDITIONAL")

        if possible_following:
            add("SPECIAL_CAUTION", "Cần xét thêm khả năng ngoại cách", "Không thấy căn cùng hành, Ấn hay can sinh trợ trong lá số. "
                "Có dấu hiệu cần khảo sát thuận thế; chưa đủ bộ quy tắc tòng cách để kết luận. Vì vậy phần cân bằng không tự áp dụng cách bổ Nhật chủ của nội cách.",
                [p.fact_id for p in chart.pillars], "UNRESOLVED")
        if strength == "STRONG" and not possible_following:
            preferred, supporting, restrain = [output], [wealth], [resource, day.element]
            balance_text = f"Hướng phù ức tạm nghiêng về {output} để tạo đường sinh xuất; {wealth} là trục theo sau để khảo sát. "
            balance_text += f"Chưa ưu tiên tăng thêm {resource} và {day.element}, vì ba dấu hiệu sinh trợ đang cùng hướng. "
        elif strength == "WEAK" and not possible_following:
            preferred, supporting, restrain = [resource], [day.element], [output, wealth, officer]
            balance_text = f"Hướng phù ức tạm ưu tiên {resource} để sinh Nhật chủ, tiếp đến {day.element} để đồng hành. "
            balance_text += f"Cần cân nhắc thêm tác động của {output}, {wealth}, {officer} vì chúng thuộc nhóm tiết, hao hoặc khắc. "
        else:
            preferred, supporting, restrain = [], [], []
            balance_text = "Chưa chốt một hành Dụng/Hỷ/Kỵ theo phù ức: " + ("dấu hiệu thuận thế cần được xét riêng. " if possible_following else "khí thế đang có các dấu hiệu trái chiều. ")
        balance_text += "Hướng phù ức nhằm điều tiết phần sinh trợ và hao lực; nhu cầu hàn noãn được đọc riêng ở phần Điều hậu."
        add("BALANCE", "Hướng phù ức · Dụng, Hỷ, Kỵ", balance_text, refs,
            "CONDITIONAL" if preferred else "UNRESOLVED")

        climate = "Hỏa" if month.branch_index in (11, 0, 1) else "Thủy" if month.branch_index in (5, 6, 7) else None
        climate_conflict = climate in restrain if climate else False
        if climate:
            climatic = f"Tháng {month.branch} thuộc nhóm " + ("lạnh; có thể khảo sát Hỏa về nhu cầu làm ấm. " if climate == "Hỏa" else "nóng; có thể khảo sát Thủy về nhu cầu điều hòa nóng. ")
            climatic += f"Trong lá số, {climate} hiện ở {sum(p.stem.element == climate for p in chart.pillars)} can lộ và "
            climatic += f"{sum(h.element == climate for p in chart.pillars for h in p.hidden_stems)} vị trí tàng can. "
            climatic += ("Hướng này khác với nhóm đang cần tiết chế trong phù ức, nên chưa gộp thành một hành ưu tiên cuối cùng. " if climate_conflict else "Cần xét mức hàn, noãn, táo, thấp của toàn cục trước khi chọn hành. ")
        else:
            climatic = f"Tháng {month.branch} không thuộc hai nhóm mùa nóng/lạnh mà bộ gợi ý hiện tại xét. Không suy ra rằng lá số đã đủ cân bằng về hàn noãn. "
        add("CLIMATE", "Hàn noãn và Điều hậu", climatic + "Nhận định còn ở mức gợi ý mùa sinh; cần xét toàn cục trước khi chốt dụng Điều hậu.",
            ["facts:season", "facts:distribution", *[p.fact_id for p in chart.pillars]], "CONDITIONAL")

        if facts.relations:
            labels = {p.fact_id: p.label.lower() for p in chart.pillars}
            relation_text = "; ".join(f"{r.name} {RELATION_NAMES[r.kind]} ({'–'.join(labels[k] for k in r.pillar_refs)})" for r in facts.relations)
            relation_text += ". Các quan hệ có thể cùng tồn tại; hợp chưa có nghĩa đã hóa, xung/hình/hại chưa đủ để phán một sự kiện xấu."
        else:
            relation_text = "Chưa ghi nhận quan hệ trong các bảng hợp, xung, tam hợp/tam hội đủ bộ, hại và hình đang hỗ trợ. Điều này không đồng nghĩa toàn bộ lá số không có tương tác."
        add("RELATIONS", "Những tương tác cần đọc cùng nhau", relation_text,
            [r.fact_id for r in facts.relations] or [p.fact_id for p in chart.pillars],
            extra_evidence=[r.evidence_id for r in facts.relations])

        for group, gods in GROUP_GODS.items():
            visible = [(p, p.stem) for p in chart.pillars if p.position != "day" and p.stem.ten_god in gods]
            hidden = [(p, h) for p in chart.pillars for h in p.hidden_stems if h.ten_god in gods]
            text = (f"Nhóm {GROUP_NAMES[group]} lộ qua " + "; ".join(f"{h.name} ({h.ten_god_name}) ở can {p.label.lower()}" for p, h in visible) + ". "
                    if visible else f"Nhóm {GROUP_NAMES[group]} chưa lộ trên can. ")
            text += ("Trong tàng can có " + "; ".join(f"{h.name} ({h.ten_god_name}) ở chi {p.label.lower()}" for p, h in hidden) + ". "
                     if hidden else "Không thấy nhóm này trong tàng can của bốn chi. ")
            add("TEN_GODS", "Nhóm " + GROUP_NAMES[group], text,
                [h.fact_id for p, h in visible + hidden] or [p.fact_id for p in chart.pillars], suffix="group:" + group)

        assessment = NatalAssessment.model_validate({"strength": strength, "strength_name": label, "possible_following": possible_following,
            "structures": candidates, "balance": {"state": "CONDITIONAL" if preferred else "UNRESOLVED",
            "preferred": preferred, "supporting": supporting, "restrain": restrain},
            "climate_element": climate, "climate_conflict": climate_conflict})
        return assessment, findings
