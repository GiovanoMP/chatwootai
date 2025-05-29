FROM node:18-slim

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de configuração
COPY package*.json ./

# Instalar dependências
RUN npm install

# Copiar código fonte
COPY src ./src

# Expor porta
EXPOSE 8000

# Configurar variáveis de ambiente para multi-tenant
ENV MULTI_TENANT=true
ENV PORT=8000
ENV DEFAULT_TENANT=account_1
ENV MAX_RESULTS=100
ENV ALLOWED_COLLECTIONS=company_services,tenants,configurations

# Comando para iniciar o servidor
CMD ["npm", "start"]
