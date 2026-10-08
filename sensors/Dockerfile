FROM python:3.12-slim-bullseye
ENV PYTHONUNBUFFERED=1

WORKDIR /app 

COPY sensors/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sensors/ .
CMD ["python", "simulator.py"]