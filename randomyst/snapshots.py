"""Authenticate browser-held results without keeping profiles on the server."""
import hashlib
import hmac
import math
import secrets
import struct
from typing import Literal

from pydantic import Field

from .engine import EngineError
from .models import StrictModel

SnapshotKind = Literal["DRAW", "BAZI", "BAZI_READING", "MAIHOA", "COINS", "LIUYAO", "DATE"]
DEVELOPMENT_KEY = secrets.token_bytes(32)


class SignedSnapshot(StrictModel):
    kind: SnapshotKind
    data: dict
    signature: str = Field(pattern=r"^[0-9a-f]{64}$")


class SnapshotSigner:
    def __init__(self, key):
        self.key = key

    def sign(self, kind, data):
        # JSON.parse/stringify turns 1.0 into 1 and -0 into 0. Hash semantic
        # JSON values with explicit type/length tags, not serializer-specific
        # number spelling. IEEE-754 matches the browser's number representation.
        mac = hmac.new(self.key, digestmod=hashlib.sha256)

        def feed(value, depth=0):
            if depth > 64:
                raise EngineError("SNAPSHOT_INVALID", "Cấu trúc kết quả không hợp lệ.", 422)
            if value is None:
                mac.update(b"z")
            elif isinstance(value, bool):
                mac.update(b"t" if value else b"f")
            elif isinstance(value, (int, float)):
                if isinstance(value, int) and abs(value) > 2**53 - 1:
                    raise EngineError("SNAPSHOT_INVALID", "Giá trị kết quả không hợp lệ.", 422)
                number = float(value)
                if not math.isfinite(number):
                    raise EngineError("SNAPSHOT_INVALID", "Giá trị kết quả không hợp lệ.", 422)
                mac.update(b"n" + struct.pack(">d", number if number else 0.0))
            elif isinstance(value, str):
                encoded = value.encode("utf-8")
                mac.update(b"s" + struct.pack(">Q", len(encoded)) + encoded)
            elif isinstance(value, list):
                mac.update(b"a" + struct.pack(">Q", len(value)))
                for item in value:
                    feed(item, depth + 1)
            elif isinstance(value, dict):
                mac.update(b"o" + struct.pack(">Q", len(value)))
                for key in sorted(value):
                    feed(key, depth + 1)
                    feed(value[key], depth + 1)
            else:
                raise EngineError("SNAPSHOT_INVALID", "Kiểu kết quả không hợp lệ.", 422)

        feed(["arcana-snapshot-v2", kind, data])
        return mac.hexdigest()

    def verify(self, snapshot, kind):
        if snapshot.kind != kind or not hmac.compare_digest(snapshot.signature, self.sign(kind, snapshot.data)):
            raise EngineError("SNAPSHOT_INVALID", "Kết quả đã lưu không còn hợp lệ. Hãy tạo phiên mới.", 422)
        return snapshot.data
