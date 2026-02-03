
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for caching
COPY backend/requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ /app/

# Copy frontend code to static directory
COPY frontend/ /app/static/

# Copy scripts
COPY scripts/ /app/scripts/

# Fix line endings and permissions for start script
RUN dos2unix /app/scripts/start.sh && chmod +x /app/scripts/start.sh

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app

# Start services
CMD ["/app/scripts/start.sh"]
