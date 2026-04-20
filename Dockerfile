FROM python:3.11-slim

WORKDIR /app

COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt

COPY backend/ ./backend/
COPY config/ ./config/

EXPOSE 5005

ENV JWT_SECRET_KEY=""
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "backend.deploy"]
