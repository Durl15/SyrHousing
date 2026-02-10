FROM python:3.12-slim

WORKDIR /app

# Install system deps for bcrypt and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psycopg2-binary gunicorn

COPY . ./backend/
# Create empty __init__ at app root so "backend" is a package
RUN touch __init__.py

# Create data directory for SQLite (if used)
RUN mkdir -p /data

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:////data/syrhousing.db

EXPOSE 8000

CMD ["gunicorn", "backend.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120"]
