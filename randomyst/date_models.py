"""Versioned contracts for date selection, separate from number generation."""
from datetime import date, time
from typing import Literal

from pydantic import Field, model_validator

from .models import Birth, StrictModel
from .date_activities import Activity, BY_ACTIVITY, GROUPS, REGISTRY_VERSION


class DateSubject(StrictModel):
    subject_id: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    birth: Birth


class DateRange(StrictModel):
    start: date
    end: date

    @model_validator(mode="after")
    def valid_range(self):
        if self.start > self.end or (self.end - self.start).days >= 93:
            raise ValueError("Khoảng tra phải từ 1 đến 93 ngày.")
        if self.start < date(2024, 1, 1) or self.end > date(2030, 12, 31):
            raise ValueError("Khoảng tra nằm trong 2024–2030 theo UTC+7.")
        return self


class AllowedHours(StrictModel):
    start: time = time(0)
    end: time | None = None  # null means the next midnight, end exclusive

    @model_validator(mode="after")
    def valid_hours(self):
        if self.start.tzinfo or (self.end is not None and (self.end.tzinfo or self.start >= self.end)):
            raise ValueError("Khung giờ UTC+7 phải có giờ bắt đầu trước giờ kết thúc.")
        if self.start.microsecond or (self.end is not None and self.end.microsecond):
            raise ValueError("Khung giờ nhận độ phân giải giây.")
        return self


class DateSearchRequest(StrictModel):
    activity: Activity
    subjects: list[DateSubject] = Field(min_length=1, max_length=2)
    date_range: DateRange
    allowed_weekdays: list[int] = Field(default_factory=lambda: list(range(7)), min_length=1, max_length=7)
    allowed_hours: AllowedHours = Field(default_factory=AllowedHours)
    include_details: bool = False

    @model_validator(mode="after")
    def scope(self):
        spec = BY_ACTIVITY[self.activity]
        if not spec["enabled"]:
            raise ValueError("Việc này chưa được bật: " + spec["name"])
        required = spec["subject_count"]
        if len(self.subjects) != required:
            raise ValueError(f"{spec['name']} cần {required} hồ sơ người đứng việc.")
        if spec["hour_evaluation_mode"] == "DAY_ONLY" and (self.allowed_hours.start != time(0) or self.allowed_hours.end is not None):
            raise ValueError("Việc này chỉ xét ngày; không nhận bộ lọc giờ tổ chức.")
        if len({s.subject_id for s in self.subjects}) != required:
            raise ValueError("Mã chủ thể phải khác nhau.")
        if len(set(self.allowed_weekdays)) != len(self.allowed_weekdays) or any(type(x) is not int or not 0 <= x <= 6 for x in self.allowed_weekdays):
            raise ValueError("Ngày trong tuần dùng 0=Thứ Hai đến 6=Chủ Nhật, không trùng.")
        return self


class DateSource(StrictModel):
    source_id: str
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    url: str
    basis: str


class RuleWhen(StrictModel):
    fact: Literal["calendar_class", "day_relation", "ambient_support", "year_clash", "sat_chu", "tho_tu", "nguyet_pha", "tam_nuong"]
    equals: str | bool


class DateRule(StrictModel):
    rule_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    enabled: bool
    when: RuleWhen
    activity_scope: list[Activity] = Field(min_length=1, max_length=21)
    subject_scope: Literal["GENERAL"] = "GENERAL"
    effect: Literal["PENALTY", "BLOCK", "WARN"]
    points: int | None = Field(default=None, ge=0, le=100)
    dedupe_group: str
    message: str
    source_id: str
    review_status: Literal["PINNED_SOFTWARE", "PRODUCT_POLICY", "NOT_ENABLED"]

    @model_validator(mode="after")
    def effect_points(self):
        if (self.effect == "PENALTY") != (self.points is not None):
            raise ValueError("Chỉ PENALTY có points; BLOCK/WARN dùng null.")
        if not self.enabled and self.review_status != "NOT_ENABLED":
            raise ValueError("Luật tắt phải ghi NOT_ENABLED.")
        allowed = {"calendar_class": {"HAC_DAO", "HOANG_DAO"},
                   "day_relation": {"SAME", "STEM_GENERATES_BRANCH", "BRANCH_GENERATES_STEM", "STEM_CONTROLS_BRANCH", "BRANCH_CONTROLS_STEM"},
                   "ambient_support": {"NONE", "PAIR", "FULL"}}
        if self.when.fact in allowed:
            if type(self.when.equals) is not str or self.when.equals not in allowed[self.when.fact]:
                raise ValueError("Giá trị điều kiện không hợp lệ.")
        elif type(self.when.equals) is not bool:
            raise ValueError("Điều kiện đối chiếu dùng Boolean.")
        return self


class ActivitySpec(StrictModel):
    activity: Activity
    name: str
    provider_token: str
    subject_count: Literal[1, 2]
    group_id: str
    provider_hour_token: str | None
    subject_roles: list[str] = Field(min_length=1, max_length=2)
    hour_evaluation_mode: Literal["LEGACY_V1", "DIRECT_YI_JI", "DAY_ONLY"]
    rule_profile: Literal["LEGACY_V1", "CONSTRUCTIVE_V2", "RITUAL_V2", "DEFERRED"]
    event_anchor: str
    scope_note: str
    enabled: bool
    tier: Literal["CORE", "CONTEXTUAL"]
    review_status: Literal["PRODUCT_POLICY", "NOT_ENABLED"]


class ActivityGroup(StrictModel):
    group_id: str
    name: str


class DateScoring(StrictModel):
    base: int = Field(ge=0, le=100)
    good_threshold: int = Field(ge=1, le=100)
    normal_threshold: int = Field(ge=0, le=99)
    day_not_listed_penalty: int = Field(ge=0, le=100)
    hour_not_listed_penalty: int = Field(ge=0, le=100)
    personal_element_penalties: dict[Literal["PRIMARY", "HY", "NEUTRAL", "KY"], int]
    personal_clash_blocks: bool

    @model_validator(mode="after")
    def thresholds(self):
        if self.normal_threshold >= self.good_threshold:
            raise ValueError("Ngưỡng bình thường phải thấp hơn ngưỡng đẹp.")
        if set(self.personal_element_penalties) != {"PRIMARY", "HY", "NEUTRAL", "KY"} or any(not 0 <= x <= 25 for x in self.personal_element_penalties.values()):
            raise ValueError("Cần đủ bốn mức phạt hành, trong 0–25.")
        return self


class MonthTables(StrictModel):
    sat_chu: list[int] = Field(min_length=12, max_length=12)
    tho_tu: list[int] = Field(min_length=12, max_length=12)
    nguyet_pha: list[int] = Field(min_length=12, max_length=12)

    @model_validator(mode="after")
    def indices(self):
        if any(type(i) is not int or not 0 <= i < 12 for row in (self.sat_chu, self.tho_tu, self.nguyet_pha) for i in row):
            raise ValueError("Target CHI dùng index 0–11.")
        return self


class DateRules(StrictModel):
    schema_version: Literal["date-rules-v2"]
    rules_version: str
    provider_version: Literal["1.4.8"]
    calendar_policy: Literal["BEIJING_CIVIL_UTC8"]
    major_taboo_basis: Literal["CANDIDATE_EXACT_JIE_MONTH_AND_SECT1_DAY"]
    disabled_rules: list[str]
    sources: list[DateSource]
    activity_registry_version: Literal["major-events-2026-10-25-v2"]
    groups: list[ActivityGroup] = Field(min_length=7, max_length=7)
    activities: list[ActivitySpec] = Field(min_length=21, max_length=21)
    month_tables: MonthTables
    scoring: DateScoring
    day_scoring: DateScoring
    rules: list[DateRule] = Field(min_length=1)

    @model_validator(mode="after")
    def references(self):
        ids = [x.rule_id for x in self.rules]
        sources = [x.source_id for x in self.sources]
        if len(set(ids)) != len(ids) or len(set(sources)) != len(sources):
            raise ValueError("Mã rule/source không trùng.")
        if {x.activity: x.model_dump() for x in self.activities} != BY_ACTIVITY or len({x.activity for x in self.activities}) != len(self.activities):
            raise ValueError("Registry hoạt động khác policy đã ghim.")
        if [x.model_dump() for x in self.groups] != GROUPS or self.activity_registry_version != REGISTRY_VERSION:
            raise ValueError("Nhóm/phiên bản registry không khớp.")
        if any(x.source_id not in sources for x in self.rules if x.enabled):
            raise ValueError("Luật bật cần source.")
        if set(self.disabled_rules) != {x.rule_id for x in self.rules if not x.enabled}:
            raise ValueError("Danh sách luật chưa bật không khớp.")
        if any(len(set(r.activity_scope)) != len(r.activity_scope) or any(not BY_ACTIVITY[a]["enabled"] for a in r.activity_scope) for r in self.rules):
            raise ValueError("Scope luật trùng hoặc chứa việc chưa bật.")
        return self


class RecommendedWindow(StrictModel):
    """Every GOOD interval, in chronological order, without bulky evidence."""
    start_at: str
    end_at: str
    hour_branch: Literal["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


class DateWindow(RecommendedWindow):
    duration_seconds: float = Field(gt=0)
    calendar_class: Literal["HOANG_DAO", "HAC_DAO"]
    day_officer: str
    tian_shen: str
    civil_day_ganzhi: str
    bazi_day_ganzhi: str
    month_ganzhi_exact: str
    lunar: dict
    day_activity_status: Literal["SUPPORTED", "AVOID", "NOT_LISTED", "UNRESOLVED"]
    hour_activity_status: Literal["SUPPORTED", "AVOID", "NOT_LISTED", "UNRESOLVED"]
    assessment_state: Literal["COMPLETE", "UNRESOLVED"]
    score: int | None = Field(ge=0, le=100)
    raw_score: int = Field(ge=0, le=100)
    grade: Literal["GOOD", "NORMAL", "BAD"] | None
    hard_exclusions: list[str]
    penalties: list[dict]
    subject_assessments: list[dict]
    facts: dict
    rule_warnings: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def decision(self):
        if self.assessment_state == "UNRESOLVED" and (self.score is not None or self.grade is not None):
            raise ValueError("Chưa đủ kết luận phải có score/grade null.")
        if self.assessment_state == "COMPLETE" and self.hard_exclusions and (self.score != 0 or self.grade != "BAD"):
            raise ValueError("Luật cấm không được bù bằng điểm.")
        return self


class DayPeriod(StrictModel):
    """Validity interval for a day assessment, never a recommended hour."""
    start_at: str
    end_at: str


class DayAssessment(DayPeriod):
    duration_seconds: float = Field(gt=0)
    calendar_class: Literal["HOANG_DAO", "HAC_DAO"]
    day_officer: str
    tian_shen: str
    civil_day_ganzhi: str
    bazi_day_ganzhi: str
    month_ganzhi_exact: str
    lunar: dict
    day_activity_status: Literal["SUPPORTED", "AVOID", "NOT_LISTED", "UNRESOLVED"]
    assessment_state: Literal["COMPLETE", "UNRESOLVED"]
    score: int | None = Field(ge=0, le=100)
    raw_score: int = Field(ge=0, le=100)
    grade: Literal["GOOD", "NORMAL", "BAD"] | None
    hard_exclusions: list[str]
    penalties: list[dict]
    subject_assessments: list[dict]
    facts: dict
    rule_warnings: list[dict]

    @model_validator(mode="after")
    def decision(self):
        if self.assessment_state == "UNRESOLVED" and (self.score is not None or self.grade is not None):
            raise ValueError("Chưa đủ kết luận phải có score/grade null.")
        if self.assessment_state == "COMPLETE" and self.hard_exclusions and (self.score != 0 or self.grade != "BAD"):
            raise ValueError("Luật cấm không được bù bằng điểm.")
        return self


class DateDay(StrictModel):
    date: str
    grade: Literal["GOOD", "NORMAL", "BAD"] | None
    assessment_state: Literal["COMPLETE", "UNRESOLVED", "FILTERED"]
    score: int | None = Field(ge=0, le=100)
    windows: list[DateWindow]
    recommended_windows: list[RecommendedWindow]
    evaluated_windows: int = Field(ge=0)
    recommended_minutes: float = Field(ge=0, le=1440)
    has_unresolved_windows: bool
    day_periods: list[DayAssessment]
    recommended_day_periods: list[DayPeriod]
    evaluated_periods: int = Field(ge=0)
    hour_evaluation: Literal["NOT_SUPPORTED", "NOT_EVALUATED", "HAS_RECOMMENDATIONS", "EVALUATED_NO_MATCH"]

    @model_validator(mode="after")
    def capability(self):
        if self.hour_evaluation == "NOT_SUPPORTED" and (self.windows or self.recommended_windows or self.evaluated_windows or self.recommended_minutes):
            raise ValueError("Chỉ xét ngày không được trả giờ đẹp.")
        if bool(self.recommended_windows) != (self.hour_evaluation == "HAS_RECOMMENDATIONS"):
            raise ValueError("Trạng thái giờ không khớp danh sách giờ đẹp.")
        if self.hour_evaluation != "NOT_SUPPORTED" and (self.day_periods or self.recommended_day_periods or self.evaluated_periods):
            raise ValueError("Khoảng hiệu lực ngày chỉ dùng cho chế độ xét ngày.")
        return self


class DateSearchResponse(StrictModel):
    schema_version: Literal["date-search-response-v2"]
    date_rules_version: str
    calendar_policy: Literal["BEIJING_CIVIL_UTC8"]
    activity: Activity
    activity_name: str
    disabled_rules: list[str]
    coverage_note: str
    subject_summaries: list[dict]
    days: list[DateDay]
    evaluated_windows: int
    personal_comparisons: int
    natal_analysis_count: int
    sources: list[DateSource]
    warnings: list[dict]
    activity_registry_version: str
    activity_spec: ActivitySpec
    evaluation_mode: Literal["DAY_ONLY", "DAY_AND_HOUR"]
    evaluated_periods: int = Field(ge=0)

    @model_validator(mode="after")
    def scope_and_counts(self):
        spec = self.activity_spec
        if spec.activity != self.activity or not spec.enabled or spec.name != self.activity_name:
            raise ValueError("Kết quả không khớp việc đã chọn.")
        expected_mode = "DAY_ONLY" if spec.hour_evaluation_mode == "DAY_ONLY" else "DAY_AND_HOUR"
        if self.evaluation_mode != expected_mode:
            raise ValueError("Chế độ đánh giá khác capability của việc.")
        if len(self.subject_summaries) != spec.subject_count or self.natal_analysis_count != spec.subject_count:
            raise ValueError("Số hồ sơ không khớp việc.")
        if self.evaluated_windows != sum(d.evaluated_windows for d in self.days) or self.evaluated_periods != sum(d.evaluated_periods for d in self.days):
            raise ValueError("Tổng lượt đánh giá không khớp ngày.")
        if self.personal_comparisons != (self.evaluated_windows+self.evaluated_periods)*spec.subject_count:
            raise ValueError("Tổng đối chiếu cá nhân không khớp.")
        if any(d.assessment_state != "FILTERED" and (d.hour_evaluation == "NOT_SUPPORTED") != (self.evaluation_mode == "DAY_ONLY") for d in self.days):
            raise ValueError("Trạng thái ngày khác chế độ đánh giá.")
        return self
