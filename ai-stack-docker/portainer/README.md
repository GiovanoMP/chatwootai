# Portainer CE para ChatwootAI

Este diretório contém a configuração do Portainer Community Edition para gerenciamento de contêineres Docker do projeto ChatwootAI.

## Informações de Acesso

- **URL de acesso**: http://localhost:9000
- **Usuário inicial**: Será criado no primeiro acesso
- **Senha**: Defina uma senha forte no primeiro acesso (mínimo 12 caracteres)

## Inicialização

### Usando o script de inicialização

O método recomendado para iniciar o Portainer é usando o script `start.sh`:

```bash
# Navegue até o diretório do Portainer
cd /home/giovano/Projetos/ai_stack/ai-stack/portainer

# Execute o script de inicialização
./start.sh
```

Este script irá:
1. Verificar se a rede Docker `ai-stack` existe e criá-la se necessário
2. Iniciar o serviço Portainer usando docker-compose

### Inicialização manual

Se preferir iniciar manualmente:

```bash
# Navegue até o diretório do Portainer
cd /home/giovano/Projetos/ai_stack/ai-stack/portainer

# Verifique se a rede ai-stack existe
cd ..
./network.sh
cd portainer

# Inicie o Portainer
docker-compose up -d
```

## Parando o serviço

Para parar o serviço Portainer:

```bash
# Navegue até o diretório do Portainer
cd /home/giovano/Projetos/ai_stack/ai-stack/portainer

# Pare o serviço
docker-compose down
```

## Reiniciando o serviço

Para reiniciar o serviço Portainer:

```bash
# Navegue até o diretório do Portainer
cd /home/giovano/Projetos/ai_stack/ai-stack/portainer

# Pare e inicie o serviço
docker-compose down
docker-compose up -d
```

## Recursos

- Interface web para gerenciamento de contêineres Docker
- Monitoramento de recursos (CPU, memória)
- Gerenciamento de volumes e redes
- Visualização de logs
- Acesso ao terminal dos contêineres

## Notas

- O Portainer tem acesso ao socket do Docker, o que lhe dá controle total sobre o ambiente Docker
- As configurações e dados do Portainer são persistidos no volume `portainer_data`
- O contêiner é configurado com a opção `no-new-privileges:true` para maior segurança
