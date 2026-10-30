"""Small OpenAI-compatible HTTP transport; credentials remain on the server."""
from dataclasses import dataclass, field
from http.client import IncompleteRead
import json
import logging
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .engine import EngineError, ROOT


@dataclass(frozen=True)
class AIConfig:
    base_url: str = ""
    model: str = ""
    api_key: str = field(default="", repr=False)
    timeout: float = 55
    reasoning_effort: str | None = None

    @classmethod
    def load(cls, path=None, environ=None):
        values = {}
        path = Path(path) if path is not None else ROOT / ".env.local"
        if path.exists():
            for line in path.read_text().splitlines():
                if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip().startswith("RANDOMYST_AI_"):
                    values[key.strip()] = value.strip().strip('"').strip("'")
        values.update(os.environ if environ is None else environ)
        try:
            timeout = float(values.get("RANDOMYST_AI_TIMEOUT_SECONDS", 55))
        except ValueError:
            raise ValueError("Invalid AI timeout configuration") from None
        if not 5 <= timeout <= 180:
            raise ValueError("AI timeout must be between 5 and 180 seconds")
        effort = values.get("RANDOMYST_AI_REASONING_EFFORT") or None
        if effort not in (None, "none", "low", "medium", "high", "xhigh", "max"):
            raise ValueError("Invalid AI reasoning effort")
        result = cls(values.get("RANDOMYST_AI_BASE_URL", "").rstrip("/"), values.get("RANDOMYST_AI_MODEL", ""),
                     values.get("RANDOMYST_AI_API_KEY", ""), timeout, effort)
        if result.base_url:
            u = urlsplit(result.base_url)
            if u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment:
                raise ValueError("AI base URL must be an HTTPS URL without credentials, query or fragment")
        return result

    @property
    def configured(self):
        return bool(self.base_url and self.model and self.api_key)

    def public_status(self):
        return {"configured": self.configured, "model": self.model,
                "provider_host": urlsplit(self.base_url).hostname if self.base_url else None}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward an Authorization header to another origin.


class CompatibleAIClient:
    def __init__(self, config, opener=None, before_request=None):
        self.config = config
        self.opener = opener or build_opener(NoRedirect())
        self.before_request = before_request

    @staticmethod
    def _usage(data):
        return {key: value for key, value in (data or {}).items()
                if key in ("prompt_tokens", "completion_tokens", "total_tokens") and type(value) is int and value >= 0}

    def _stream(self, response, deadline):
        parts, content_size, wire_size, event_size = [], 0, 0, 0
        lines, model, usage, finish = [], self.config.model, {}, None
        while True:
            if time.monotonic() >= deadline:
                raise EngineError("AI_CONNECTION_FAILED", "Phần luận đã hết thời gian xử lý. Bạn có thể thử lại.", 502)
            line = response.readline(1_048_577)
            wire_size += len(line)
            event_size += len(line)
            if wire_size > 8_388_608 or event_size > 1_048_576:
                raise ValueError("Oversized stream")
            if not line:
                raise EngineError("AI_RESPONSE_INCOMPLETE", "Kết nối AI bị ngắt trước khi bài luận hoàn tất.", 502)
            line = line.rstrip(b"\r\n")
            if line:
                if line.startswith(b"data:"):
                    lines.append(line[5:].lstrip(b" "))
                continue
            event_size = 0
            if not lines:
                continue  # SSE comments/heartbeats carry no model text.
            event, lines = b"\n".join(lines).decode("utf-8"), []
            if event == "[DONE]":
                if finish != "stop" or not parts:
                    raise EngineError("AI_RESPONSE_INCOMPLETE", "Bài luận AI chưa hoàn tất; chưa được lưu.", 502)
                return "".join(parts), {"model": model, "usage": usage}
            data = json.loads(event)
            if data.get("error"):
                raise EngineError("AI_UPSTREAM_FAILED", "Dịch vụ AI chưa hoàn tất bài luận. Bạn có thể thử lại.", 502)
            if isinstance(data.get("model"), str):
                model = data["model"][:150]
            if data.get("usage") is not None:
                usage = self._usage(data["usage"])
            for choice in data.get("choices", []):
                if choice.get("index", 0) != 0:
                    continue
                chunk = choice.get("delta", {}).get("content")
                if chunk is not None:
                    if not isinstance(chunk, str):
                        raise ValueError("Invalid stream content")
                    content_size += len(chunk.encode("utf-8"))
                    if content_size > 1_048_576:
                        raise ValueError("Oversized content")
                    parts.append(chunk)
                reason = choice.get("finish_reason")
                if reason is not None:
                    if reason != "stop":
                        raise EngineError("AI_RESPONSE_INCOMPLETE", "Bài luận AI bị ngắt giữa chừng; chưa được lưu.", 502)
                    finish = reason

    @staticmethod
    def _read_json(response, deadline):
        chunks, size = [], 0
        read = getattr(response, "read1", response.read)
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                raise EngineError("AI_CONNECTION_FAILED", "Phần luận đã hết thời gian xử lý. Bạn có thể thử lại.", 502)
            chunk = read(min(8192, 1_048_577 - size))
            if not chunk:
                return json.loads(b"".join(chunks))
            size += len(chunk)
            if size > 1_048_576:
                raise ValueError("Oversized response")
            chunks.append(chunk)

    def complete(self, messages, *, max_tokens=12000, stream=False, deadline=None):
        if not self.config.configured:
            raise EngineError("AI_NOT_CONFIGURED", "Chưa cấu hình dịch vụ luận giải AI ở máy chủ.", 503)
        if type(max_tokens) is not int or not 1 <= max_tokens <= 24000:
            raise ValueError("Invalid server completion budget")
        payload = {"model": self.config.model, "messages": messages,
                   "max_tokens": max_tokens, "response_format": {"type": "json_object"}, "stream": stream}
        if stream:
            payload["stream_options"] = {"include_usage": True}
        if self.config.reasoning_effort:
            payload["reasoning_effort"] = self.config.reasoning_effort
        else:
            payload["temperature"] = 0.3
        body = json.dumps(payload, ensure_ascii=False).encode()
        request = Request(self.config.base_url + "/chat/completions", data=body, method="POST",
                          headers={"Authorization": "Bearer " + self.config.api_key,
                                   "Content-Type": "application/json", "Accept": "text/event-stream" if stream else "application/json"})
        # Idle reads retain the configured socket timeout; a busy stream also has
        # a finite total lifetime, even if the provider only sends heartbeats.
        deadline = min(deadline or float("inf"), time.monotonic() + 600) if stream else deadline
        for attempt in range(2):
            remaining = deadline - time.monotonic() if deadline is not None else self.config.timeout
            if remaining <= 0:
                raise EngineError("AI_CONNECTION_FAILED", "Phần luận đã hết thời gian xử lý. Bạn có thể thử lại.", 502)
            if self.before_request:
                self.before_request()
            try:
                with self.opener.open(request, timeout=min(self.config.timeout, remaining)) as response:
                    # Some compatible gateways return a complete JSON response
                    # despite stream=true. Accept it without a second paid call.
                    content_type = getattr(response, "headers", {}).get("Content-Type", "").lower()
                    if stream and "application/json" not in content_type:
                        content, metadata = self._stream(response, deadline)
                    else:
                        data = self._read_json(response, deadline)
                        choice = data["choices"][0]
                        content = choice["message"]["content"]
                        if choice.get("finish_reason") == "length":
                            raise EngineError("AI_RESPONSE_INCOMPLETE", "Bài luận AI bị ngắt giữa chừng; chưa được lưu.", 502)
                        model = data.get("model")
                        metadata = {"model": model[:150] if isinstance(model, str) else self.config.model,
                                    "usage": self._usage(data.get("usage"))}
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("Empty content")
                # Some compatible providers wrap even JSON-mode output in fences.
                content = content.strip()
                if content.startswith("```json\n") and content.endswith("\n```"):
                    content = content[8:-4]
                reading = json.loads(content)
                return reading, metadata
            except HTTPError as error:
                code = error.code
                error.close()
                if code in (429, 502, 503, 504) and attempt == 0:
                    time.sleep(1)
                    continue
                if code in (401, 403):
                    raise EngineError("AI_AUTH_FAILED", "Dịch vụ AI chưa chấp nhận thông tin kết nối ở máy chủ.", 502) from None
                if code == 429:
                    raise EngineError("AI_RATE_LIMITED", "Dịch vụ AI đang giới hạn lượt gọi. Bạn có thể thử lại sau.", 503) from None
                raise EngineError("AI_UPSTREAM_FAILED", "Chưa nhận được bài luận từ dịch vụ AI. Bạn có thể thử lại.", 502) from None
            except (TimeoutError, URLError, OSError, IncompleteRead):
                # An uncertain timeout is not automatically retried: it may already
                # have been billed by the remote provider.
                raise EngineError("AI_CONNECTION_FAILED", "Kết nối AI chưa hoàn tất. Phiên đã lưu; bạn có thể thử lại phần luận.", 502) from None
            except (ValueError, TypeError, KeyError, IndexError, AttributeError) as error:
                # Diagnose transport/JSON failures without logging model prose,
                # questions, request bodies or authentication headers.
                logging.getLogger("arcana.ai").warning("AI response invalid: stream=%s type=%s", stream, type(error).__name__)
                raise EngineError("AI_RESPONSE_INVALID", "AI chưa trả đúng định dạng bài luận; kết quả này chưa được lưu.", 502) from None
