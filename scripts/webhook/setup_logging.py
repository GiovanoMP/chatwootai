#!/usr/bin/env python3
"""
Script para configurar o sistema de logs do webhook e do hub.py

Este script:
1. Cria os arquivos de log necessários
2. Configura o formato dos logs
3. Testa o sistema de logs
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Configurar diretório de logs
def setup_log_directory():
    """Cria o diretório de logs se não existir."""
    log_dir = Path("logs")
    if not log_dir.exists():
        print(f"📁 Criando diretório de logs: {log_dir}")
        log_dir.mkdir(parents=True)
    return log_dir

# Configurar arquivos de log
def setup_log_files(log_dir):
    """Cria os arquivos de log se não existirem."""
    webhook_log = log_dir / "webhook.log"
    hub_log = log_dir / "hub.log"
    
    # Criar arquivos de log vazios se não existirem
    for log_file in [webhook_log, hub_log]:
        if not log_file.exists():
            print(f"📄 Criando arquivo de log: {log_file}")
            with open(log_file, 'w') as f:
                f.write(f"# Log iniciado em {datetime.now().isoformat()}\n")
    
    return webhook_log, hub_log

# Configurar logger para webhook
def setup_webhook_logger(log_file):
    """Configura o logger para o webhook."""
    logger = logging.getLogger('webhook')
    logger.setLevel(logging.DEBUG)
    
    # Configurar handler para arquivo
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Configurar formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Adicionar handler ao logger
    logger.addHandler(file_handler)
    
    return logger

# Configurar logger para hub
def setup_hub_logger(log_file):
    """Configura o logger para o hub."""
    logger = logging.getLogger('hub')
    logger.setLevel(logging.DEBUG)
    
    # Configurar handler para arquivo
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Configurar formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Adicionar handler ao logger
    logger.addHandler(file_handler)
    
    return logger

# Testar loggers
def test_loggers(webhook_logger, hub_logger):
    """Testa os loggers com mensagens de exemplo."""
    print("🧪 Testando loggers com mensagens de exemplo...")
    
    # Exemplo de mensagem do Chatwoot
    example_message = {
        "event": "message_created",
        "account": {"id": 1},
        "message": {
            "id": 123456,
            "content": "Olá, gostaria de informações sobre produtos.",
            "message_type": 0,
            "content_type": "text"
        },
        "conversation": {"id": 789012, "inbox_id": 345678},
        "contact": {"id": 901234, "name": "Cliente Teste"}
    }
    
    # Simular recebimento de mensagem no webhook
    webhook_logger.info("Servidor webhook iniciado na porta 8001")
    webhook_logger.info(f"Mensagem recebida do Chatwoot: conversation_id={example_message['conversation']['id']}")
    webhook_logger.debug(f"Conteúdo da mensagem: {json.dumps(example_message)}")
    webhook_logger.info("Encaminhando mensagem para o hub.py")
    
    # Simular processamento no hub
    hub_logger.info("HubCrew inicializado e pronto para processar mensagens")
    hub_logger.info(f"Mensagem recebida do webhook: conversation_id={example_message['conversation']['id']}")
    hub_logger.info("OrchestratorAgent analisando intenção da mensagem")
    hub_logger.info("Intenção detectada: consulta_produto")
    hub_logger.info("Encaminhando para SalesCrew")
    hub_logger.info("SalesCrew processando mensagem")
    hub_logger.info("DataProxyAgent consultando informações de produtos")
    hub_logger.info("Resposta gerada: 'Temos vários produtos disponíveis. Poderia especificar qual categoria lhe interessa?'")
    hub_logger.info("Enviando resposta para o Chatwoot")
    
    print("✅ Logs de teste gerados com sucesso!")

# Criar instruções para o arquivo README
def create_logging_instructions():
    """Cria instruções para configurar logs nos arquivos do projeto."""
    instructions = """
# Instruções para Configurar Logs no Projeto

Para adicionar logs detalhados ao servidor webhook e ao hub.py, siga estas instruções:

## 1. No arquivo src/webhook/server.py

Adicione o seguinte código no início do arquivo:

```python
import logging

# Configurar logger
logger = logging.getLogger('webhook')
```

E utilize o logger em pontos importantes do código:

```python
# Ao iniciar o servidor
logger.info(f"Servidor webhook iniciado na porta {port}")

# Ao receber uma mensagem
logger.info(f"Mensagem recebida: conversation_id={data['conversation']['id']}")
logger.debug(f"Conteúdo da mensagem: {json.dumps(data)}")

# Ao encaminhar para o hub
logger.info(f"Encaminhando mensagem para o hub.py")

# Em caso de erro
logger.error(f"Erro ao processar mensagem: {str(e)}")
```

## 2. No arquivo src/core/hub.py

Adicione o seguinte código no início do arquivo:

```python
import logging

# Configurar logger
logger = logging.getLogger('hub')
```

E utilize o logger em pontos importantes do código:

```python
# Ao inicializar o HubCrew
logger.info("HubCrew inicializado")

# Ao receber uma mensagem
logger.info(f"Mensagem recebida: conversation_id={conversation_id}")

# Ao detectar intenção
logger.info(f"Intenção detectada: {intent}")

# Ao encaminhar para uma crew especializada
logger.info(f"Encaminhando para {crew_name}")

# Ao gerar resposta
logger.info(f"Resposta gerada: {response[:50]}...")

# Ao enviar resposta
logger.info(f"Enviando resposta para o Chatwoot")
```

## 3. Monitoramento de Logs

Para monitorar os logs em tempo real, utilize o script:

```bash
python scripts/webhook/monitor_webhook_logs.py
```

Você pode filtrar e destacar termos específicos:

```bash
python scripts/webhook/monitor_webhook_logs.py --highlight "conversation_id=123456"
```

Ou filtrar por nível de log:

```bash
python scripts/webhook/monitor_webhook_logs.py --level warning
```
"""
    
    # Escrever instruções em um arquivo
    with open("logs/logging_instructions.md", "w") as f:
        f.write(instructions)
    
    print("📝 Instruções para configurar logs criadas em logs/logging_instructions.md")

def main():
    """Função principal."""
    print("\n" + "="*80)
    print("🔧 CONFIGURAÇÃO DO SISTEMA DE LOGS")
    print("="*80)
    
    # Configurar diretório e arquivos de log
    log_dir = setup_log_directory()
    webhook_log, hub_log = setup_log_files(log_dir)
    
    # Configurar loggers
    webhook_logger = setup_webhook_logger(webhook_log)
    hub_logger = setup_hub_logger(hub_log)
    
    # Testar loggers
    test_loggers(webhook_logger, hub_logger)
    
    # Criar instruções
    create_logging_instructions()
    
    print("\n" + "="*80)
    print("✅ CONFIGURAÇÃO CONCLUÍDA")
    print("="*80)
    print(f"📁 Diretório de logs: {log_dir}")
    print(f"📄 Log do webhook: {webhook_log}")
    print(f"📄 Log do hub: {hub_log}")
    print(f"📝 Instruções: logs/logging_instructions.md")
    print("\n🚀 Para monitorar os logs, execute:")
    print("   python scripts/webhook/monitor_webhook_logs.py")
    print("="*80)

if __name__ == "__main__":
    main()
