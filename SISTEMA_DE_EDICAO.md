# Sistema de Edição de Dados Vetorizados

## Visão Geral

O Sistema de Edição de Dados Vetorizados é uma extensão do ecossistema Odoo-AI que permite aos usuários visualizar, editar e gerenciar dados que foram processados e vetorizados pelo sistema de IA. Esta funcionalidade proporciona transparência, controle e personalização sobre como os dados são interpretados e utilizados pelos agentes de IA.

## Objetivos

- **Transparência**: Permitir que os usuários vejam como seus dados são interpretados pelo sistema de IA
- **Controle**: Oferecer a capacidade de corrigir ou refinar o conteúdo vetorizado
- **Personalização**: Possibilitar ajustes finos que seriam difíceis de alcançar apenas através de configurações
- **Confiança**: Aumentar a confiança no sistema ao mostrar e permitir ajustes no que a IA "entende"

## Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Módulo Odoo    │     │  API REST       │     │  Sistema de IA  │
│  (Visualização) │◄────┤  (Endpoints)    │◄────┤  (Qdrant/LLM)   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Interface de   │     │  Controlador    │     │  Agentes de     │
│  Edição         │────►│  de Edição      │────►│  Embedding      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Componentes Principais

### 1. Módulo Odoo: `ai_vector_visualization`

Um novo módulo Odoo que fornece interfaces para visualização e edição de dados vetorizados:

- **Visualizações em Abas**: Para diferentes tipos de dados (metadados da empresa, configurações de atendimento, documentos de suporte, etc.)
- **Editor de Texto Rico**: Para edição de conteúdo
- **Controles de Modo de Edição**: Para escolher como o texto editado será processado
- **Histórico de Versões**: Para acompanhar mudanças ao longo do tempo

### 2. API REST: Endpoints de Visualização e Edição

#### Endpoints de Visualização (Existentes):
- `GET /api/v1/business-rules/processed/company-metadata`
- `GET /api/v1/business-rules/processed/service-config`
- `GET /api/v1/business-rules/processed/scheduling-rules`
- `GET /api/v1/business-rules/processed/support-documents`
- `GET /api/v1/business-rules/processed/support-document/{document_id}`

#### Novos Endpoints de Edição:
- `PUT /api/v1/business-rules/processed/company-metadata`
- `PUT /api/v1/business-rules/processed/service-config`
- `PUT /api/v1/business-rules/processed/support-document/{document_id}`

### 3. Agente de Edição de Vetores

Um novo agente especializado que gerencia o processo de edição e revetorização:

```python
class VectorEditAgent:
    async def process_edit(self, original_data, edited_data, edit_mode="exact"):
        if edit_mode == "exact":
            # Preservar exatamente como editado
            return edited_data
        elif edit_mode == "assisted":
            # Sugerir melhorias mas preservar intenção
            suggestions = await self._generate_suggestions(edited_data)
            return {"edited_data": edited_data, "suggestions": suggestions}
        elif edit_mode == "ai":
            # Processar completamente para otimizar
            return await self._optimize_for_vectorization(edited_data)
```

## Modos de Edição

O sistema oferece três modos de edição para atender a diferentes necessidades:

1. **Modo Exato**: Preserva exatamente o texto editado pelo usuário, sem processamento adicional pela IA
2. **Modo Assistido**: Sugere melhorias ao texto do usuário, mas permite que ele aceite ou rejeite as sugestões
3. **Modo IA**: Processa completamente o texto para otimizar a vetorização, ideal para conteúdo técnico complexo

## Versionamento e Histórico

O sistema mantém um histórico de versões dos dados vetorizados:

```json
{
    "account_id": "account_1",
    "metadata": { /* dados atuais */ },
    "original_text": "Texto original",
    "processed_text": "Texto editado",
    "ai_processed": false,
    "last_updated": "2025-04-19T20:15:30.123Z",
    "version": 2,
    "edit_history": [
        {
            "editor": "admin",
            "timestamp": "2025-04-19T20:15:30.123Z",
            "change_summary": "Edição manual",
            "edit_mode": "exact"
        },
        {
            "editor": "system",
            "timestamp": "2025-04-18T15:30:45.789Z",
            "change_summary": "Processamento inicial pela IA",
            "edit_mode": "ai"
        }
    ]
}
```

## Interface de Usuário

### Visualização Principal
- Seletor de tipo de dados (metadados, configurações, documentos)
- Lista de itens disponíveis
- Visualização detalhada do item selecionado

### Tela de Edição
- Editor de texto rico
- Seletor de modo de edição
- Visualização comparativa (original vs. processado vs. editado)
- Histórico de versões
- Indicador de qualidade de vetorização

## Fluxo de Trabalho

1. **Visualização**: O usuário acessa o módulo `ai_vector_visualization` e seleciona o tipo de dado que deseja visualizar
2. **Seleção**: O usuário escolhe um item específico da lista
3. **Análise**: O sistema exibe o conteúdo original, o conteúdo processado pela IA e metadados relevantes
4. **Edição**: O usuário seleciona o modo de edição e faz as alterações desejadas
5. **Revetorização**: Ao salvar, o sistema processa o texto conforme o modo selecionado e atualiza o vetor no Qdrant
6. **Confirmação**: O sistema exibe uma confirmação e atualiza a visualização com os novos dados

## Benefícios

- **Controle Humano**: Mantém o humano no ciclo de decisão (human-in-the-loop)
- **Qualidade de Dados**: Melhora a qualidade dos dados vetorizados através de supervisão humana
- **Personalização**: Permite ajustes específicos para casos de uso particulares
- **Transparência**: Torna o sistema de IA mais transparente e compreensível
- **Confiança**: Aumenta a confiança dos usuários no sistema

## Próximos Passos

1. **Protótipo Inicial**: Desenvolver um protótipo básico do módulo `ai_vector_visualization`
2. **Implementação dos Endpoints de Edição**: Criar os endpoints PUT para edição de dados
3. **Desenvolvimento do Agente de Edição**: Implementar o `VectorEditAgent`
4. **Testes com Dados Reais**: Testar o sistema com dados reais do Odoo e Qdrant
5. **Refinamento da Interface**: Melhorar a experiência do usuário com base no feedback
6. **Documentação**: Criar documentação detalhada para usuários e desenvolvedores

## Conclusão

O Sistema de Edição de Dados Vetorizados representa um avanço significativo na integração entre sistemas ERP e IA, oferecendo um nível de transparência e controle raramente visto em soluções comerciais. Esta abordagem "human-in-the-loop" combina o melhor da automação com o julgamento humano, resultando em um sistema mais confiável, preciso e adaptado às necessidades específicas de cada negócio.
