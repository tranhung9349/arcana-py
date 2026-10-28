"""SQLite transaction serializes idempotent draws, including concurrent retries."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .engine import EngineError


class DrawStore:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS draws (request_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, response TEXT NOT NULL)")

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def execute(self, request, builder):
        payload = json.dumps(request.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode()).hexdigest()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            found = connection.execute("SELECT payload_hash, response FROM draws WHERE request_id=?", (str(request.request_id),)).fetchone()
            if found:
                if found[0] != digest:
                    raise EngineError("REQUEST_ID_CONFLICT", "Mã yêu cầu đã được dùng với dữ liệu khác. Hãy tạo phiên mới.", 409)
                return json.loads(found[1])
            result = builder()
            connection.execute("INSERT INTO draws VALUES (?, ?, ?, ?)", (str(request.request_id), digest,
                result["trace"]["server_received_at"], json.dumps(result, ensure_ascii=False)))
            return result

    def history(self, limit=10):
        with self.connect() as connection:
            rows = connection.execute("SELECT request_id, created_at, response FROM draws ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
        return [{"request_id": row[0], "created_at": row[1], **{k: json.loads(row[2])[k] for k in ("numbers", "score", "status", "attempts", "rules_version")}} for row in rows]

    def get(self, request_id):
        with self.connect() as connection:
            row = connection.execute("SELECT response FROM draws WHERE request_id=?", (str(request_id),)).fetchone()
        if row is None:
            raise EngineError("DRAW_NOT_FOUND", "Không tìm thấy phiên gieo để đọc giải thích.", 404)
        return json.loads(row[0])
