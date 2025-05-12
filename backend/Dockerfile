FROM python:3.12-slim-bookworm
WORKDIR /app
RUN addgroup --gid 1001 appgroup && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos "" appuser
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++-11 \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
RUN chown -R appuser:appgroup /app
USER appuser
CMD ["uvicorn", "src.monitoring:app", "--host", "0.0.0.0", "--port", "8000"]