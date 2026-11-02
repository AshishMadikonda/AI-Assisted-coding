FROM python:3.12-slim

WORKDIR /app

# Install the Python packages first, so Docker can reuse this layer when only code changes
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the project (see .dockerignore for what is left out)
COPY ai ai
COPY backend backend
COPY frontend frontend

WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Hosting platforms such as Render give the port in the PORT variable. Locally it falls back to 8000.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]