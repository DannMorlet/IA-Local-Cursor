FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MATICK_HOST=0.0.0.0 \
    MATICK_PORT=8787 \
    MATICK_DB_PATH=/data/events.db

WORKDIR /app
COPY matick_cloud /app/matick_cloud
RUN useradd --uid 10001 --create-home matick \
    && mkdir -p /data \
    && chown matick:matick /data
USER matick
VOLUME ["/data"]
EXPOSE 8787
CMD ["python", "-m", "matick_cloud"]
