"""Small OpenAI-compatible HTTP transport; credentials remain on the server."""
from dataclasses import dataclass, field
import json
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
        if not 5 <= timeout <= 90:
            raise ValueError("AI timeout must be between 5 and 90 seconds")
        result = cls(values.get("RANDOMYST_AI_BASE_URL", "").rstrip("/"), values.get("RANDOMYST_AI_MODEL", ""),
                     values.get("RANDOMYST_AI_API_KEY", ""), timeout)
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

    def complete(self, messages):
        if not self.config.configured:
            raise EngineError("AI_NOT_CONFIGURED", "Chưa cấu hình dịch vụ luận giải AI ở máy chủ.", 503)
        body = json.dumps({"model": self.config.model, "messages": messages, "temperature": 0.3,
                           "max_tokens": 12000, "response_format": {"type": "json_object"}, "stream": False}, ensure_ascii=False).encode()
        request = Request(self.config.base_url + "/chat/completions", data=body, method="POST",
                          headers={"Authorization": "Bearer " + self.config.api_key,
                                   "Content-Type": "application/json", "Accept": "application/json"})
        for attempt in range(2):
            if self.before_request:
                self.before_request()
            try:
                with self.opener.open(request, timeout=self.config.timeout) as response:
                    raw = response.read(1_048_577)
                if len(raw) > 1_048_576:
                    raise EngineError("AI_RESPONSE_INVALID", "Dịch vụ AI trả kết quả quá dài; bài luận chưa được lưu.", 502)
                data = json.loads(raw)
                choice = data["choices"][0]
                content = choice["message"]["content"]
                if choice.get("finish_reason") == "length":
                    raise EngineError("AI_RESPONSE_INCOMPLETE", "Bài luận AI bị ngắt giữa chừng; chưa được lưu.", 502)
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("Empty content")
                # Some compatible providers wrap even JSON-mode output in fences.
                content = content.strip()
                if content.startswith("```json\n") and content.endswith("\n```"):
                    content = content[8:-4]
                reading = json.loads(content)
                usage = {key: value for key, value in (data.get("usage") or {}).items()
                         if key in ("prompt_tokens", "completion_tokens", "total_tokens") and type(value) is int and value >= 0}
                model = data.get("model")
                return reading, {"model": model[:150] if isinstance(model, str) else self.config.model, "usage": usage}
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
            except (TimeoutError, URLError, OSError):
                # An uncertain timeout is not automatically retried: it may already
                # have been billed by the remote provider.
                raise EngineError("AI_CONNECTION_FAILED", "Kết nối AI chưa hoàn tất. Phiên đã lưu; bạn có thể thử lại phần luận.", 502) from None
            except (ValueError, TypeError, KeyError, IndexError):
                raise EngineError("AI_RESPONSE_INVALID", "AI chưa trả đúng định dạng bài luận; kết quả này chưa được lưu.", 502) from None
