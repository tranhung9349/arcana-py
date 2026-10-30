# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY web ./web
RUN npm run build:css
RUN npm prune --omit=dev --ignore-scripts --no-audit --no-fund

FROM python:3.13-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    RANDOMYST_ENV=production
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=frontend /usr/local/bin/node /usr/local/bin/node
COPY --from=frontend /build/node_modules ./node_modules

COPY requirements-runtime.lock ./
RUN pip install --no-cache-dir -r requirements-runtime.lock \
    && groupadd --gid 10001 arcana \
    && useradd --uid 10001 --gid arcana --no-create-home --no-log-init arcana

COPY randomyst ./randomyst
COPY vendor/tinix-bazi ./vendor/tinix-bazi
COPY research_tools/__init__.py research_tools/interpretation_prompt.py research_tools/date_interpretation_prompt.py research_tools/reading_strategy.py ./research_tools/
COPY config ./config
COPY schemas ./schemas
COPY data/reference ./data/reference
COPY data/interpretation ./data/interpretation
COPY data/date_calendar ./data/date_calendar
COPY docs/prompts ./docs/prompts
COPY dan_gian_config.json ./
COPY deploy/healthcheck.py ./deploy/
COPY --from=frontend /build/web ./web

USER 10001:10001
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "/app/deploy/healthcheck.py"]
CMD ["python", "-m", "uvicorn", "randomyst.api:app", "--host", "0.0.0.0", "--port", "8765", "--workers", "1", "--no-proxy-headers", "--timeout-graceful-shutdown", "180"]
