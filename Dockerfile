FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable instant log flushing
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for ChromaDB (C++ compiler) and PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Leverage Docker layer caching: install Python packages before copying source code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application files
COPY ingest.py store.py graph.py database.py main.py ./

# Create persistent storage directory for ChromaDB vectors inside container
RUN mkdir -p /app/chroma_data

EXPOSE 8000

# Exec form for clean shutdown signal propagation
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]