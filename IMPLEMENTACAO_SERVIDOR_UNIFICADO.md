# Implementação do Servidor Unificado

Este documento descreve a implementação do servidor unificado para o Sistema Integrado Odoo-AI, que combina o webhook do Chatwoot e a API Odoo em um único aplicativo FastAPI.

## Arquivos Criados/Modificados

### Novos Arquivos

1. **`main.py`** - Servidor unificado principal
2. **`src/webhook/routes.py`** - Rotas do webhook
3. **`src/webhook/init.py`** - Inicialização do webhook
4. **`scripts/start_unified_server.py`** - Script para iniciar o servidor unificado
5. **`scripts/start_ngrok_unified.py`** - Script para iniciar o Ngrok com o servidor unificado
6. **`docs/UNIFIED_SERVER.md`** - Documentação do servidor unificado
7. **`scripts/make_scripts_executable.sh`** - Script para tornar os scripts executáveis

### Arquivos Modificados

1. **`ARCHITECTURE.md`** - Atualizado para refletir a nova arquitetura unificada

## Como Testar a Implementação

### Passo 1: Tornar os Scripts Executáveis

```bash
# A partir da raiz do projeto
chmod +x scripts/make_scripts_executable.sh
./scripts/make_scripts_executable.sh
```

### Passo 2: Iniciar o Servidor Unificado

```bash
# A partir da raiz do projeto
./scripts/start_unified_server.py
```

O servidor unificado será iniciado na porta 8000 (ou na porta especificada na variável de ambiente `SERVER_PORT`).

### Passo 3: Iniciar o Ngrok

Em outro terminal:

```bash
# A partir da raiz do projeto
./scripts/start_ngrok_unified.py
```

O Ngrok criará um túnel para o servidor unificado e exibirá a URL pública.

### Passo 4: Atualizar a Configuração na VPS

Siga as instruções fornecidas pelo script `start_ngrok_unified.py` para atualizar a configuração na VPS.

### Passo 5: Testar o Webhook do Chatwoot

Envie uma mensagem pelo WhatsApp para o número configurado no Chatwoot e verifique se o webhook está funcionando corretamente.

### Passo 6: Testar a API Odoo

Acesse o módulo Odoo e tente sincronizar regras de negócio ou produtos. Verifique se a API está funcionando corretamente.

## Verificação de Logs

Os logs do sistema são armazenados no diretório `logs/`:

```bash
# Verificar logs do servidor unificado
tail -f logs/YYYYMMDD_unified_server.log

# Verificar logs do webhook
tail -f logs/webhook.log

# Verificar logs do hub
tail -f logs/hub.log
```

## Solução de Problemas

### Problema: O servidor não inicia

Verifique se todas as dependências estão instaladas:

```bash
pip install -r requirements.txt
```

### Problema: O Ngrok não conecta

Verifique se o token de autenticação do Ngrok está configurado corretamente no arquivo `.env`.

### Problema: O módulo Odoo não consegue acessar o endpoint

Verifique se a URL do Ngrok está configurada corretamente na VPS e se o módulo Odoo está usando a URL correta.

## Próximos Passos

1. Implementar testes automatizados para o servidor unificado
2. Melhorar o monitoramento e logging
3. Adicionar autenticação para endpoints da API
4. Considerar a migração para uma arquitetura de microserviços no futuro
