# Use official Python runtime
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Tesseract + build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libtiff5 \
    libopenjp2-7 \
    gcc \
    build-essential \
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

# Start Gunicorn server with higher timeout for OCR
ENV WEB_CONCURRENCY=1
ENV GUNICORN_CMD_ARGS="--timeout 120 --workers 1 --threads 2 --log-file -"
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "restapi_project.wsgi:application"]
