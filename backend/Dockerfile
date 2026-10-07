# FROM python:3.12-slim still works, but using 3.12-slim-bullseye is more specific and ensures compatibility with certain libraries
FROM python:3.12-slim-bullseye

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["python", "app.py"]

