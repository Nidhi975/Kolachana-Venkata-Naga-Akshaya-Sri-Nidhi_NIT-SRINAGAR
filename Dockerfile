# Use full Debian-based Python image so language packs install reliably
FROM python:3.10

# Keep Python from writing .pyc files and make output unbuffered (good for logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (Tesseract, poppler) and current Mesa packages
# Note: libgl1-mesa-glx is obsolete on recent Debian/Ubuntu — use libglx-mesa0 + libgl1-mesa-dri (or libgl1).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      tesseract-ocr-eng \
      libglx-mesa0 \
      libgl1-mesa-dri \
      libglib2.0-0 \
      poppler-utils \
 && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ ./app/

# Create runtime dirs and a non-root user
RUN mkdir -p /app/temp /app/outputs \
 && useradd --create-home --system --shell /usr/sbin/nologin appuser \
 && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
