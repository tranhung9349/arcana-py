"""Numeric decision branches ported from pinned tinix-bazi ngu_hanh.js.

Only the numeric/structure/useful-god decisions are ported, not career/health prose.
Pillars are supplied by 6tail's Beijing clock and sect 1, not the upstream calculator.
"""
from .sampling import ELEMENTS, GENERATES, CONTROLS
from .time_engine import BRANCHES, BRANCH_ELEMENTS, STEMS

SOURCE_COMMIT = "80ff4463d0397c1b11db76f38d880255f55558bc"
SOURCE_PATH = "backendjs/src/bazi/phan_tich/ngu_hanh.js"
STEM_ELEMENTS = tuple(e for e in ELEMENTS for _ in range(2))
JIAN_LU = (2, 3, 5, 6, 5, 6, 8, 9, 11, 0)
PARENT = {v: k for k, v in GENERATES.items()}
CONTROLLER = {v: k for k, v in CONTROLS.items()}


def deity(day, other):
    first, second = STEM_ELEMENTS[day], STEM_ELEMENTS[other]
    same = day % 2 == other % 2
    if first == second:
        return "Tỷ" if same else "Kiếp"
    if GENERATES[first] == second:
        return "Thực" if same else "Thương"
    if GENERATES[second] == first:
        return "Kiêu" if same else "Ấn"
    if CONTROLS[first] == second:
        return "Tài+" if same else "Tài-"
    return "Sát" if same else "Quan"


def structure(day, month_gan, month_zhi):
    if JIAN_LU[day] == month_zhi:
        return "Kiến Lộc Cách/Nguyệt Kiếp"
    name = deity(day, month_gan)
    # Preserve the repo's Tài+/Tài- -> Chính Tài and empty-pattern -> Sát decisions.
    mapping = {"Sát": "Thất Sát", "Quan": "Chính Quan", "Ấn": "Chính Ấn", "Kiêu": "Thiên Ấn",
               "Thực": "Thực Thần", "Thương": "Thương Quan", "Tài+": "Chính Tài", "Tài-": "Chính Tài"}
    return mapping.get(name, "Sát") + " Cách"


def analyze(gans, zhis):
    if len(gans) != 4 or len(zhis) != 4 or any(type(x) is not int or not 0 <= x < 10 for x in gans) or any(type(x) is not int or not 0 <= x < 12 for x in zhis):
        raise ValueError("Four valid stem and branch indices required")
    day = STEM_ELEMENTS[gans[2]]
    resource, output, wealth, officer = PARENT[day], GENERATES[day], CONTROLS[day], CONTROLLER[day]
    supported = BRANCH_ELEMENTS[zhis[1]] in (day, resource)
    scores = dict.fromkeys(("self", "resource", "output", "wealth", "officer"), 0)
    categories = {day: "self", resource: "resource", output: "output", wealth: "wealth", officer: "officer"}
    for i, stem in enumerate(gans):
        if i != 2:
            scores[categories[STEM_ELEMENTS[stem]]] += 8
    for i, branch in enumerate(zhis):
        scores[categories[BRANCH_ELEMENTS[branch]]] += 40 if i == 1 else 16 if i == 2 else 10
    support = scores["self"] + scores["resource"]
    oppose = scores["output"] + scores["wealth"] + scores["officer"]
    special = False
    if support >= 82:
        special, pattern = True, "Tòng Vượng Cách"
    elif support <= 12 and not supported:
        special = True
        largest = max(scores["wealth"], scores["officer"], scores["output"])
        pattern = "Tòng Tài Cách" if largest == scores["wealth"] else "Tòng Sát Cách" if largest == scores["officer"] else "Tòng Nhi Cách"
    else:
        pattern = structure(gans[2], gans[1], zhis[1])
    strong = not special and ((support >= 35 and oppose < 65) if supported else support > 50)
    if special:
        if pattern == "Tòng Vượng Cách":
            dung, hy, ky, reason = [day, resource], [output], [wealth, officer], "FOLLOW_STRONG"
        elif pattern == "Tòng Tài Cách":
            dung, hy, ky, reason = [wealth], [output], [resource, day], "FOLLOW_WEALTH"
        elif pattern == "Tòng Sát Cách":
            dung, hy, ky, reason = [officer], [wealth], [resource, day, output], "FOLLOW_OFFICER"
        else:
            dung, hy, ky, reason = [output], [day, wealth], [resource, officer], "FOLLOW_OUTPUT"
    elif strong:
        if scores["resource"] > scores["self"]:
            dung, hy, ky, reason = [wealth], [output], [resource, day], "STRONG_RESOURCE"
        elif scores["officer"] > 10:
            dung, hy, ky, reason = [officer], [wealth], [resource, day, output], "STRONG_SELF_OFFICER"
        else:
            dung, hy, ky, reason = [output], [wealth], [resource, officer], "STRONG_SELF_OUTPUT"
    elif scores["officer"] >= scores["wealth"]:
        dung, hy, ky, reason = [resource], [day], [wealth, output], "WEAK_OFFICER"
    elif scores["wealth"] > scores["output"]:
        dung, hy, ky, reason = [day], [resource], [output, officer], "WEAK_WEALTH"
    else:
        dung, hy, ky, reason = [resource], [day], [wealth], "WEAK_OUTPUT"
    dieu_hau = "Hỏa" if zhis[1] in (11, 0, 1) else "Thủy" if zhis[1] in (5, 6, 7) else None
    if dieu_hau and dieu_hau not in dung + hy and not (special and dieu_hau in ky):
        hy.append(dieu_hau)
    return {"dung_than": list(dict.fromkeys(dung)), "hy_than": list(dict.fromkeys(hy)), "ky_than": list(dict.fromkeys(ky)),
            "primary_dung_than": dung[0], "reason_code": reason, "structure": pattern,
            "strength": ("Cực Vượng (Ngoại cách)" if "Vượng" in pattern else "Cực Nhược (Ngoại cách)") if special else ("Thân Vượng (Nội cách)" if strong else "Thân Nhược (Nội cách)"),
            "scores": scores, "total_support": support, "total_oppose": oppose, "month_support": supported,
            "dieu_hau": dieu_hau, "source": {"repository": "vhphuoc1102/tinix-bazi", "commit": SOURCE_COMMIT, "path": SOURCE_PATH,
                "url": f"https://github.com/vhphuoc1102/tinix-bazi/blob/{SOURCE_COMMIT}/{SOURCE_PATH}", "implementation": "numeric-python-port-v1"}}


THIEN_AT = ((7,1), (8,0), (9,11), (9,11), (7,1), (8,0), (7,1), (2,6), (3,5), (3,5))
VAN_XUONG = (5, 6, 8, 9, 8, 9, 11, 0, 2, 1)
# Tuples explicitly distinguish stem targets and branch targets.
THIEN_DUC = (("branch",5), ("stem",6), ("stem",3), ("branch",8), ("stem",8), ("stem",7),
             ("branch",11), ("stem",0), ("stem",9), ("branch",2), ("stem",2), ("stem",1))


def star_bonuses(gans, zhis, casting_month_branch):
    matches = []
    for name, targets in (("Thiên Ất", THIEN_AT[gans[2]]), ("Văn Xương", (VAN_XUONG[gans[2]],))):
        found = sorted(set(targets).intersection(zhis))
        if found:
            matches.append({"name": name, "target_type": "branch", "matched_tokens": [BRANCHES[i] for i in found],
                            "matched_elements": sorted({BRANCH_ELEMENTS[i] for i in found})})
    kind, target = THIEN_DUC[casting_month_branch]
    if target in (gans if kind == "stem" else zhis):
        matches.append({"name": "Thiên Đức", "target_type": kind, "matched_tokens": [STEMS[target] if kind == "stem" else BRANCHES[target]],
                        "matched_elements": [STEM_ELEMENTS[target] if kind == "stem" else BRANCH_ELEMENTS[target]]})
    counts = {e: sum(e in star["matched_elements"] for star in matches) for e in ELEMENTS}
    deltas = {e: (0 if n == 0 else 0.20 + (0.10 if n >= 2 else 0) + max(0, n-2)*0.05) for e, n in counts.items()}
    return {"active_stars": matches, "delta_by_element": deltas, "source_commit": SOURCE_COMMIT,
            "policy": "day-stem Thien At/Van Xuong; casting-Jie-month Thien Duc matched against natal pillars"}
