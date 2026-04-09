# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies in a separated later to use the cache
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim

# no-root usaer: good basic security practice
RUN useradd --create-home appuser
WORKDIR /home/appuser

# Copy only the necessary from builder
COPY --from=builder /install /usr/local/
COPY main.py .

USER appuser

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD ["python", "main.py"]
