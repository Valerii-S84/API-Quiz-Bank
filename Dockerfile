FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QUIZBANK_DB_PATH=/data/quizbank_mvp.sqlite3
ENV QUIZBANK_ENV=pilot
ENV QUIZBANK_HOST=0.0.0.0
ENV QUIZBANK_PORT=8000

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY database ./database
COPY tests/fixtures/selection ./tests/fixtures/selection

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["sh", "-c", "python -m quizbank_mvp.cli --db-path \"$QUIZBANK_DB_PATH\" init-db && python -m quizbank_mvp.cli --db-path \"$QUIZBANK_DB_PATH\" seed-demo && uvicorn quizbank_mvp.app:app --host \"${QUIZBANK_HOST:-0.0.0.0}\" --port \"${QUIZBANK_PORT:-8000}\""]
