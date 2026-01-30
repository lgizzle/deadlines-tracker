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
# Build-time placeholders - real secrets injected at runtime via Cloud Run Secret Manager
# WARNING: These are build-time only placeholders, NOT production secrets
RUN SECRET_KEY=build-time-placeholder-not-a-real-secret-key-12345678901234567890 \
    FIELD_ENCRYPTION_KEY=HU_uPaDsI6UzYYQO9KQjsPUIhxy0jIveJVyTMige9qE= \
    python manage.py collectstatic --noinput

# Run gunicorn
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 bizops.wsgi:application
