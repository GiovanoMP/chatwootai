FROM python:3.10-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar curl para healthcheck e outras ferramentas úteis
RUN apt-get update && \
    apt-get install -y curl procps net-tools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Criar diretório para logs
RUN mkdir -p /app/logs

# Copiar código da aplicação
COPY . .

# Tornar o script de entrypoint executável
RUN chmod +x /app/docker-entrypoint.sh

# Expor portas
EXPOSE 8004
EXPOSE 8080

# Configurar variáveis de ambiente
ENV MCP_PORT=8004
ENV MCP_HOST=0.0.0.0

# Usar o script de entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
