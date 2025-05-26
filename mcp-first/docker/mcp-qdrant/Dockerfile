FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Clonar o repositório oficial do MCP-Qdrant
RUN git clone https://github.com/qdrant/mcp-server-qdrant.git . \
    && pip install --no-cache-dir -r requirements.txt

# Expor porta
EXPOSE 8000

# Configurar variáveis de ambiente
ENV QDRANT_URL=http://qdrant:6333
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=8000
ENV MCP_HOST=0.0.0.0

# Comando para iniciar o servidor
CMD ["python", "-m", "mcp_server_qdrant"]
