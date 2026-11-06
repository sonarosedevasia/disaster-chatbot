# SafeKerala / DisasterSafe - Production Dockerfile
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Set working directory
WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 disasterapp && \
    chown -R disasterapp:disasterapp /app
USER disasterapp

# Expose web server port
EXPOSE 5000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/api/health').getcode() == 200 else 1)" || exit 1

# Launch Flask application
CMD ["python", "app.py"]

