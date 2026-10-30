"""Stateless public API. Personal results belong to the browser, never SQLite."""
from datetime import datetime, timezone
import logging
import os

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .time_engine import CalendarError
from .engine import EngineError, NumberEngine, ROOT
from .models import DrawRequest, StrictModel
from .interpretation import ExplanationRepository
from .date_engine import DateEngine
from .date_models import DateSearchRequest
from .date_consultations import DateConsultationRequest, DateConsultation
from .date_reading import explain_day
from .maihoa_models import MaiHoaRequest
from .coins_models import CoinRequest
from .coins_service import CoinService
from .liuyao_analysis import LiuYaoInterpreter, digest
from .liuyao_models import AnalysisContext, QuestionIntentRequest
from .bazi_models import BaziRequest, BaziReadingRequest
from .bazi_service import BaziService
from .ai_service import AIReadingService, AIReadingRequest, AIReadingResult
from .ai_jobs import reading_events
from .security import AIBudget, SecurityConfig, SecurityMiddleware, HEADERS
from .snapshots import SignedSnapshot, SnapshotSigner


class SnapshotInput(StrictModel):
    consultation: SignedSnapshot


class BaziReadingInput(SnapshotInput):
    reading: BaziReadingRequest


class CoinAnalysisInput(SnapshotInput):
    context: AnalysisContext


def create_app(db_path=None, ai_config=None, ai_client=None, security_config=None):
    # The legacy db_path argument is accepted for callers, but never opened.
    config = security_config or SecurityConfig.load()
    app = FastAPI(title="Arcana", version="0.9.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.security = config
    app.state.signer = SnapshotSigner(config.signing_key)
    app.state.engine = NumberEngine()
    app.state.explanations = ExplanationRepository(app.state.engine.iching)
    app.state.date_engine = DateEngine()
    app.state.maihoa = app.state.explanations.maihoa_service
    app.state.coins = CoinService(app.state.explanations)
    app.state.liuyao = LiuYaoInterpreter(app.state.coins.najia)
    app.state.bazi = BaziService()
    app.state.ai_budget = AIBudget(config.ai_daily_limit)
    app.state.ai = AIReadingService(app.state, ai_config, ai_client)
    app.add_middleware(SecurityMiddleware, config=config)

    def signed(kind, result):
        data = jsonable_encoder(result)
        return JSONResponse(data, headers={"X-Arcana-Signature": app.state.signer.sign(kind, data)})

    @app.get("/api/v1/ai/status")
    def ai_status():
        return app.state.ai.config.public_status()

    @app.post("/api/v1/ai/readings/lookup", response_model=AIReadingResult | None)
    def lookup_ai_reading(payload: AIReadingRequest):
        return app.state.ai.lookup(payload)

    @app.post("/api/v1/ai/readings", response_model=AIReadingResult)
    def ai_reading(payload: AIReadingRequest):
        return app.state.ai.execute(payload)

    def reading_stream(payload, *, generate):
        job = app.state.ai.subscribe(payload, generate=generate)
        return StreamingResponse(reading_events(job), media_type="text/event-stream",
                                 headers={"X-Accel-Buffering": "no", "Cache-Control": "no-store"})

    @app.post("/api/v1/ai/readings/start")
    def start_ai_reading(payload: AIReadingRequest):
        return reading_stream(payload, generate=True)

    @app.post("/api/v1/ai/readings/stream")
    def observe_ai_reading(payload: AIReadingRequest):
        return reading_stream(payload, generate=False)

    @app.get("/api/v1/bazi/rules")
    def bazi_rules():
        return app.state.bazi.rules.overview()

    @app.post("/api/v1/bazi/consultations")
    def bazi_consultation(payload: BaziRequest):
        return signed("BAZI", app.state.bazi.consult(payload))

    @app.post("/api/v1/bazi/readings")
    def reread_bazi(payload: BaziReadingInput):
        saved = app.state.signer.verify(payload.consultation, "BAZI")
        if str(payload.reading.reading_id) == saved["request_id"]:
            raise EngineError("REQUEST_ID_CONFLICT", "Hãy dùng mã mới cho bài luận mới.", 409)
        return signed("BAZI_READING", app.state.bazi.reinterpret(saved, payload.reading))

    @app.get("/api/v1/coins/analysis-rules")
    def coin_analysis_rules():
        return app.state.liuyao.rules()

    @app.post("/api/v1/coins/question-intent")
    def coin_question_intent(payload: QuestionIntentRequest):
        return app.state.liuyao.intent.recognize(payload.question, payload.topic)

    @app.post("/api/v1/coins/analysis")
    def analyze_coin_consultation(payload: CoinAnalysisInput):
        saved = app.state.signer.verify(payload.consultation, "COINS")
        return signed("LIUYAO", app.state.liuyao.analyze(saved, payload.context))

    @app.get("/api/v1/coins/hexagrams")
    def coin_catalog():
        return app.state.coins.catalog()

    @app.get("/api/v1/coins/hexagrams/{number}")
    def coin_reading(number: int):
        if not 1 <= number <= 64:
            raise EngineError("VALIDATION_FAILED", "Số quẻ nằm ngoài phạm vi hỗ trợ.", 422)
        return app.state.coins.reading(number)

    @app.post("/api/v1/coins/consultations")
    def coin_consultation(payload: CoinRequest):
        return signed("COINS", app.state.coins.consult(payload))

    @app.get("/api/v1/maihoa/rules")
    def maihoa_rules():
        return app.state.maihoa.rules.overview()

    @app.post("/api/v1/maihoa/consultations")
    def maihoa_consultation(payload: MaiHoaRequest):
        return signed("MAIHOA", app.state.maihoa.consult(payload, datetime.now(timezone.utc)))

    @app.post("/api/v2/auspicious-dates/search")
    def search_dates(payload: DateSearchRequest):
        return app.state.date_engine.search(payload)

    @app.post("/api/v2/auspicious-dates/consultations")
    def date_consultation(payload: DateConsultationRequest):
        result = app.state.date_engine.search(payload.search.model_copy(update={"include_details": True}))
        config = app.state.date_engine.evaluator.config
        scoring = (config.day_scoring if result["evaluation_mode"] == "DAY_ONLY" else config.scoring).model_dump()
        saved = DateConsultation(request_id=payload.request_id, created_at=datetime.now(timezone.utc), result=result,
            scoring=scoring, rules_sha256=digest(config.model_dump(mode="json")), explanation=explain_day(result, scoring))
        return signed("DATE", saved.model_dump(mode="json"))

    @app.get("/api/v2/auspicious-dates/rules")
    def date_rule_summary():
        rules = app.state.date_engine.evaluator.config
        return {"rules_version": rules.rules_version, "activities": [x.model_dump() for x in rules.activities],
                "activity_registry_version": rules.activity_registry_version,
                "groups": [x.model_dump() for x in rules.groups],
                "disabled_rules": rules.disabled_rules, "scoring": rules.scoring.model_dump(),
                "day_scoring": rules.day_scoring.model_dump(), "rules": [x.model_dump() for x in rules.rules],
                "sources": [x.model_dump() for x in rules.sources]}

    @app.get("/api/v1/health")
    def health():
        engine = app.state.engine
        return {"status": "ok", "mvp": 1, "pool": [engine.pool[0], engine.pool[-1]],
                "set_size": engine.rules["numbers"]["set_size"], "beta": engine.beta,
                "rules_version": engine.rules["rules_version"], "calendar": engine.rules["calendar"],
                "validation_status": "EXPERIMENTAL", "storage": "VOLATILE_ONLY"}

    @app.post("/api/v1/draw")
    def draw(payload: DrawRequest):
        return signed("DRAW", app.state.engine.draw(payload, datetime.now(timezone.utc)))

    @app.post("/api/v1/interpretation")
    def interpretation(payload: SnapshotInput):
        return app.state.explanations.explain(app.state.signer.verify(payload.consultation, "DRAW"))

    @app.exception_handler(EngineError)
    async def engine_error(request, exc):
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": str(exc)}})

    @app.exception_handler(CalendarError)
    async def calendar_error(request, exc):
        return JSONResponse(status_code=422, content={"error": {"code": exc.code, "message": str(exc)}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_FAILED", "message": "Dữ liệu đầu vào không hợp lệ.",
            "fields": [{"field": ".".join(str(v) for v in e["loc"]), "message": "Giá trị không hợp lệ."} for e in exc.errors()]}})

    @app.exception_handler(Exception)
    async def internal_error(request, exc):
        # Exception text can contain birth profiles, provider responses or keys.
        logging.getLogger("arcana.security").error("Request failed: %s", type(exc).__name__)
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Chưa xử lý được yêu cầu. Hãy thử lại sau."}},
                            headers={**HEADERS, "Cache-Control": "no-store"})

    app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(ROOT / "web/index.html")

    return app


app = create_app()
