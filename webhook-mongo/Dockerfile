FROM python:3.10-slim

WORKDIR /app

# Instalar dependências específicas para garantir compatibilidade
RUN pip install --no-cache-dir "pymongo<4.0.0" "motor<3.0.0" fastapi uvicorn pydantic pyyaml

# Copiar código
COPY . .

# Expor porta
EXPOSE 8003

# Comando para iniciar o serviço
CMD ["python", "webhook_app.py"]
