FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY genopedia ./genopedia
RUN python -m pip install --upgrade pip build && python -m build --wheel --outdir /wheels
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 APP_ENV=production
RUN addgroup --system genopedia && adduser --system --ingroup genopedia --home /app genopedia
WORKDIR /app
COPY requirements-api.txt ./requirements-api.txt
RUN python -m pip install --no-cache-dir -r requirements-api.txt
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
USER genopedia
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3)" || exit 1
CMD ["sh","-c","alembic upgrade head && exec uvicorn genopedia.api.app:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
