import json
from datetime import datetime, timezone
from math import exp
from pathlib import Path
from random import SystemRandom

from .bazi import analyze, star_bonuses
from .maihoa import IchingRepository
from .sampling import (ELEMENTS, GENERATES, CONTROLS, THRESHOLDS, BUCKETS, Configuration, Distribution,
                       configurations, element_of, relation_score, select_context, validate_sample)
from .time_engine import BRANCH_ELEMENTS, beijing_clock, check_provider, pillars, resolve_maihoa, solar_month

ROOT = Path(__file__).resolve().parents[1]


class EngineError(Exception):
    def __init__(self, code, message, status_code=422):
        super().__init__(message)
        self.code, self.status_code = code, status_code


class NumberEngine:
    def __init__(self):
        self.rules = json.loads((ROOT / "config/mvp1_rules.json").read_text())
        check_provider()
        if self.rules["calendar"]["algorithm_id"] != "6tail-chinese-utc8-v1":
            raise RuntimeError("Runtime requires the Beijing calendar policy")
        self.beta = self.rules["exponential_weights"]["selected_beta"]
        if self.beta != 2 or not self.rules["exponential_weights"]["production_sampling_law_confirmed"]:
            raise RuntimeError("Runtime v1 requires the selected beta 2 product-weight law")
        number_rules = self.rules["numbers"]
        if (self.rules["remediation"]["target_quota_max"] != 4
                or (number_rules["pool_min"], number_rules["pool_max"], number_rules["set_size"]) != (0, 99, 6)):
            raise RuntimeError("Run feasibility audit before changing hard-rule configuration")
        self.pool = tuple(range(number_rules["pool_min"], number_rules["pool_max"] + 1))
        thresholds = {"DAI_CAT": THRESHOLDS["DAI_CAT"], "NORMAL": THRESHOLDS["BINH_HOA"], "DAI_HUNG": THRESHOLDS["DAI_HUNG"]}
        if self.rules["evaluation"]["thresholds"] != thresholds:
            raise RuntimeError("Configured thresholds must match the audited sampling policy")
        self.iching = IchingRepository()
        folk_data = json.loads((ROOT / "dan_gian_config.json").read_text())
        self.folk = {entry["number"] for entry in folk_data["entries"]}
        self.disclaimer = json.loads((ROOT / "config/interpretation_disclaimers.json").read_text())

    def draw(self, request, received_at=None, rng=None):
        received_at = received_at or datetime.now(timezone.utc)
        civil = request.casting.clicked_at if request.casting.mode == "CURRENT" else request.casting.custom_timestamp
        warnings = []
        skew = abs((received_at - civil).total_seconds()) if request.casting.mode == "CURRENT" else None
        if skew is not None and skew > 30:
            warnings.append({"code": "CLIENT_CLOCK_SKEW", "message": "Mốc bấm nút khác giờ nhận ở server trên 30 giây; giữ mốc đã gửi để kiểm chứng."})
        birth_time = beijing_clock(request.birth.civil_datetime, request.birth.clock_uncertainty_seconds)
        casting_time = beijing_clock(civil, request.casting.clock_uncertainty_seconds)
        birth_calendar = resolve_maihoa(request.birth.civil_datetime, kind="birth")
        calendar = resolve_maihoa(civil, kind="casting")
        natal = pillars(request.birth.civil_datetime)
        bazi = analyze(natal["gans"], natal["zhis"])
        primary = request.birth.override_dung_than or bazi["primary_dung_than"]
        bazi.update(primary_used=primary, overridden=request.birth.override_dung_than is not None, natal=natal)
        maihoa = self.iching.calculate(calendar["maihoa_inputs"])
        current_month = solar_month(civil)
        stars = star_bonuses(natal["gans"], natal["zhis"], current_month["month_branch_index"])
        context, candidates = select_context(primary, maihoa["the"]["element"], maihoa["dung"]["element"], pool=self.pool)
        first_configs = configurations(context, pool=self.pool)
        if not first_configs:
            raise EngineError("INFEASIBLE_CONTEXT", "Không có bộ hợp lệ theo cấu hình hiện tại.", 500)
        cap = max(c.raw_units for c in first_configs)
        if cap <= 0:
            raise EngineError("INVALID_SCORE_CAP", "G_cap phải dương.", 500)
        month_element = BRANCH_ELEMENTS[current_month["month_branch_index"]]
        in_season = (month_element, GENERATES[month_element])
        scores = {e: relation_score(e, primary) + relation_score(e, context.the) for e in ELEMENTS}
        maximum = max(scores[element_of(n)] for n in self.pool if context.allowed(element_of(n)))
        weights, weight_trace = {}, []
        for number in self.pool:
            element = element_of(number)
            allowed = context.allowed(element)
            delta_season = 0.15 if element in in_season and (context.state != "DAI_HUNG" or element == context.remedy) else 0
            deltas = {"thien_thoi": delta_season, "hao_dong": 0.10 if number%2 == maihoa["moving_line"]%2 else 0,
                      "than_sat": stars["delta_by_element"][element],
                      "dan_gian": 0.05 if number in self.folk and CONTROLS[element] != primary else 0}
            base = exp(self.beta*(scores[element]-maximum)/100)
            multiplier = 3 if element == context.remedy else 1
            weight = base * multiplier * (1+sum(deltas.values())) if allowed else 0
            if allowed:
                weights[number] = weight
            weight_trace.append({"number": f"{number:02d}", "element": element, "single_raw_score": scores[element],
                                 "base_weight": base, "remediation_multiplier": multiplier if allowed else 0,
                                 "deltas": deltas, "weight": weight, "allowed": allowed})
        first = Distribution(first_configs, weights, pool=self.pool)
        # Freeze cap and every weight; conditioning changes only the eligible configurations.
        retry_configs = configurations(context, pool=self.pool, retry=True)
        passing = tuple(c for c in retry_configs if c.meets(cap, context.threshold))
        retry = Distribution(passing or retry_configs, weights, pool=self.pool) if retry_configs else None
        rng = rng or SystemRandom()
        history, best = [], None
        for attempt in range(1, 6):
            distribution = first if attempt == 1 or retry is None else retry
            numbers, config = distribution.sample(rng)
            is_retry = attempt > 1 and retry is not None
            if not validate_sample(numbers, context, retry=is_retry, pool=self.pool):
                raise EngineError("INVARIANT_FAILED", "Bộ sinh vi phạm luật cứng.", 500)
            record = {"attempt": attempt, "numbers": [f"{n:02d}" for n in numbers], "score": config.score(cap),
                      "g_raw": config.raw_units/6, "g_cap": cap/6, "yin_yang_score": config.yin_yang,
                      "element_score": 100*max(0,min(config.raw_units,cap))/cap,
                      "conflicting_number_count": config.conflicts, "meets_threshold": config.meets(cap,context.threshold)}
            history.append(record)
            if best is None or record["score"] > best["score"]:
                best = record
            if record["meets_threshold"]:
                best = record
                break
        for label, timing in (("birth", birth_time), ("casting", casting_time)):
            if timing["boundary"]["status"] == "UNDETERMINED":
                warnings.append({"code": "BOUNDARY_UNCERTAINTY_UNKNOWN", "context": label,
                                 "message": "Chưa có biên sai số đồng hồ để đánh giá vùng giáp ranh giờ/ngày Bắc Kinh."})
            if timing["boundary"]["crosses_boundary_with_known_components"]:
                warnings.append({"code": "NEAR_HOUR_BOUNDARY", "context": label,
                                 "message": "Thời gian Bắc Kinh nằm gần ranh giới giờ/ngày theo sai số đồng hồ đã cung cấp."})
        return {"schema_version": "draw-response-v2", "request_id": str(request.request_id), "rules_version": self.rules["rules_version"],
                "numbers": best["numbers"], "status": "OPTIMAL" if best["meets_threshold"] else "SUB_OPTIMAL",
                "score": best["score"], "threshold": context.threshold, "attempts": len(history), "selected_attempt": best["attempt"],
                "warnings": warnings,
                "disclaimer": next(row["text"] for row in self.disclaimer["messages"] if row["code"] == "INTERNAL_SCORE_MEANING"),
                "trace": {"server_received_at": received_at.isoformat(), "client_server_difference_seconds": skew,
                          "birth_time": birth_time, "casting_time": casting_time, "birth_calendar": birth_calendar, "casting_calendar": calendar,
                          "bazi": bazi, "maihoa": maihoa, "casting_solar_month": current_month, "stars": stars,
                          "remediation": {"enabled": context.state=="DAI_HUNG", "strategy": context.strategy, "target": context.remedy,
                                          "quota_min": 3, "quota_max": 4, "candidates": candidates},
                          "weights": weight_trace, "attempt_history": history, "g_cap": cap/6,
                          "beta": self.beta, "sampling_law": "CONDITIONAL_PRODUCT_WEIGHTS", "rng": "SystemRandom",
                          "interpretation": {"status": "NOT_REQUESTED", "model_called": False},
                          "calendar_policy": "BEIJING_CIVIL_UTC8", "legacy_location_fields_used": False,
                          "validation_status": "EXPERIMENTAL"}}
