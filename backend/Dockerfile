FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps required by some Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libjpeg-dev \
       poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/ /app/

# Copy and make the start script executable
COPY backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh || true

EXPOSE 8000

# Use the start script to ensure DB and folders exist before starting
ENTRYPOINT ["sh", "/app/start.sh"]
