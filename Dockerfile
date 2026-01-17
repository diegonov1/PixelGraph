# Multi-stage build for PixelGraph

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY pixelgraph/ ./pixelgraph/
COPY examples/ ./examples/

# Copy built frontend into the package
COPY --from=frontend-builder /app/pixelgraph/static ./pixelgraph/static

# Expose port
EXPOSE 8000

# Default command - run demo
CMD ["python", "examples/simple_demo.py"]
