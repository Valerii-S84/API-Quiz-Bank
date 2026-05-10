FROM cgr.dev/chainguard/python:latest-dev

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QUIZBANK_DB_PATH=/data/quizbank_mvp.sqlite3
ENV QUIZBANK_ENV=pilot
ENV QUIZBANK_HOST=0.0.0.0
ENV QUIZBANK_PORT=8000

WORKDIR /app

COPY --chown=nonroot:nonroot pyproject.toml README.md ./
COPY --chown=nonroot:nonroot src ./src
COPY --chown=nonroot:nonroot database ./database
COPY --chown=nonroot:nonroot tests/fixtures/selection ./tests/fixtures/selection

USER root

RUN python -m pip install --no-cache-dir -e . \
    && mkdir -p /data \
    && chown -R nonroot:nonroot /app /data

USER nonroot

EXPOSE 8000

CMD ["sh", "-c", "python -m quizbank_mvp.cli init-db && python -m quizbank_mvp.cli seed-demo && uvicorn quizbank_mvp.app:app --host \"${QUIZBANK_HOST:-0.0.0.0}\" --port \"${QUIZBANK_PORT:-8000}\""]
