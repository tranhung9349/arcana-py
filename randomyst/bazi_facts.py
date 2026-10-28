"""Provider-backed natal facts; no scoring or prose generation."""
from itertools import combinations

from lunar_python.util import LunarUtil

from .bazi_models import NatalChart, NatalFacts
from .time_engine import STEMS, STEMS_ZH, BRANCHES, BRANCHES_ZH, pillars
from .sampling import ELEMENTS, GENERATES, CONTROLS

ELEMENT_ZH = dict(zip("木火土金水", ELEMENTS))
GODS = {
    "比肩": ("PEER", "Tỷ Kiên"), "劫财": ("ROB_WEALTH", "Kiếp Tài"),
    "食神": ("EATING_GOD", "Thực Thần"), "伤官": ("HURTING_OFFICER", "Thương Quan"),
    "偏财": ("INDIRECT_WEALTH", "Thiên Tài"), "正财": ("DIRECT_WEALTH", "Chính Tài"),
    "七杀": ("SEVEN_KILLINGS", "Thất Sát"), "正官": ("DIRECT_OFFICER", "Chính Quan"),
    "偏印": ("INDIRECT_RESOURCE", "Thiên Ấn"), "正印": ("DIRECT_RESOURCE", "Chính Ấn"),
}
POSITIONS = ("year", "month", "day", "hour")
LABELS = ("Năm", "Tháng", "Ngày", "Giờ")


def ten_god(day_index, other_index):
    return GODS[LunarUtil.SHI_SHEN[STEMS_ZH[day_index] + STEMS_ZH[other_index]]]


def stem_fact(index, day, fact_id, is_day=False):
    god, name = ("DAY_MASTER", "Nhật chủ") if is_day else ten_god(day, index)
    return {"fact_id": fact_id, "index": index, "name": STEMS[index], "zh": STEMS_ZH[index],
            "element": ELEMENT_ZH[LunarUtil.WU_XING_GAN[STEMS_ZH[index]]],
            "polarity": "Dương" if index % 2 == 0 else "Âm", "ten_god": god, "ten_god_name": name}


def chart_from_birth(birth):
    natal = pillars(birth.civil_datetime)
    day = natal["gans"][2]
    rows = []
    for position, label, g, z in zip(POSITIONS, LABELS, natal["gans"], natal["zhis"]):
        rows.append({"fact_id": "pillar:" + position, "position": position, "label": label,
                     "stem": stem_fact(g, day, "stem:" + position, position == "day"),
                     "branch_index": z, "branch": BRANCHES[z], "branch_zh": BRANCHES_ZH[z],
                     "branch_element": ELEMENT_ZH[LunarUtil.WU_XING_ZHI[BRANCHES_ZH[z]]],
                     "hidden_stems": [stem_fact(STEMS_ZH.index(h), day, f"hidden:{position}:{i}")
                                      for i, h in enumerate(LunarUtil.ZHI_HIDE_GAN[BRANCHES_ZH[z]])]})
    month = natal["solar_month"]
    month_element = rows[1]["branch_element"]
    day_element = rows[2]["stem"]["element"]
    return NatalChart.model_validate({"civil_datetime": birth.civil_datetime, "beijing_datetime": natal["beijing_datetime"],
        "provider": natal["provider"], "sect": natal["sect"], "day_boundary": natal["day_boundary"], "pillars": rows,
        "month": {"branch": month["month_branch"], "branch_index": month["month_branch_index"], "element": month_element,
                  "jie_name": month["jie_name"], "jie_start_beijing": month["jie_start_beijing"],
                  "seasonal_support": month_element == day_element or GENERATES[month_element] == day_element}})


def relations_for(chart, tables):
    """Each actual pair/group once; repeated tokens cannot complete a three-branch set."""
    rows = []
    def add(kind, members, tokens, evidence):
        rows.append({"fact_id": f"relation:{len(rows)}", "kind": kind,
                     "name": "–".join(tokens), "tokens": tokens,
                     "pillar_refs": [p.fact_id for p in members], "evidence_id": evidence,
                     "transformation_assumed": False})
    for a, b in combinations(chart.pillars, 2):
        x, y = a.stem.index, b.stem.index
        if LunarUtil.HE_GAN_5[x] == STEMS_ZH[y]:
            add("STEM_COMBINATION", [a, b], [a.stem.name, b.stem.name], "provider:tables")
        x, y = a.branch_index, b.branch_index
        if LunarUtil.HE_ZHI_6[x] == BRANCHES_ZH[y]:
            add("SIX_COMBINATION", [a, b], [a.branch, b.branch], "provider:tables")
        if LunarUtil.CHONG[x] == BRANCHES_ZH[y]:
            add("CLASH", [a, b], [a.branch, b.branch], "provider:tables")
        if sorted([x, y]) in tables["harms"]:
            add("HARM", [a, b], [a.branch, b.branch], "text:relations")
        if sorted([x, y]) == [0, 3]:
            add("PUNISHMENT", [a, b], [a.branch, b.branch], "text:relations")
        if x == y and x in tables["self_punishments"]:
            add("SELF_PUNISHMENT", [a, b], [a.branch], "text:relations")
    present = {p.branch_index for p in chart.pillars}
    for key, kind in (("three_combinations", "THREE_COMBINATION"), ("three_meetings", "THREE_MEETING"),
                      ("three_punishments", "PUNISHMENT")):
        for group in tables[key]:
            if set(group) <= present:
                add(kind, [p for p in chart.pillars if p.branch_index in group],
                    [BRANCHES[i] for i in group], "text:relations" if key == "three_punishments" else "policy:relations")
    return rows


def facts_for(chart, tables):
    day = chart.pillars[2].stem.element
    roots, support, drain, resource = [], [], [], []
    for p in chart.pillars:
        if p.position != "day":
            (support if p.stem.element == day or GENERATES[p.stem.element] == day else drain).append(p.stem.fact_id)
        for i, h in enumerate(p.hidden_stems):
            if h.element == day:
                roots.append({"fact_id": f"root:{p.position}:{i}", "pillar": p.position, "stem_ref": h.fact_id,
                              "stem": h.name, "level": "MAIN_QI" if i == 0 else "OTHER_QI"})
        for h in [p.stem, *p.hidden_stems]:
            if GENERATES[h.element] == day:
                resource.append(h.fact_id)
    return NatalFacts.model_validate({"roots": roots, "visible_support_refs": support, "visible_drain_refs": drain,
        "resource_refs": resource, "relations": relations_for(chart, tables),
        "distribution": [{"element": e, "visible_stems": sum(p.stem.element == e for p in chart.pillars),
                          "hidden_occurrences": sum(h.element == e for p in chart.pillars for h in p.hidden_stems)} for e in ELEMENTS]})
