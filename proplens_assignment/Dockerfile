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

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && python scripts/import_leads.py && gunicorn core.wsgi:application --bind 0.0.0.0:10000"]

