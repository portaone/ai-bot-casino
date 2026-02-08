FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run Jobs send SIGTERM on timeout; bot handles it gracefully
STOPSIGNAL SIGTERM

ENTRYPOINT ["python", "bot.py"]
