FROM node:18-slim

WORKDIR /app

# Clonar o repositório oficial do MCP-MongoDB
RUN apt-get update && apt-get install -y git \
    && git clone https://github.com/mongodb-developer/mongodb-mcp-server.git . \
    && apt-get purge -y git && apt-get autoremove -y && apt-get clean

# Instalar dependências
RUN npm install

# Expor porta
EXPOSE 8000

# Configurar variáveis de ambiente para multi-tenant
ENV MULTI_TENANT=true

# Comando para iniciar o servidor
CMD ["npm", "start"]
