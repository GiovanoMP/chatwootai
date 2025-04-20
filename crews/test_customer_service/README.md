# Crew de Teste para Atendimento ao Cliente

Esta crew demonstra como usar o CrewAI para melhorar o atendimento ao cliente usando agentes especializados e ferramentas personalizadas.

## Estrutura

A crew é composta por três agentes especializados:

1. **Agente de Busca de Dados**: Responsável por buscar informações relevantes no banco de dados vetorial Qdrant.
2. **Agente de Processamento de Regras**: Responsável por analisar e priorizar regras de negócio.
3. **Agente de Atendimento ao Cliente**: Responsável por gerar respostas amigáveis e precisas para os clientes.

## Ferramentas

A crew utiliza duas ferramentas personalizadas:

1. **VectorSearchTool**: Ferramenta para buscar informações no Qdrant.
2. **RuleProcessorTool**: Ferramenta para processar e priorizar regras de negócio.

## Fluxo de Trabalho

O fluxo de trabalho da crew é sequencial:

1. O Agente de Busca de Dados busca informações relevantes no Qdrant.
2. O Agente de Processamento de Regras analisa e prioriza as regras encontradas.
3. O Agente de Atendimento ao Cliente gera uma resposta com base nas informações processadas.

## Como Usar

Para usar a crew, execute o script `test_customer_service_crew.py`:

```bash
python test_customer_service_crew.py
```

Ou forneça uma consulta diretamente:

```bash
python test_customer_service_crew.py --query "Vocês têm alguma promoção de shampoo?"
```

## Comparação com o Simulador Anterior

Esta crew oferece várias vantagens em relação ao simulador anterior:

1. **Divisão de Responsabilidades**: Cada agente é especializado em uma tarefa específica.
2. **Ferramentas Personalizadas**: As ferramentas permitem que os agentes realizem tarefas específicas de forma eficiente.
3. **Fluxo de Trabalho Definido**: O fluxo de trabalho sequencial garante que cada etapa seja concluída antes da próxima.
4. **Contexto Compartilhado**: Os agentes compartilham informações entre si, mantendo um contexto consistente.

## Próximos Passos

1. **Melhorar as Ferramentas**: Adicionar mais funcionalidades às ferramentas existentes.
2. **Adicionar Mais Agentes**: Criar agentes especializados para tarefas específicas, como processamento de pedidos.
3. **Implementar Fluxos de Trabalho Mais Complexos**: Usar fluxos de trabalho hierárquicos para tarefas mais complexas.
4. **Integrar com Outros Sistemas**: Integrar a crew com outros sistemas, como Odoo e Chatwoot.
