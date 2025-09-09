# Use official Python runtime
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Tesseract + build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage caching properly
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the project
COPY . .

# Run collectstatic (for whitenoise)
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Start Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--log-file", "-", "restapi_project.wsgi:application"]
