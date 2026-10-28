"""Plain explanations of the date engine's decisions; no new calendar rules."""
from .time_engine import BRANCHES_ZH

VERSION = "date-explanation-v1"
GRADES = {"GOOD": "Ngày Đẹp", "NORMAL": "Ngày Bình Thường", "BAD": "Ngày Xấu"}
BLOCKS = {"SAT_CHU": "Sát Chủ", "THO_TU": "Thọ Tử", "NGUYET_PHA": "Nguyệt Phá",
          "NGUYET_PHA_V2": "Nguyệt Phá", "ACTIVITY_DAY_JI": "lịch ngày kỵ việc đã chọn",
          "ACTIVITY_HOUR_JI": "lịch giờ kỵ việc đã chọn"}
BANDS = {"PRIMARY": "Dụng thần", "HY": "Hỷ thần", "KY": "Kỵ thần", "NEUTRAL": "trung tính"}


def period_label(row):
    def clock(value):
        return value[11:16] if value[17:19] == "00" else value[11:19]
    end = "24:00" if row["end_at"][:10] != row["start_at"][:10] else clock(row["end_at"])
    return clock(row["start_at"]) + "–" + end


def explain_day(result, scoring):
    """The complete, single-day result is the only source of interpretive facts."""
    day = result["days"][0]
    day_only = result["evaluation_mode"] == "DAY_ONLY"
    rows = day["day_periods"] if day_only else day["windows"]
    # Same ordering as DateEngine.rank, including stable chronological ties.
    best = max(rows, key=lambda w: ({"GOOD": 3, "NORMAL": 2, "BAD": 1, None: 0}[w["grade"]],
                                  w["score"] if w["score"] is not None else -1, w["duration_seconds"]))
    roles = {p["subject_id"]: p["role"] for p in result["subject_summaries"]}
    noun = "khoảng hiệu lực đánh giá ngày" if day_only else "khung giờ bắt đầu"
    good = [w for w in rows if w["grade"] == "GOOD"]
    date = "/".join(reversed(day["date"].split("-")))
    activity = result["activity_name"].lower()
    if day["grade"] == "GOOD":
        summary = f"Ngày {date} có {len(good)} {noun} đạt mức Ngày Đẹp cho {activity}. Điểm nổi bật nằm ở {period_label(best)} (Giờ Việt Nam), đạt {best['score']}/100 điểm."
    elif day["grade"] is None:
        summary = f"Ngày {date} chưa đủ dữ liệu để kết luận phù hợp với {activity}; hiện chưa có {noun} được khuyến nghị."
    else:
        summary = f"Ngày {date} chưa có {noun} đạt mức Ngày Đẹp cho {activity}. Khoảng được xếp cao nhất là {period_label(best)} (Giờ Việt Nam), ở mức {GRADES[day['grade']]} ({best['score']}/100 điểm)."
    reasons, cautions = [], []
    status = best["day_activity_status"]
    reasons.append({"SUPPORTED": f"Lịch ngày có mục nên làm phù hợp với việc {activity}.",
                    "AVOID": f"Lịch ngày ghi kỵ việc {activity}; đây là điều kiện loại trừ, điểm số không bù được.",
                    "NOT_LISTED": f"Lịch ngày không đề cập việc {activity}; thiếu căn cứ này không được xem là thuận.",
                    "UNRESOLVED": f"Dữ liệu nên/kỵ theo ngày cho việc {activity} đang mâu thuẫn; cần để ngỏ kết luận."}[status])
    if not day_only:
        reasons.append({"SUPPORTED": "Lịch giờ cũng có mục nên làm phù hợp với việc đã chọn.",
                        "AVOID": "Lịch giờ kỵ việc đã chọn nên khung này bị loại trừ.",
                        "NOT_LISTED": "Lịch giờ không đề cập việc đã chọn; phần điểm thiếu này đã được trừ.",
                        "UNRESOLVED": "Dữ liệu nên/kỵ theo giờ đang mâu thuẫn nên chưa thể kết luận."}[best["hour_activity_status"]])
    for p in best["subject_assessments"]:
        role = roles[p["subject_id"]]
        positions = ["Can ngày", "Chi ngày"] if day_only else ["Can ngày", "Can giờ", "Chi ngày", "Chi giờ"]
        parts = [f"{position} {element} ({BANDS[band]})" for position, element, band in zip(positions, p["elements"], p["element_bands"])]
        text = f"{role}: hành của {'ngày' if day_only else 'ngày và giờ'} được đối chiếu là " + ", ".join(parts) + f"; trừ {p['penalty']} điểm theo bảng đối chiếu hồ sơ."
        if p["clashing_natal_branch_indices"]:
            text += " Chi ngày xung với chi năm/ngày sinh " + ", ".join(BRANCHES_ZH[i] for i in p["clashing_natal_branch_indices"]) + "."
        if p["status"] == "UNSTABLE_BIRTH":
            text += " Sai số giờ sinh có thể làm đổi trụ nên chưa chốt kết quả."
        reasons.append(text)
    if best["assessment_state"] == "UNRESOLVED":
        cautions.append("Điểm thô chỉ để kiểm tra phép tính; không dùng để khuyến nghị khi kết quả còn chưa rõ.")
    if best["hard_exclusions"]:
        def block_name(code):
            if code.startswith("NATAL_CLASH:"):
                return "xung chi năm/ngày sinh của " + roles.get(code.split(":", 1)[1], "đương sự").lower()
            return BLOCKS.get(code, code)
        cautions.append("Điều kiện loại trừ tại khoảng này: " + "; ".join(block_name(c) for c in best["hard_exclusions"]) + ". Không cộng bù bằng điểm.")
    if len(roles) == 2:
        reasons.append("Hai hồ sơ được xét riêng. Điểm đối chiếu lấy mức trừ lớn hơn, không lấy trung bình để che đi hồ sơ kém phù hợp.")
    deducted = [p for p in best["penalties"] if p["points"]]
    formula = " + ".join(str(p["points"]) for p in deducted) or "0"
    reasons.append(f"Cách tính: {scoring['base']} − ({formula}), giới hạn trong 0–100, được {best['raw_score']} điểm thô; ngưỡng Ngày Đẹp là {scoring['good_threshold']}. Mức Ngày Đẹp còn cần lịch ngày và hồ sơ đạt điều kiện"
                   + (", cùng lịch giờ phù hợp" if result["activity_spec"]["hour_evaluation_mode"] == "DIRECT_YI_JI" else "") + ".")
    for p in deducted:
        if p["rule_id"] != "PERSONAL_ELEMENTS":
            reasons.append(f"Trừ {p['points']} điểm: {p['message']}")
    cautions += [w["message"] for w in best["rule_warnings"]]
    if day_only:
        cautions.append("Các khoảng trên chỉ là phạm vi hiệu lực của đánh giá ngày; tính năng này chưa chọn giờ đẹp cho việc này.")
    else:
        cautions.append("Kết luận áp dụng cho giờ bắt đầu trong các khung được khuyến nghị, không áp dụng cho toàn bộ ngày.")
    if day["has_unresolved_windows"]:
        cautions.append("Trong ngày vẫn có khoảng chưa đủ dữ liệu kết luận; chỉ dùng các khoảng đã được khuyến nghị.")
    return {"version": VERSION, "summary": summary, "focus_start_at": best["start_at"],
            "focus_end_at": best["end_at"], "reasons": reasons, "cautions": list(dict.fromkeys(cautions))}
