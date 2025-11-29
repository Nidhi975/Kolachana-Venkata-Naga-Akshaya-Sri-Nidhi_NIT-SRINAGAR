# Dockerfile (updated)
FROM python:3.10

# Prevent Python from writing .pyc files and buffer output (useful for logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (Tesseract + poppler for PDFs + minimal GL libs)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      tesseract-ocr-eng \
      libgl1-mesa-glx \
      libglib2.0-0 \
      poppler-utils \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create necessary dirs and a non-root user, set ownership
RUN mkdir -p /app/temp /app/outputs \
 && useradd --create-home --shell /bin/false appuser \
 && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
