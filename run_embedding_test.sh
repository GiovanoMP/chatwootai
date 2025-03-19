#!/bin/bash
# Script para executar o teste de otimização de embeddings

# Carregar variáveis de ambiente
echo "Carregando variáveis de ambiente..."
source .env

# Verificar se a chave da API da OpenAI está definida
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERRO: A variável OPENAI_API_KEY não está definida no arquivo .env"
    echo "Por favor, adicione sua chave da API da OpenAI ao arquivo .env"
    exit 1
fi

# Verificar se a URL do Redis está definida
if [ -z "$REDIS_URL" ]; then
    echo "AVISO: A variável REDIS_URL não está definida no arquivo .env"
    echo "O teste de cache não funcionará corretamente sem uma conexão Redis"
    echo "Recomendamos adicionar REDIS_URL=redis://localhost:6379/0 ao arquivo .env"
fi

# Executar o teste
echo "Executando teste de otimização de embeddings..."
python tests/test_embedding_optimization.py

# Verificar o resultado
if [ $? -eq 0 ]; then
    echo "Teste concluído com sucesso!"
else
    echo "Teste falhou. Verifique os erros acima."
fi
