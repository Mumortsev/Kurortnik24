#!/bin/bash
set -e

# Use 8000 as default port for Amvera
PORT=${PORT:-8000}
echo "Running on port: $PORT"

# Ensure database is initialized in the persistent volume
if [[ "$DATABASE_URL" == *"sqlite"* ]] || [ -z "$DATABASE_URL" ]; then
    echo "Using SQLite database. Ensuring /data directory exists..."
    mkdir -p /data
    
    # Initialize DB tables and demo data if needed
    echo "Running database initialization..."
    python scripts/init_db.py --demo
fi

# Define API URL for the bot
export API_URL="http://127.0.0.1:$PORT"

# Start Telegram Bot in background
echo "Starting Telegram Bot..."
python -m bot.main &

# Start FastAPI server in foreground
echo "Starting FastAPI server..."
exec uvicorn api.main:app --host 0.0.0.0 --port $PORT
