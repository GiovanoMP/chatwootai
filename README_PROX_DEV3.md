# Documentação para o Próximo Desenvolvedor

## Visão Geral do Projeto

Este projeto implementa um sistema de atendimento ao cliente baseado em IA, integrando CrewAI com Qdrant para fornecer respostas precisas e factuais aos clientes. O sistema é projetado para ser multi-tenant, permitindo que diferentes contas (empresas) utilizem a mesma infraestrutura com seus próprios dados isolados.

## Objetivo Atual

Estamos trabalhando na implementação de uma solução otimizada para consulta ao Qdrant usando CrewAI, com foco em:

1. **Prevenção de Alucinações**: Garantir que as respostas sejam baseadas APENAS nos dados existentes no Qdrant, sem inventar informações.
2. **Baixa Latência**: Garantir que as respostas sejam entregues em menos de 3 segundos.
3. **Arquitetura Profissional**: Implementar uma arquitetura bem estruturada seguindo as melhores práticas do CrewAI.

## Componentes Principais

### 1. Ferramentas de Busca no Qdrant

Implementamos várias versões de ferramentas para busca no Qdrant:

- **QdrantMultiTenantSearchTool**: Ferramenta original para busca no Qdrant.
- **FastQdrantSearchTool**: Versão otimizada para baixa latência.
- **OptimizedQdrantTool**: Versão mais recente, seguindo a documentação oficial do CrewAI.

### 2. Agentes CrewAI

Implementamos diferentes abordagens para os agentes:

- **Agente Único**: Um único agente especializado em atendimento ao cliente.
- **Múltiplos Agentes**: Tentativa de implementar agentes especializados para diferentes coleções.

### 3. Scripts de Teste

Criamos scripts para testar as diferentes implementações:

- **test_fast_response.py**: Testa a implementação com FastQdrantSearchTool.
- **test_simple_response.py**: Testa a implementação simplificada com o decorador @tool.
- **test_optimized_response.py**: Testa a implementação otimizada com OptimizedQdrantTool.

## Dificuldades Encontradas

### 1. Alucinações do Modelo

O problema principal que estamos tentando resolver é a tendência do modelo de "alucinar" - inventar informações que não existem nos dados do Qdrant. Isso é inaceitável para um sistema de atendimento ao cliente, pois pode levar a informações incorretas sendo fornecidas aos clientes.

Tentamos várias abordagens para mitigar esse problema:
- Instruções explícitas no prompt para não inventar informações
- Temperatura baixa (0.0) para reduzir a criatividade do modelo
- Citação de fontes para cada informação
- Verificação de confiança nas respostas

### 2. Latência Alta

Outro desafio significativo é garantir que as respostas sejam entregues em menos de 3 segundos. Isso é difícil devido a:

- Tempo de geração de embeddings
- Tempo de busca no Qdrant
- Tempo de processamento do modelo LLM
- Overhead de comunicação entre agentes

Tentamos várias otimizações:
- Cache de embeddings
- Timeout reduzido para chamadas ao Qdrant
- Limite de tokens na resposta
- Execução direta da tarefa em vez de usar uma crew completa

### 3. Integração com CrewAI

Enfrentamos desafios na integração correta com o CrewAI:

- Implementação correta de ferramentas personalizadas (BaseTool)
- Configuração adequada de agentes e tarefas
- Uso eficiente da API do CrewAI

## Estado Atual

Atualmente, temos uma implementação funcional, mas ainda estamos enfrentando desafios:

1. **Latência**: Ainda estamos acima do limite de 3 segundos em alguns casos.
2. **Alucinações**: Melhoramos significativamente, mas ainda pode ocorrer em casos específicos.
3. **Robustez**: Precisamos melhorar a robustez da solução para lidar com diferentes tipos de consultas.

## Próximos Passos

1. **Otimização Adicional de Latência**:
   - Implementar cache em nível de aplicação para consultas frequentes
   - Otimizar ainda mais os prompts para reduzir o tempo de processamento

2. **Melhoria na Prevenção de Alucinações**:
   - Implementar verificação de fatos nas respostas
   - Adicionar exemplos específicos de respostas corretas no prompt

3. **Testes Abrangentes**:
   - Testar com diferentes tipos de consultas
   - Medir precisão e latência em diferentes cenários

## Documentos Importantes

Para se contextualizar com o projeto, recomendamos a leitura dos seguintes documentos:

### Documentação do CrewAI

1. **[Documentação Oficial do CrewAI](https://docs.crewai.com/introduction)**: Visão geral do CrewAI.
2. **[Ferramentas no CrewAI](https://docs.crewai.com/concepts/tools)**: Como implementar e usar ferramentas.
3. **[Criação de Ferramentas Personalizadas](https://docs.crewai.com/how-to/create-custom-tools)**: Guia para criar ferramentas personalizadas.
4. **[QdrantVectorSearchTool](https://docs.crewai.com/tools/qdrantvectorsearchtool)**: Documentação específica da ferramenta para Qdrant.

### Documentação do Qdrant

1. **[Documentação Oficial do Qdrant](https://qdrant.tech/documentation/)**: Visão geral do Qdrant.
2. **[API Python do Qdrant](https://qdrant.github.io/qdrant-client/)**: Documentação da API Python.

### Arquivos do Projeto

1. **`crew_tests/tools/optimized_qdrant_tool.py`**: Implementação otimizada da ferramenta para Qdrant.
2. **`crew_tests/agents/optimized_agent.py`**: Implementação do agente otimizado.
3. **`test_optimized_response.py`**: Script para testar a implementação otimizada.
4. **`config.py`**: Configurações do projeto, incluindo URLs e chaves de API.

## Configuração do Ambiente

Para executar o projeto, você precisa:

1. **Qdrant**: Um servidor Qdrant rodando (por padrão em http://localhost:6333).
2. **OpenAI API Key**: Uma chave de API válida da OpenAI configurada no arquivo `.env`.
3. **Dependências Python**: Instalar as dependências necessárias (crewai, qdrant-client, openai).

## Exemplos de Uso

Para testar a implementação otimizada:

```bash
python test_optimized_response.py --query "Vocês têm alguma promoção de shampoo?"
```

Para executar um benchmark com múltiplas consultas:

```bash
python test_optimized_response.py --benchmark
```

## Notas Adicionais

- O sistema está configurado para usar o modelo `gpt-4o-mini` da OpenAI, que oferece um bom equilíbrio entre qualidade e velocidade.
- As coleções no Qdrant são separadas por `account_id` para garantir o isolamento de dados entre diferentes clientes.
- O sistema prioriza regras temporárias (promoções) sobre regras permanentes quando relevante para a consulta.

## Contato

Se você tiver dúvidas ou precisar de esclarecimentos adicionais, entre em contato com a equipe de desenvolvimento.

---

Esperamos que esta documentação ajude você a entender o estado atual do projeto e os desafios que estamos enfrentando. Boa sorte com o desenvolvimento!
