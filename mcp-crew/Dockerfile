FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copiar arquivos de requisitos
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY . .

# Expor porta
EXPOSE 5000

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV MULTI_TENANT=true
ENV DEFAULT_TENANT=account_1

# Comando para iniciar o servidor
CMD ["python", "start.py"]
