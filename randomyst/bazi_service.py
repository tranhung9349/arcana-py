"""Independent natal consultations; no number engine, RNG or current-day context."""
from datetime import datetime, timedelta, timezone

from .bazi_facts import chart_from_birth, facts_for
from .bazi_models import BaziResponse, BaziReadingSnapshot
from .bazi_narrative import compose
from .bazi_rules import BaziRules, digest
from .engine import EngineError


class BaziService:
    def __init__(self):
        self.rules = BaziRules()

    def consult(self, payload):
        chart = chart_from_birth(payload.birth)
        uncertainty = payload.birth.clock_uncertainty_seconds
        if uncertainty:
            center = payload.birth.civil_datetime
            for edge in (center - timedelta(seconds=uncertainty), center + timedelta(seconds=uncertainty)):
                birth = payload.birth.model_copy(update={"civil_datetime": edge})
                alternative = chart_from_birth(birth)
                if [(p.stem.index, p.branch_index) for p in chart.pillars] != [(p.stem.index, p.branch_index) for p in alternative.pillars]:
                    raise EngineError("BIRTH_BOUNDARY_UNSTABLE", "Khoảng sai số giờ sinh đi qua ranh đổi lá số. Hãy xác định lại giờ sinh trước khi luận đủ Tứ Trụ.", 422)
        facts = facts_for(chart, self.rules.config["tables"])
        assessment, findings = self.rules.evaluate(chart, facts)
        reading = compose(chart, facts, assessment, findings, payload.topic, payload.question)
        return BaziResponse.model_validate({"schema_version": "bazi-consultation-v1", "request_id": payload.request_id,
            "created_at": datetime.now(timezone.utc), "display_name": payload.display_name,
            "analysis_profile": "bazi_natal_v1", "rules_version": self.rules.version,
            "corpus_version": self.rules.corpus_version, "rules_sha256": self.rules.rules_sha256,
            "calendar_policy": "VN_INSTANT_TO_BEIJING_SECT1", "chart": chart, "facts": facts,
            "assessment": assessment, "findings": findings, "reading": reading, "evidence": self.rules.evidence,
            "coverage": self.rules.config["coverage"]}).model_dump(mode="json")

    def reinterpret(self, session, payload):
        saved = BaziResponse.model_validate(session)
        reading = compose(saved.chart, saved.facts, saved.assessment, saved.findings, payload.topic, payload.question)
        return BaziReadingSnapshot(reading_id=payload.reading_id, consultation_id=saved.request_id,
            created_at=datetime.now(timezone.utc), analysis_rules_version=saved.rules_version,
            chart_sha256=digest(session["chart"]), reading=reading).model_dump(mode="json")
