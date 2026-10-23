FROM python:3.10-slim

WORKDIR /app

# Install minimal build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install CPU PyTorch first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the MiniLM embedding model during build time so runtime startup is instant
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

# Render dynamically sets PORT environment variable (default 10000)
ENV PORT=10000
EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --timeout-keep-alive 120"]