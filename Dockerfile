# Build stage for Vue frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy all frontend source files
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html ./
COPY frontend/*.json ./
COPY frontend/*.ts ./
COPY frontend/vite.config.ts ./

# Build the frontend
RUN npm run build

# Production stage - use OSGeo image with GDAL pre-installed
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.3

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python commands
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY voronoi_generator.py .
COPY static/ ./static/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create directories for cache and maps
RUN mkdir -p cache maps

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default port (Railway will override with $PORT)
ENV PORT=8000

# Start command (uses shell form to expand $PORT)
CMD uvicorn app:app --host 0.0.0.0 --port $PORT

