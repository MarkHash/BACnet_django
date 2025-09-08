FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-test.txt

COPY . .

RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
