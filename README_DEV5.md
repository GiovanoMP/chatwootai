# Documentação de Desenvolvimento - Versão 5

## Status Atual do Projeto

O sistema de integração Chatwoot-CrewAI está funcional, mas com algumas limitações e áreas que precisam de otimização:

1. **Tempo de Resposta**: Atualmente em torno de 15-26 segundos (objetivo: 3 segundos)
2. **Problemas com Redis**: Conexão com Redis não está funcionando corretamente
3. **Integração WhatsApp**: Temporariamente usando um simulador enquanto a API da Meta está sendo configurada

## Principais Componentes

- **Webhook Handler**: Recebe mensagens do Chatwoot e as processa
- **Hub**: Gerencia o roteamento de mensagens para as crews apropriadas
- **Crews**: Conjuntos de agentes especializados para diferentes domínios
- **Chatwoot Client**: Envia respostas de volta para o Chatwoot

## Melhorias Recentes

1. **Correção de URL**: Resolvido problema com URL incorreta (chatwoot.efetivia.com.br → chat.sprintia.com.br)
   - Removido arquivo `instances.json` que continha referências ao domínio antigo
   
2. **Simulador de WhatsApp**: Criado para testes enquanto a API da Meta está indisponível
   - Disponível em: `http://localhost:8080/simple_simulator.html`
   - Permite testar o sistema sem depender da API da Meta
   - Envia mensagens no formato correto que o webhook handler espera

3. **Arquitetura Simplificada**: Implementada nova arquitetura hub-and-spoke
   - Todas as mensagens são direcionadas para a `customer_service_crew`
   - Configuração baseada em account_id para multitenancy

## Problemas Conhecidos

1. **Redis**: Erro de conexão com Redis
   ```
   Error 111 connecting to localhost:6379. Connection refused.
   ```
   - O sistema continua funcionando sem Redis, mas não está utilizando cache

2. **Tempo de Resposta**: Muito acima do objetivo de 3 segundos
   - Atualmente: 15-26 segundos
   - Gargalos não identificados completamente

3. **API da Meta**: Integração com WhatsApp oficial temporariamente indisponível
   - Usando simulador para testes

## Próximos Passos

### Prioridade Alta

1. **Otimização de Desempenho**:
   - Identificar gargalos específicos no processamento de mensagens
   - Implementar profiling detalhado para cada etapa do processamento
   - Otimizar agentes para reduzir tempo de resposta

2. **Correção do Redis**:
   - Verificar configuração do Redis
   - Implementar fallback adequado quando Redis não estiver disponível
   - Garantir que o sistema use cache quando disponível

3. **Multitenancy**:
   - Melhorar a implementação de multitenancy baseada em account_id
   - Garantir isolamento adequado de dados entre clientes

### Prioridade Média

1. **Documentação**:
   - Documentar a nova arquitetura hub-and-spoke
   - Criar diagramas de fluxo para o processamento de mensagens

2. **Testes**:
   - Implementar testes automatizados para diferentes cenários
   - Criar testes de carga para verificar desempenho

3. **Integração com API da Meta**:
   - Restaurar integração com WhatsApp oficial quando disponível
   - Garantir transição suave do simulador para a API real

### Prioridade Baixa

1. **Interface de Administração**:
   - Criar interface para gerenciar configurações
   - Implementar dashboard para monitoramento

2. **Logging Aprimorado**:
   - Melhorar sistema de logs para facilitar diagnóstico
   - Implementar alertas para erros críticos

## Como Executar o Sistema

1. **Iniciar o Servidor**:
   ```bash
   cd /home/giovano/Projetos/Chatwoot\ V4 && ./scripts/restart_and_monitor.sh
   ```

2. **Iniciar o Simulador** (para testes sem WhatsApp):
   ```bash
   ./start_simple_simulator.sh
   ```
   Acesse: `http://localhost:8080/simple_simulator.html`

## Notas Adicionais

- O sistema está configurado para usar a URL `https://chat.sprintia.com.br/api/v1` para comunicação com o Chatwoot
- As configurações de cada cliente (tenant) são baseadas no `account_id` do Chatwoot
- O webhook handler espera mensagens no formato específico com campo `message` separado

## Contatos

Para mais informações, entre em contato com:
- Email: giovano@sprintia.com.br
