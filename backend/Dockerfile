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

# Copy requirements file (Dockerfile already inside backend/)
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy entire backend directory
COPY . /app/

# Fix permissions for start script
RUN chmod +x /app/start.sh

EXPOSE 8000

ENTRYPOINT ["sh", "/app/start.sh"]
