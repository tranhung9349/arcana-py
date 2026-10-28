"""Immutable consultation and topic-reading snapshots, each idempotent by UUID."""
import json

from .bazi_models import BaziReadingSnapshot
from .bazi_rules import digest
from .engine import EngineError


class BaziStore:
    def __init__(self, store):
        self.store = store
        with store.connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS bazi_consultations (request_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, response TEXT NOT NULL)")
            connection.execute("CREATE TABLE IF NOT EXISTS bazi_readings (reading_id TEXT PRIMARY KEY, consultation_id TEXT NOT NULL, payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, response TEXT NOT NULL)")

    def execute(self, payload, service):
        key = str(payload.request_id)
        hashed = digest(payload.model_dump(mode="json"))
        with self.store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT payload_hash, response FROM bazi_consultations WHERE request_id=?", (key,)).fetchone()
            if row:
                if row[0] != hashed:
                    raise EngineError("REQUEST_ID_CONFLICT", "Mã lá số đã dùng với hồ sơ khác. Hãy tạo lá số mới.", 409)
                return json.loads(row[1])
            result = service.consult(payload)
            connection.execute("INSERT INTO bazi_consultations VALUES (?, ?, ?, ?)",
                (key, hashed, result["created_at"], json.dumps(result, ensure_ascii=False)))
            return result

    def get(self, request_id):
        with self.store.connect() as connection:
            row = connection.execute("SELECT response FROM bazi_consultations WHERE request_id=?", (str(request_id),)).fetchone()
        if not row:
            raise EngineError("BAZI_NOT_FOUND", "Không tìm thấy lá số Bát Tự.", 404)
        return json.loads(row[0])

    def history(self, limit=10):
        with self.store.connect() as connection:
            rows = connection.execute("SELECT response FROM bazi_consultations ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
        result = []
        for row in rows:
            s = json.loads(row[0])
            result.append({"request_id": s["request_id"], "created_at": s["created_at"], "display_name": s["display_name"],
                           "birth_datetime": s["chart"]["civil_datetime"], "title": s["reading"]["title"],
                           "topic_name": s["reading"]["topic_name"]})
        return result

    def reread(self, request_id, payload, service):
        session = self.get(request_id)
        parent, key = str(request_id), str(payload.reading_id)
        hashed = digest({"consultation_id": parent, "context": payload.model_dump(mode="json")})
        # Initial reading has the consultation UUID; it is never a new-reading key.
        if key == parent:
            raise EngineError("REQUEST_ID_CONFLICT", "Hãy dùng mã mới cho bài luận mới.", 409)
        with self.store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT payload_hash, response FROM bazi_readings WHERE reading_id=?", (key,)).fetchone()
            if row:
                if row[0] != hashed:
                    raise EngineError("REQUEST_ID_CONFLICT", "Mã bài luận đã dùng với ngữ cảnh khác.", 409)
                return json.loads(row[1])
            result = service.reinterpret(session, payload)
            connection.execute("INSERT INTO bazi_readings VALUES (?, ?, ?, ?, ?)",
                (key, parent, hashed, result["created_at"], json.dumps(result, ensure_ascii=False)))
            return result

    def readings(self, request_id, limit=10):
        session = self.get(request_id)
        initial = BaziReadingSnapshot(reading_id=session["request_id"], consultation_id=session["request_id"],
            created_at=session["created_at"], analysis_rules_version=session["rules_version"],
            chart_sha256=digest(session["chart"]), reading=session["reading"]).model_dump(mode="json")
        with self.store.connect() as connection:
            rows = connection.execute("SELECT response FROM bazi_readings WHERE consultation_id=? ORDER BY rowid DESC LIMIT ?", (str(request_id), limit)).fetchall()
        return [initial, *[json.loads(row[0]) for row in rows]]
