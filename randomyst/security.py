"""Bound anonymous traffic and AI spend using bounded process memory only."""
import asyncio
from collections import OrderedDict, deque
from dataclasses import dataclass, field
import hashlib
import ipaddress
import logging
import os
import re
import threading
import time
from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from .engine import EngineError
from .snapshots import DEVELOPMENT_KEY

HEADERS = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'",
    "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer", "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


@dataclass(frozen=True)
class SecurityConfig:
    signing_key: bytes = field(default=DEVELOPMENT_KEY, repr=False)
    public_origin: str = ""
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "testserver", "[::1]")
    trusted_proxies: tuple[str, ...] = ()
    max_body_bytes: int = 1024 * 1024
    api_per_minute: int = 120
    writes_per_minute: int = 30
    ai_per_hour: int = 10
    global_per_minute: int = 600
    ai_daily_limit: int = 100
    ai_concurrency: int = 2

    @classmethod
    def load(cls):
        production = os.environ.get("RANDOMYST_ENV") == "production"
        secret = os.environ.get("RANDOMYST_SIGNING_KEY", "")
        origin = os.environ.get("RANDOMYST_PUBLIC_ORIGIN", "").rstrip("/")
        if secret and not re.fullmatch(r"[0-9a-fA-F]{64}", secret):
            raise ValueError("RANDOMYST_SIGNING_KEY must contain 64 random hexadecimal characters")
        if production and (not secret or not origin):
            raise ValueError("Production requires RANDOMYST_SIGNING_KEY and RANDOMYST_PUBLIC_ORIGIN")
        parsed = urlsplit(origin)
        if origin and (parsed.scheme not in ({"https"} if production else {"http", "https"}) or not parsed.hostname
                       or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path):
            raise ValueError("RANDOMYST_PUBLIC_ORIGIN must be an origin without a path or credentials")
        hosts = tuple(filter(None, os.environ.get("RANDOMYST_ALLOWED_HOSTS", "").split(",")))
        hosts = tuple(h.strip().lower() for h in hosts)
        if any(not re.fullmatch(r"[a-z0-9.-]+|\[::1\]", h) for h in hosts):
            raise ValueError("RANDOMYST_ALLOWED_HOSTS must list exact host names")
        proxies = tuple(filter(None, os.environ.get("RANDOMYST_TRUSTED_PROXIES", "").split(",")))
        for network in proxies:
            ipaddress.ip_network(network.strip(), strict=False)
        daily = int(os.environ.get("RANDOMYST_AI_DAILY_LIMIT", "100"))
        if not 1 <= daily <= 10000:
            raise ValueError("RANDOMYST_AI_DAILY_LIMIT must be between 1 and 10000")
        return cls(signing_key=bytes.fromhex(secret) if secret else DEVELOPMENT_KEY, public_origin=origin,
                   allowed_hosts=tuple(dict.fromkeys(["localhost", "127.0.0.1", "[::1]", *(hosts or ([parsed.hostname] if origin else ["testserver"]))])),
                   trusted_proxies=proxies, ai_daily_limit=daily)


class AIBudget:
    def __init__(self, limit):
        self.limit = limit
        self.day = ""
        self.attempts = 0
        self.lock = threading.Lock()

    def reserve(self):
        day = time.strftime("%Y-%m-%d", time.gmtime())
        with self.lock:
            if day != self.day:
                self.day, self.attempts = day, 0
            if self.attempts >= self.limit:
                raise EngineError("AI_BUDGET_EXHAUSTED", "Phần luận AI đã đạt giới hạn hôm nay. Bạn có thể quay lại ngày mai.", 429)
            self.attempts += 1


class TrafficLimits:
    def __init__(self):
        self.buckets = OrderedDict()
        self.lock = threading.Lock()

    def allow(self, rules):
        now = time.monotonic()
        with self.lock:
            # All idle keys expire, and no request can grow the map without bound.
            for expired in [k for k, v in self.buckets.items() if v[1] <= now]:
                del self.buckets[expired]
            queues = []
            for key, limit, window in rules:
                existing = self.buckets.get(key)
                queue = existing[0] if existing else deque()
                while queue and queue[0] <= now - window:
                    queue.popleft()
                if len(queue) >= limit:
                    return max(1, int(queue[0] + window - now) + 1)
                queues.append((key, queue, window))
            # Refuse new identities at capacity; never evict an active user's limit.
            if len(self.buckets) + sum(k not in self.buckets for k, _, _ in queues) > 10000:
                return 60
            for key, queue, window in queues:
                queue.append(now)
                self.buckets[key] = (queue, now + window)
                self.buckets.move_to_end(key)
        return 0


class SecurityMiddleware:
    def __init__(self, app, config):
        self.app, self.config = app, config
        self.limits = TrafficLimits()
        self.inflight = 0
        self.proxies = [ipaddress.ip_network(p.strip(), strict=False) for p in config.trusted_proxies]

    def client_key(self, scope, headers):
        peer = (scope.get("client") or ("unknown", 0))[0]
        try:
            address = ipaddress.ip_address(peer)
            if any(address in network for network in self.proxies):
                chain = headers.get("x-forwarded-for", "").split(",")
                if len(chain) <= 20:
                    for hop in reversed(chain):
                        address = ipaddress.ip_address(hop.strip())
                        if not any(address in network for network in self.proxies):
                            break
                    peer = str(address)
        except ValueError:
            pass
        return hashlib.sha256(peer.encode()).hexdigest()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        path = scope["path"]
        api = path.startswith("/api/")
        response_started = False

        async def secure_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                additions = {k.lower().encode(): v.encode() for k, v in HEADERS.items()}
                if api or path == "/":
                    additions[b"cache-control"] = b"no-store"
                if self.config.public_origin.startswith("https://"):
                    additions[b"strict-transport-security"] = b"max-age=31536000"
                message["headers"] = [(k, v) for k, v in message.get("headers", []) if k.lower() not in additions] + list(additions.items())
            await send(message)

        async def reject(code, message, status, retry=None):
            response = JSONResponse({"error": {"code": code, "message": message}}, status_code=status,
                                    headers={"Retry-After": str(retry)} if retry else None)
            await response(scope, receive, secure_send)

        async def handle(app_receive):
            try:
                return await self.app(scope, app_receive, secure_send)
            except Exception as exc:
                # Do not let ASGI log the raw exception or private request values.
                logging.getLogger("arcana.security").error("Request failed: %s", type(exc).__name__)
                if not response_started:
                    return await reject("INTERNAL_ERROR", "Chưa xử lý được yêu cầu. Hãy thử lại sau.", 500)

        host = headers.get("host", "").lower()
        hostname = host.rsplit(":", 1)[0] if host.count(":") == 1 else host.split("]:", 1)[0] + "]" if host.startswith("[") and "]:" in host else host
        if hostname not in self.config.allowed_hosts:
            return await reject("HOST_NOT_ALLOWED", "Địa chỉ truy cập không hợp lệ.", 400)
        if not api or path == "/api/v1/health":
            return await handle(receive)
        origin = headers.get("origin")
        expected = self.config.public_origin or f"{scope['scheme']}://{host}"
        if headers.get("sec-fetch-site") == "cross-site" or (origin and origin != expected):
            return await reject("ORIGIN_NOT_ALLOWED", "Không chấp nhận yêu cầu từ website khác.", 403)
        client = self.client_key(scope, headers)
        rules = [("global", self.config.global_per_minute, 60), (("api", client), self.config.api_per_minute, 60)]
        if scope["method"] == "POST":
            rules.append((("write", client), self.config.writes_per_minute, 60))
        if path == "/api/v1/ai/readings":
            rules.append((("ai", client), self.config.ai_per_hour, 3600))
        retry = self.limits.allow(rules)
        if retry:
            return await reject("RATE_LIMITED", "Bạn thao tác quá nhanh. Hãy đợi một lát rồi thử lại.", 429, retry)
        if self.inflight >= 16:
            return await reject("SERVER_BUSY", "Ứng dụng đang bận. Hãy thử lại sau.", 503, 5)
        self.inflight += 1
        try:
            if scope["method"] == "POST":
                if headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                    return await reject("JSON_REQUIRED", "Yêu cầu cần dùng dữ liệu JSON.", 415)
                declared = headers.get("content-length")
                if declared and (not re.fullmatch(r"[0-9]{1,8}", declared) or int(declared) > self.config.max_body_bytes):
                    return await reject("BODY_TOO_LARGE", "Dữ liệu gửi lên quá lớn.", 413)
                chunks, size = [], 0
                deadline = time.monotonic() + 10
                while True:
                    try:
                        message = await asyncio.wait_for(receive(), max(0.01, deadline - time.monotonic()))
                    except asyncio.TimeoutError:
                        return await reject("REQUEST_TIMEOUT", "Yêu cầu đã hết thời gian chờ.", 408)
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    size += len(chunk)
                    if size > self.config.max_body_bytes:
                        return await reject("BODY_TOO_LARGE", "Dữ liệu gửi lên quá lớn.", 413)
                    chunks.append(chunk)
                    if not message.get("more_body", False):
                        break
                body = b"".join(chunks)
                delivered = False

                async def body_receive():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": body, "more_body": False}
                    return await receive()

                return await handle(body_receive)
            return await handle(receive)
        finally:
            self.inflight -= 1
