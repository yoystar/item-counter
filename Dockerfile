FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    flask~=2.3 \
    opencv-python-headless~=4.8 \
    pillow~=10.0 \
    gunicorn~=21.2

COPY app.py detector.py ./
COPY static/ static/

RUN useradd -m appuser && mkdir -p uploads && chown appuser:appuser uploads
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", \
     "--access-logfile", "-", "--error-logfile", "-", "app:app"]
