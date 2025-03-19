FROM python:3.10-slim

WORKDIR /app

COPY webhook_server.py .
COPY .env .

RUN pip install fastapi uvicorn requests python-dotenv

EXPOSE 8002

CMD ["python", "webhook_server.py"]
