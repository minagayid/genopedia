FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PORT=8000
WORKDIR /app
RUN groupadd --system genopedia && useradd --system --gid genopedia --home-dir /nonexistent --shell /usr/sbin/nologin genopedia
COPY pyproject.toml README.md LICENSE ./
COPY genopedia ./genopedia
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
RUN python -m pip install --upgrade pip && python -m pip install ".[api]"
USER genopedia
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3)" || exit 1
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
