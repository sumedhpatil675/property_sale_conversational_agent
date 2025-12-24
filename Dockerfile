FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Download embedding model during build to prevent timeouts at runtime
RUN python scripts/download_model.py && rm -rf tmp_chroma_db_dl

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && python scripts/import_properties.py && gunicorn core.wsgi:application --bind 0.0.0.0:10000"]

