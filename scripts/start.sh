#!/bin/bash
set -e

# Define API URL for the bot based on Railway PORT
export API_URL="http://127.0.0.1:${PORT:-8000}"

# Start Telegram Bot in background
echo "Starting Telegram Bot with API_URL=$API_URL..."
python -m bot.main &

# Start FastAPI server in foreground
# Use PORT env var provided by Railway
echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
