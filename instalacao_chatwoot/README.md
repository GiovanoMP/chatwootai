# Instalação do Chatwoot com WhatsApp Business API

Este diretório contém arquivos de configuração e scripts para instalar o Chatwoot em um ambiente Docker Swarm, com suporte para integração com a API oficial do WhatsApp Business.

## Localização dos Arquivos na VPS

- **Diretório principal da instalação**: `/opt/chatwoot_evolution_nova/`
- **Arquivos de configuração**: `/opt/chatwoot_evolution_nova/*.yaml`
- **Scripts**: `/opt/chatwoot_evolution_nova/*.sh`
- **Volumes Docker**:
  - Chatwoot: `/var/lib/docker/volumes/chatwoot_*`
  - PostgreSQL: `/var/lib/docker/volumes/postgres_data`
  - Redis: `/var/lib/docker/volumes/redis_data`

## Arquivos de Configuração

- `1 - traefik.yaml`: Configuração do Traefik (proxy reverso)
- `2 - portainer.yaml`: Configuração do Portainer (gerenciamento de contêineres)
- `3 - redis.yaml`: Configuração do Redis (cache)
- `4 - postgres.yaml`: Configuração do PostgreSQL (banco de dados)
- `5 - chatwoot_v4.yaml`: Configuração do Chatwoot v4.0.3

## Scripts

- `instalar.sh`: Script para remover a instalação atual e configurar uma nova
- `verificar_status.sh`: Script para verificar o status dos serviços

## Pré-requisitos

- Docker Swarm inicializado
- Domínio configurado para apontar para o servidor:
  - chat.sprintia.com.br
- Portas 80 e 443 abertas no firewall
- Conta no Meta Business para WhatsApp Business API (para integração com WhatsApp)

## Instruções de Instalação

1. Verifique e ajuste as configurações nos arquivos YAML conforme necessário
2. Execute o script de instalação:

```bash
./instalar.sh
```

3. Após a instalação, configure o Chatwoot:

```bash
docker exec -it $(docker ps | grep chatwoot_app | awk '{print $1}') bundle exec rails db:chatwoot_prepare
```

4. Verifique o status dos serviços:

```bash
./verificar_status.sh
```

5. Configure a integração com WhatsApp Business API:
   - Acesse o Chatwoot: https://chat.sprintia.com.br
   - Vá para Configurações > Caixas de Entrada > Adicionar Caixa de Entrada
   - Selecione WhatsApp
   - Siga as instruções para conectar com a API oficial do WhatsApp Business
   - Certifique-se de que a política de privacidade está disponível em: https://chat.sprintia.com.br/politicadeprivacidade/

## Acesso

- Chatwoot: https://chat.sprintia.com.br

## Solução de Problemas

Se encontrar problemas com a conexão do WhatsApp:

1. Verifique os logs do Chatwoot:
   ```bash
   docker service logs infra_chatwoot_app
   ```

2. Verifique os logs do Sidekiq (processamento em segundo plano):
   ```bash
   docker service logs infra_chatwoot_sidekiq
   ```

3. Problemas comuns:
   - Token de acesso expirado: Renove o token no painel do Meta for Developers
   - Webhook não configurado corretamente: Verifique as configurações do webhook no Meta Business
   - Política de privacidade inacessível: Certifique-se de que a página está disponível em https://chat.sprintia.com.br/politicadeprivacidade/

## Credenciais e Informações Importantes

### Banco de Dados
- **Senha do PostgreSQL**: `SprintiaDB2024!`
- **Usuário do PostgreSQL**: `postgres`
- **Banco de dados Chatwoot**: `chatwoot`

### Chatwoot
- **Versão**: `v4.0.3`
- **URL**: `https://chat.sprintia.com.br`
- **Senha inicial**: Criada durante o processo de configuração inicial em `https://chat.sprintia.com.br/installation/onboarding`
- **Obter token de API**: Após login, vá para Perfil → Configurações da API → Gerar token de API
- **Política de Privacidade**: `https://chat.sprintia.com.br/politicadeprivacidade/`

### WhatsApp Business API
- **Painel de Desenvolvedores**: [Meta for Developers](https://developers.facebook.com/)
- **Documentação**: [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- **Requisitos**: Política de privacidade, verificação de negócio no Meta Business

### Contêineres e Serviços
- **Verificar serviços**: `docker service ls`
- **Logs do Chatwoot**: `docker service logs infra_chatwoot_app`
- **Logs do Sidekiq**: `docker service logs infra_chatwoot_sidekiq`
- **Acessar shell do Chatwoot**: `docker exec -it $(docker ps | grep chatwoot_app | awk '{print $1}') bash`

### Comandos Úteis
- **Reiniciar Chatwoot**: `docker service update --force infra_chatwoot_app`
- **Reiniciar Sidekiq**: `docker service update --force infra_chatwoot_sidekiq`
- **Verificar status completo**: `./verificar_status.sh`
