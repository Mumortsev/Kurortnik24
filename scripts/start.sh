#!/bin/bash
set -e

# Start Telegram Bot in background
echo "Starting Telegram Bot..."
python -m bot.main &

# Start FastAPI server in foreground
# Use PORT env var provided by Railway
echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
