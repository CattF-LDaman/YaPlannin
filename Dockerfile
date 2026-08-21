FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    YAP_DATA_DIR=/data/YaPServer \
    YAP_HOST=0.0.0.0 \
    YAP_PORT=8080

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/sh yap

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY YaP ./YaP
COPY run_server.py .
COPY docker ./docker

RUN chmod +x docker/entrypoint.sh \
    && mkdir -p /data/YaPServer \
    && chown -R yap:yap /app /data

USER yap

EXPOSE 8080

VOLUME ["/data/YaPServer"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"YAP_PORT\", \"8080\")}/login')"

ENTRYPOINT ["docker/entrypoint.sh"]
