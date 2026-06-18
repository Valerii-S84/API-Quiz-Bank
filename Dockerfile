FROM cgr.dev/chainguard/python:latest-dev@sha256:d1dd83447d5113f8b3eeb67c4863db2c8198952ec78fd643c1b3844f0d7cb36c

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QUIZBANK_DB_PATH=/data/quizbank_mvp.sqlite3
ENV QUIZBANK_ENV=pilot
ENV QUIZBANK_HOST=0.0.0.0
ENV QUIZBANK_PORT=8000

WORKDIR /app

COPY --chown=nonroot:nonroot pyproject.toml README.md ./
COPY --chown=nonroot:nonroot data/config/protected_beta_channels.json ./data/config/protected_beta_channels.json
COPY --chown=nonroot:nonroot src ./src
COPY --chown=nonroot:nonroot database ./database
COPY --chown=nonroot:nonroot \
    tools/quizbank_common.py \
    tools/import_production_corpus_to_runtime.py \
    tools/recover_protected_beta_schedule.py \
    tools/run_protected_beta_schedule.py \
    ./tools/
COPY --chown=nonroot:nonroot tests/fixtures/selection ./tests/fixtures/selection

USER root

RUN python -m pip install --no-cache-dir -e . \
    && mkdir -p /data \
    && chown -R nonroot:nonroot /app /data

USER nonroot

EXPOSE 8000

ENTRYPOINT []
CMD ["sh", "-c", "python -m quizbank_mvp.cli init-db && uvicorn quizbank_mvp.app:app --host \"${QUIZBANK_HOST:-0.0.0.0}\" --port \"${QUIZBANK_PORT:-8000}\""]
