#!/bin/sh
set -e

# Ensure upload/result dirs exist and DB file is present with permissive permissions
mkdir -p /app/uploads /app/results
if [ ! -f /app/database.db ]; then
  touch /app/database.db
fi

# Try to set permissions where possible; ignore errors
chmod 777 /app/uploads || true
chmod 777 /app/results || true
chmod 666 /app/database.db || true

# Exec the server
exec uvicorn main:app --host 0.0.0.0 --port 8000
