#!/bin/bash
set -e

# Use 80 as default port for Amvera
PORT=${PORT:-80}
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
echo "--- DEBUG INFO ---"
ls -la /app/api/main.py
echo "Checking for debug-files endpoint code:"
grep "debug-files" /app/api/main.py || echo "NOT FOUND!"
echo "Listing static files:"
ls -R /app/static || echo "Static dir error"
echo "--- END DEBUG ---"
exec uvicorn api.main:app --host 0.0.0.0 --port $PORT
