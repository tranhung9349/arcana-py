"""Typed, auditable analysis attached to a saved three-coin consultation."""
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from .models import StrictModel

Topic = Literal['GENERAL', 'WEALTH', 'CAREER', 'DOCUMENT', 'PARENTS', 'CHILDREN', 'SIBLINGS', 'PARTNERSHIP']
Relative = Literal['Phụ mẫu', 'Huynh đệ', 'Tử tôn', 'Thê tài', 'Quan quỷ']


class AnalysisContext(StrictModel):
    topic: Topic = 'GENERAL'
    use_relative: Relative | None = None
    focus_line: int | None = Field(default=None, ge=1, le=6, strict=True)
    intent_mode: Literal['TOPIC_ONLY', 'COMBINED'] = 'TOPIC_ONLY'
    intent_acknowledged: bool = Field(default=False, strict=True)


class QuestionIntentRequest(StrictModel):
    question: str = Field(min_length=5, max_length=2000)
    topic: Topic = 'GENERAL'

    @model_validator(mode='after')
    def valid_question(self):
        self.question = self.question.strip()
        if len(self.question) < 5:
            raise ValueError('Câu hỏi cần ít nhất 5 ký tự sau khi bỏ khoảng trắng.')
        return self


class IntentMatch(StrictModel):
    rule_id: str
    topic: Topic
    label: str
    term: str
    disposition: Literal['INTENT', 'NEGATED', 'CONTEXT']


class IntentCandidate(StrictModel):
    topic: Topic
    label: str
    target: str
    intent_labels: list[str]
    terms: list[str]
    evidence_level: Literal['SPECIFIC_PHRASE', 'KEYWORD']


class QuestionIntent(StrictModel):
    rules_version: str
    question_sha256: str
    selected_topic: Topic
    status: Literal['MATCH', 'CONFLICT', 'MULTIPLE', 'UNRECOGNIZED']
    suggested_topic: Topic | None
    candidates: list[IntentCandidate]
    matches: list[IntentMatch]
    needs_review: bool
    message: str
    notes: list[str]


class AnalysisFinding(StrictModel):
    id: str
    rule: str
    effect: Literal['SUPPORT', 'OBSTACLE', 'CONDITION', 'CONTEXT']
    title: str
    explanation: str
    evidence: list[str] = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)


class LineAnalysis(StrictModel):
    key: str
    position: int = Field(ge=1, le=6)
    visibility: Literal['VISIBLE', 'HIDDEN']
    branch: str
    element: str
    relative: str
    month_relation: str
    day_relation: str
    seasonal_state: str
    calendar_state: Literal['SUPPORTED', 'MIXED', 'WEAK']
    calendar_summary: str
    activity: Literal['MOVING', 'DARK_ACTIVE', 'STATIC', 'DAY_CLASH_WEAK']
    flags: list[str]
    transformation: list[str]
    caveats: list[str]


class UseSelection(StrictModel):
    target: str
    reason: str
    status: Literal['SELECTED', 'PROVISIONAL', 'AMBIGUOUS']
    selected_key: str | None
    candidate_keys: list[str] = Field(min_length=1)
    hidden: bool
    calendar_representatives: list[str]
    emerging_lines: list[int]


class AnalysisRole(StrictModel):
    role: str
    element: str
    line_keys: list[str]
    active_line_keys: list[str]


class TimingCondition(StrictModel):
    line_key: str
    kind: str
    branches: list[str]
    explanation: str


class LiuYaoAnalysis(StrictModel):
    schema_version: Literal['liuyao-analysis-v1']
    session_id: UUID
    rules_version: str
    rules_sha256: str
    snapshot_sha256: str
    context: AnalysisContext
    intent: QuestionIntent | None = None
    topic_label: str
    method: Literal['DETERMINISTIC_RULES']
    selection: UseSelection
    tendency: Literal['SUPPORT_WITH_CONDITIONS', 'MIXED', 'OBSTACLES', 'UNRESOLVED']
    headline: str
    narrative: list[str] = Field(min_length=2)
    practical_questions: list[str]
    lines: list[LineAnalysis] = Field(min_length=6)
    roles: list[AnalysisRole]
    findings: list[AnalysisFinding] = Field(min_length=1)
    timing_conditions: list[TimingCondition]
    limitations: list[str]
    sources: list[dict]

    @model_validator(mode='after')
    def valid_references(self):
        keys = [row.key for row in self.lines]
        visible = [row for row in self.lines if row.visibility == 'VISIBLE']
        if len(set(keys)) != len(keys) or len(visible) != 6 or {row.position for row in visible} != set(range(1, 7)):
            raise ValueError('Analysis requires exactly six distinct visible lines')
        if any(row.key != ('L' if row.visibility == 'VISIBLE' else 'H') + str(row.position) for row in self.lines):
            raise ValueError('Line keys must match position and visibility')
        if not set(self.selection.candidate_keys) <= set(keys):
            raise ValueError('Unknown use-god candidate')
        if self.selection.selected_key is not None and self.selection.selected_key not in self.selection.candidate_keys:
            raise ValueError('Selected use-god must be a candidate')
        if (self.selection.status == 'AMBIGUOUS') != (self.selection.selected_key is None):
            raise ValueError('Ambiguous use-god cannot have an implicit winner')
        sources = {row['id'] for row in self.sources}
        if any(not set(row.source_ids) <= sources for row in self.findings):
            raise ValueError('Unknown analysis source')
        if len({row.id for row in self.findings}) != len(self.findings):
            raise ValueError('Finding IDs must be unique')
        if any(not set(role.line_keys + role.active_line_keys) <= set(keys) for role in self.roles):
            raise ValueError('Unknown role line')
        if any(row.line_key not in keys for row in self.timing_conditions):
            raise ValueError('Unknown timing condition line')
        return self
