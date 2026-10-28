"""Deterministic date search. Exactly one natal analyze call per subject/request."""
from datetime import timedelta

from .bazi import analyze, STEM_ELEMENTS
from .date_calendar import DateCalendar
from .date_rules import RuleEvaluator, activity_status
from .time_engine import BRANCH_ELEMENTS, BRANCHES_ZH, pillars


class DateEngine:
    def __init__(self):
        self.calendar = DateCalendar()
        self.evaluator = RuleEvaluator()

    def profile(self, subject):
        natal = pillars(subject.birth.civil_datetime)
        analysis = analyze(natal["gans"], natal["zhis"])
        primary = subject.birth.override_dung_than or analysis["primary_dung_than"]
        boundary = self.calendar.birth_boundary_warning(subject.birth)
        return {"subject_id": subject.subject_id, "primary": primary, "calculated_primary": analysis["primary_dung_than"],
                "overridden": subject.birth.override_dung_than is not None,
                "hy": tuple(analysis["hy_than"]), "ky": tuple(analysis["ky_than"]),
                "natal_branches": tuple(natal["zhis"]), "pillars": natal["pillars"], "birth_boundary": boundary}

    def personal(self, profile, facts, day_only=False):
        sc = self.evaluator.config.day_scoring if day_only else self.evaluator.config.scoring
        indices = (2,) if day_only else (2, 3)
        elements = [STEM_ELEMENTS[facts["gans"][i]] for i in indices] + [BRANCH_ELEMENTS[facts["zhis"][i]] for i in indices]
        bands = ["PRIMARY" if e == profile["primary"] else "KY" if e in profile["ky"] else "HY" if e in profile["hy"] else "NEUTRAL" for e in elements]
        # Override wins only for its selected element; derived Hy/Ky are preserved.
        penalty = sum(sc.personal_element_penalties[b] for b in bands)
        clashes = sorted({n for n in (profile["natal_branches"][0], profile["natal_branches"][2]) if (facts["zhis"][2] - n) % 12 == 6})
        state = "UNSTABLE_BIRTH" if profile["birth_boundary"] == "UNSTABLE" else "CLASH" if clashes else "TENSION" if "KY" in bands else "SUPPORTED"
        return {"subject_id": profile["subject_id"], "status": state, "penalty": penalty,
                "elements": elements, "element_bands": bands, "clashing_natal_branch_indices": clashes,
                "blocked": bool(clashes) and sc.personal_clash_blocks}

    def window(self, start, end, activity, profiles):
        return self.assessment(start, end, activity, profiles, day_only=False)

    def day_period(self, start, end, activity, profiles):
        return self.assessment(start, end, activity, profiles, day_only=True)

    def assessment(self, start, end, activity, profiles, day_only):
        facts = self.calendar.at(start)
        rules, context = self.evaluator.evaluate(facts, activity)
        spec = self.evaluator.activities[activity]
        day_status = activity_status(facts["civil_day"]["yi"], facts["civil_day"]["ji"], spec.provider_token)
        hour_status = None if day_only else activity_status(facts["civil_hour"]["yi"], facts["civil_hour"]["ji"], spec.provider_hour_token)
        people = [self.personal(p, facts, day_only=day_only) for p in profiles]
        blocks = [r["rule_id"] for r in rules if r["effect"] == "BLOCK"]
        if day_status == "AVOID": blocks.append("ACTIVITY_DAY_JI")
        if hour_status == "AVOID": blocks.append("ACTIVITY_HOUR_JI")
        blocks.extend("NATAL_CLASH:" + p["subject_id"] for p in people if p["blocked"])
        unresolved = day_status == "UNRESOLVED" or hour_status == "UNRESOLVED" or any(p["status"] == "UNSTABLE_BIRTH" for p in people)
        sc = self.evaluator.config.day_scoring if day_only else self.evaluator.config.scoring
        penalties = [r for r in rules if r["effect"] == "PENALTY"]
        if day_status == "NOT_LISTED": penalties.append({"rule_id": "DAY_NOT_LISTED", "points": sc.day_not_listed_penalty, "message": "Lịch ngày không đề cập việc đã chọn.", "source_id": "6TAIL_CORPUS"})
        if hour_status == "NOT_LISTED": penalties.append({"rule_id": "HOUR_NOT_LISTED", "points": sc.hour_not_listed_penalty, "message": "Lịch giờ không đề cập việc đã chọn.", "source_id": "6TAIL_CORPUS"})
        worst = max(p["penalty"] for p in people)
        penalties.append({"rule_id": "PERSONAL_ELEMENTS", "points": worst, "message": "Mức phạt hành của chủ thể có điểm thấp nhất; Dụng Thần nhập đè có ưu tiên.", "source_id": "PRODUCT_PERSONAL_POLICY"})
        raw_score = max(0, min(100, sc.base - sum(p["points"] for p in penalties)))
        if unresolved:
            grade, score, state = None, None, "UNRESOLVED"
        elif blocks:
            grade, score, state = "BAD", 0, "COMPLETE"
        else:
            score, state = raw_score, "COMPLETE"
            eligible = day_status == "SUPPORTED" and all(p["status"] == "SUPPORTED" for p in people)
            if spec.hour_evaluation_mode == "DIRECT_YI_JI":
                eligible = eligible and hour_status == "SUPPORTED"
            grade = "GOOD" if score >= sc.good_threshold and eligible else "NORMAL" if score >= sc.normal_threshold else "BAD"
        result = {"start_at": start.isoformat(), "end_at": end.isoformat(), "duration_seconds": (end-start).total_seconds(),
                "calendar_class": facts["calendar_class"], "day_officer": facts["civil_day"]["day_officer"], "tian_shen": facts["civil_day"]["tian_shen"],
                "civil_day_ganzhi": facts["civil_day_ganzhi"], "bazi_day_ganzhi": facts["bazi_day_ganzhi"],
                "month_ganzhi_exact": facts["pillars_zh"][1], "lunar": facts["civil_day"]["lunar"],
                "day_activity_status": day_status,
                "assessment_state": state, "score": score, "raw_score": raw_score, "grade": grade,
                "hard_exclusions": sorted(set(blocks)), "penalties": penalties, "subject_assessments": people,
                "rule_warnings": [r for r in rules if r["effect"] == "WARN"],
                "facts": {**context, "day_yi": facts["civil_day"]["yi"], "day_ji": facts["civil_day"]["ji"]}}
        if not day_only:
            result.update(hour_branch=BRANCHES_ZH[facts["zhis"][3]], hour_activity_status=hour_status)
            result["facts"].update(hour_yi=facts["civil_hour"]["yi"], hour_ji=facts["civil_hour"]["ji"])
        return result

    @staticmethod
    def rank(window):
        return ({"GOOD": 3, "NORMAL": 2, "BAD": 1, None: 0}[window["grade"]],
                window["score"] if window["score"] is not None else -1, window["duration_seconds"])

    def search(self, request):
        profiles = tuple(self.profile(subject) for subject in request.subjects)
        spec = self.evaluator.activities[request.activity]
        day_only = spec.hour_evaluation_mode == "DAY_ONLY"
        # Nothing below this line initializes or re-analyzes a natal chart.
        days, evaluated = [], 0
        current = request.date_range.start
        while current <= request.date_range.end:
            if current.weekday() not in request.allowed_weekdays:
                days.append({"date": str(current), "grade": None, "assessment_state": "FILTERED", "score": None,
                             "windows": [], "recommended_windows": [], "evaluated_windows": 0, "recommended_minutes": 0, "has_unresolved_windows": False,
                             "day_periods": [], "recommended_day_periods": [], "evaluated_periods": 0, "hour_evaluation": "NOT_EVALUATED"})
            else:
                intervals = self.calendar.day_intervals(current) if day_only else self.calendar.intervals(current, request.allowed_hours)
                evaluate = self.day_period if day_only else self.window
                windows = [evaluate(start, end, request.activity, profiles) for start, end in intervals]
                evaluated += len(windows)
                ordered = sorted(windows, key=self.rank, reverse=True)  # stable: earlier time wins final ties
                best = ordered[0]
                recommended = [w for w in windows if w["grade"] == "GOOD"]
                days.append({"date": str(current), "grade": best["grade"], "assessment_state": best["assessment_state"],
                             "score": best["score"], "windows": [] if day_only else windows if request.include_details else ordered[:3],
                             "recommended_windows": [] if day_only else [{key: w[key] for key in ("start_at", "end_at", "hour_branch")} for w in recommended],
                             "evaluated_windows": 0 if day_only else len(windows),
                             "recommended_minutes": 0 if day_only else sum(w["duration_seconds"] for w in recommended)/60,
                             "has_unresolved_windows": any(w["assessment_state"] == "UNRESOLVED" for w in windows),
                             "day_periods": (windows if request.include_details else ordered[:3]) if day_only else [],
                             "recommended_day_periods": [{key: w[key] for key in ("start_at", "end_at")} for w in recommended] if day_only else [],
                             "evaluated_periods": len(windows) if day_only else 0,
                             "hour_evaluation": "NOT_SUPPORTED" if day_only else "HAS_RECOMMENDATIONS" if recommended else "EVALUATED_NO_MATCH"})
            current += timedelta(days=1)
        config = self.evaluator.config
        coverage = ("Đã xét ngày và hồ sơ; chưa khuyến nghị giờ. Khoảng hiệu lực có thể đổi tại ranh lịch trong ngày. Tam Nương chưa được đánh giá."
                    if day_only else "Đánh giá theo các luật đang bật; Tam Nương chưa được đánh giá. Khung giờ là giờ bắt đầu, không đại diện toàn bộ ngày.")
        return {"schema_version": "date-search-response-v2", "date_rules_version": config.rules_version,
                "calendar_policy": config.calendar_policy, "activity": request.activity,
                "activity_name": spec.name, "activity_spec": spec.model_dump(),
                "activity_registry_version": config.activity_registry_version,
                "evaluation_mode": "DAY_ONLY" if day_only else "DAY_AND_HOUR",
                "disabled_rules": config.disabled_rules,
                "coverage_note": coverage,
                "subject_summaries": [{**p, "role": spec.subject_roles[i]} for i, p in enumerate(profiles)],
                "days": days, "evaluated_windows": 0 if day_only else evaluated,
                "evaluated_periods": evaluated if day_only else 0,
                "personal_comparisons": evaluated * len(profiles), "natal_analysis_count": len(profiles),
                "sources": [x.model_dump() for x in config.sources],
                "warnings": [{"code": "BIRTH_UNCERTAINTY_UNKNOWN", "subject_id": p["subject_id"], "message": "Chưa có biên sai số giờ sinh."} for p in profiles if p["birth_boundary"] == "UNDETERMINED"]}
