# Uptime Kuma para ChatwootAI

Este diretório contém a configuração do Uptime Kuma para monitoramento de serviços do projeto ChatwootAI.

## Informações de Acesso

- **URL de acesso**: http://localhost:3001
- **Usuário inicial**: Será criado no primeiro acesso
- **Senha**: Defina uma senha forte no primeiro acesso

## Inicialização

### Inicialização com Docker Compose

```bash
# Navegue até o diretório do Uptime Kuma
cd /home/giovano/Projetos/ai_stack/ai-stack/uptime-kuma

# Verifique se a rede ai-stack existe
cd ..
./network.sh
cd uptime-kuma

# Inicie o Uptime Kuma
docker-compose up -d
```

## Parando o serviço

Para parar o serviço Uptime Kuma:

```bash
# Navegue até o diretório do Uptime Kuma
cd /home/giovano/Projetos/ai_stack/ai-stack/uptime-kuma

# Pare o serviço
docker-compose down
```

## Reiniciando o serviço

Para reiniciar o serviço Uptime Kuma:

```bash
# Navegue até o diretório do Uptime Kuma
cd /home/giovano/Projetos/ai_stack/ai-stack/uptime-kuma

# Pare e inicie o serviço
docker-compose down
docker-compose up -d
```

## Recursos

- Interface web para monitoramento de serviços
- Notificações por e-mail, Telegram, Discord, etc.
- Monitoramento de status HTTP, TCP, DNS, etc.
- Gráficos de tempo de resposta e disponibilidade
- Certificados SSL e expiração de domínio

## Segurança

- Configurado com `no-new-privileges:true` para maior segurança
- Dados persistidos em volume Docker dedicado
