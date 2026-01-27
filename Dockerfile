# Use official Python runtime
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
# Provide a placeholder encryption key during build (collectstatic doesn't encrypt data)
# The real key is injected at runtime via Cloud Run secrets
RUN FIELD_ENCRYPTION_KEY=nPMQFDQoYc972n7SIzQ_B6iAeztx10FVQ154nKC0h6M= python manage.py collectstatic --noinput

# Run gunicorn
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 bizops.wsgi:application
