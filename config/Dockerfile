FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código-fonte
COPY . .

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Porta para expor (se necessário)
# EXPOSE 8080

# Comando para iniciar o serviço
CMD ["python", "src/main.py"]
