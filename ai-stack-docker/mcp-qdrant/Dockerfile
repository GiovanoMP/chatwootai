FROM mcp-server-qdrant

# Instalar netcat para healthcheck
RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean

# Manter o comando padrão do container
CMD ["uvx", "mcp-server-qdrant"]
