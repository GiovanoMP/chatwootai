# Documentação do Módulo Odoo-Integration

## Visão Geral

O módulo **Odoo-Integration** implementa um agente universal de IA no Odoo que pode operar em todo o sistema, conectando-se com MCPs (Model Context Protocols) externos e permitindo interações via linguagem natural. Este módulo serve como um hub central para integração com múltiplas plataformas externas, começando com o Mercado Livre e preparado para expansão para outras plataformas como Instagram e Facebook.

## Principais Funcionalidades

### 1. Agente Universal de IA

O agente universal permite que usuários interajam com o sistema Odoo e plataformas externas usando linguagem natural, executando operações como:

- Criar e atualizar produtos
- Verificar estoque
- Criar promoções
- Sincronizar dados entre Odoo e plataformas externas
- Responder perguntas sobre produtos, pedidos e clientes

### 2. Conectores MCP

Conectores para diferentes plataformas externas, permitindo:

- Autenticação segura
- Comunicação padronizada
- Mapeamento de entidades
- Monitoramento de status

### 3. Sincronização Bidirecional

Sincronização automática de dados entre Odoo e plataformas externas:

- Produtos: informações, preços, imagens
- Pedidos: novos pedidos, atualizações de status
- Mensagens: perguntas de clientes, respostas

### 4. Dashboards Analíticos

Visualizações personalizáveis para dados de plataformas externas:

- KPIs de vendas e desempenho
- Gráficos de tendências
- Tabelas de produtos e pedidos
- Listas de mensagens recentes

### 5. Motor de Decisão Inteligente

Sistema que determina qual crew de IA deve processar cada comando ou mensagem, baseado em:

- Análise de conteúdo
- Contexto da conversa
- Regras de negócio
- Perfis de especialização das crews

## Instalação

### Requisitos

- Odoo 16.0
- Python 3.8+
- Acesso a MCPs externos (MCP-Crew, MCP-Mercado Livre)

### Procedimento de Instalação

1. Copie o diretório `odoo_integration` para o diretório de addons do Odoo
2. Atualize a lista de módulos no Odoo
3. Instale o módulo "Odoo Integration with MCP"
4. Configure os conectores MCP conforme necessário

## Configuração

### Configuração de Conectores

1. Acesse **Odoo Integration > Configuração > Conectores**
2. Clique em **Criar** para adicionar um novo conector
3. Preencha os campos:
   - **Nome**: Nome descritivo para o conector
   - **Tipo**: Selecione o tipo de conector (MCP-Crew, Mercado Livre, etc.)
   - **Endpoint**: URL base da API
   - **API Key**: Chave de API fornecida pela plataforma
   - **API Secret**: Segredo da API (se aplicável)
4. Clique em **Conectar** para testar a conexão
5. Salve o conector

### Configuração do Agente Universal

1. Acesse **Odoo Integration > Configuração > Agentes**
2. Clique em **Criar** ou edite o agente existente
3. Configure os parâmetros:
   - **Nome**: Nome do agente
   - **Usuário Relacionado**: Usuário do Odoo que o agente representará
   - **Versão do Modelo**: Versão do modelo de IA
   - **Temperatura**: Controla a criatividade das respostas (0.0-1.0)
   - **Máximo de Tokens**: Limite de tokens para respostas
4. Salve a configuração

### Configuração de Sincronizadores

1. Acesse **Odoo Integration > Configuração > Sincronizadores**
2. Clique em **Criar** para adicionar um novo sincronizador
3. Configure os parâmetros:
   - **Nome**: Nome descritivo
   - **Conector**: Selecione o conector configurado
   - **Tipo de Sincronização**: Produtos, Pedidos ou Mensagens
   - **Direção**: Odoo para MCP, MCP para Odoo, ou Bidirecional
   - **Sincronização Automática**: Ative para sincronização periódica
   - **Intervalo**: Frequência de sincronização em minutos
4. Salve a configuração

### Configuração de Dashboards

1. Acesse **Odoo Integration > Dashboards**
2. Clique em **Criar** para adicionar um novo dashboard
3. Configure os parâmetros:
   - **Nome**: Nome descritivo
   - **Tipo**: Visão Geral, Vendas, Estoque, etc.
   - **Conectores**: Selecione os conectores a incluir
4. Adicione widgets ao dashboard:
   - Clique em **Adicionar Widget**
   - Selecione o tipo de widget (KPI, Gráfico, Tabela, Lista)
   - Configure a fonte de dados e parâmetros
5. Salve o dashboard

## Fluxos de Uso

### 1. Interação com o Agente Universal

#### Via Interface de Comando

1. Acesse **Odoo Integration > Interface de Comando**
2. Digite um comando em linguagem natural na caixa de texto
3. Clique em **Enviar** ou pressione Enter
4. O agente processará o comando e exibirá a resposta
5. O histórico de comandos e respostas é mantido para referência

**Exemplos de comandos:**
- "Crie um novo produto chamado Notebook XPS com preço 5000"
- "Atualize o preço do produto Teclado Mecânico para 350"
- "Verifique o estoque do produto Mouse Sem Fio"
- "Crie uma promoção de 15% para os produtos da categoria Eletrônicos"
- "Sincronize os produtos com o Mercado Livre"

#### Via Sugestões

1. Acesse **Odoo Integration > Interface de Comando**
2. Visualize as sugestões de comandos disponíveis
3. Clique em uma sugestão para usá-la como base
4. Modifique o comando conforme necessário
5. Envie o comando

### 2. Sincronização de Produtos

#### Sincronização Manual

1. Acesse **Odoo Integration > Sincronizadores**
2. Localize o sincronizador de produtos desejado
3. Clique em **Sincronizar Agora**
4. Acompanhe o progresso na mensagem de status
5. Verifique os logs para detalhes da sincronização

#### Sincronização Automática

1. Configure o sincronizador com **Sincronização Automática** ativada
2. Defina o **Intervalo de Sincronização** desejado
3. O sistema sincronizará automaticamente nos intervalos definidos
4. Verifique a **Última Sincronização** e **Próxima Sincronização** para monitorar

#### Mapeamento de Produtos

1. Acesse **Odoo Integration > Mapeamentos > Produtos**
2. Visualize os produtos mapeados entre Odoo e plataformas externas
3. Verifique o status da última sincronização
4. Acesse links externos para visualizar produtos nas plataformas

### 3. Sincronização de Pedidos

#### Importação de Pedidos

1. Acesse **Odoo Integration > Sincronizadores**
2. Localize o sincronizador de pedidos desejado
3. Clique em **Sincronizar Agora**
4. Os pedidos das plataformas externas serão importados para o Odoo
5. Acesse **Vendas > Pedidos** para visualizar os pedidos importados

#### Atualização de Status

1. Quando o status de um pedido é alterado no Odoo:
   - O sincronizador detecta a alteração
   - Atualiza o status na plataforma externa
2. Quando o status é alterado na plataforma externa:
   - O sincronizador importa a alteração
   - Atualiza o pedido no Odoo

### 4. Sincronização de Mensagens

#### Recebimento de Perguntas

1. Perguntas de clientes nas plataformas externas são importadas
2. Acesse **Odoo Integration > Mensagens** para visualizar
3. Responda diretamente pelo Odoo
4. As respostas são sincronizadas com a plataforma externa

#### Resposta Automática

1. Configure o agente para responder automaticamente a perguntas comuns
2. O motor de decisão inteligente determina qual crew deve responder
3. A resposta é gerada e enviada automaticamente
4. O histórico de interações é mantido para referência

### 5. Uso de Dashboards

#### Visualização de KPIs

1. Acesse **Odoo Integration > Dashboards**
2. Selecione o dashboard desejado
3. Visualize KPIs como:
   - Total de vendas
   - Produtos ativos
   - Taxa de conversão
   - Tempo médio de resposta

#### Análise de Dados

1. Utilize os gráficos para analisar tendências
2. Filtre dados por período, categoria, etc.
3. Exporte dados para relatórios
4. Configure alertas para métricas importantes

## Integração com MCP-Crew

### Fluxo de Decisão Inteligente

1. Uma mensagem ou comando é recebido
2. O sistema analisa o conteúdo usando processamento de linguagem natural
3. O motor de decisão avalia:
   - Intenção e entidades no texto
   - Contexto da conversa
   - Regras de negócio configuradas
4. Uma pontuação é calculada para cada crew disponível
5. A crew com maior pontuação é selecionada
6. A mensagem é encaminhada para processamento
7. A decisão é registrada para aprendizado futuro

### Configuração de Crews

1. Acesse **Odoo Integration > Configuração > Crews**
2. Visualize as crews disponíveis sincronizadas do MCP-Crew
3. Ative ou desative crews conforme necessário
4. Visualize especialidades e estatísticas de cada crew

### Ajuste de Pesos de Decisão

1. Acesse **Odoo Integration > Configuração > Conectores**
2. Edite o conector MCP-Crew
3. Ajuste os **Pesos de Decisão** para modificar como o motor prioriza diferentes fatores:
   - Conteúdo: peso da análise de texto
   - Contexto: peso do histórico e metadados
   - Regras: peso das regras de negócio

## Solução de Problemas

### Problemas de Conexão

**Sintoma**: Erro "Falha ao conectar com MCP"

**Soluções**:
1. Verifique se o endpoint está correto e acessível
2. Confirme se a API Key e Secret estão corretos
3. Verifique se o serviço MCP está online
4. Verifique logs do sistema para detalhes do erro

### Falhas de Sincronização

**Sintoma**: Sincronização falha ou dados incompletos

**Soluções**:
1. Verifique os logs de sincronização para erros específicos
2. Confirme se os mapeamentos estão corretos
3. Verifique se há conflitos de dados (ex: SKUs duplicados)
4. Tente sincronizar manualmente um item específico para isolar o problema

### Problemas com o Agente

**Sintoma**: O agente não responde ou dá respostas incorretas

**Soluções**:
1. Verifique se o conector MCP-Crew está conectado
2. Analise os logs de interação para entender a interpretação do comando
3. Ajuste a temperatura se as respostas forem muito criativas ou muito restritas
4. Verifique se há crews disponíveis para processar o tipo de comando

## Manutenção

### Backup de Configurações

1. Exporte as configurações regularmente:
   - Acesse **Configurações > Exportar**
   - Selecione os modelos de configuração do módulo
   - Salve o arquivo de exportação

### Monitoramento de Performance

1. Verifique regularmente:
   - Tempo de resposta das sincronizações
   - Taxa de sucesso das interações com o agente
   - Uso de recursos do servidor

### Atualização do Módulo

1. Faça backup das configurações
2. Atualize o código-fonte do módulo
3. Reinicie o servidor Odoo
4. Execute a atualização do módulo via interface
5. Verifique se todas as funcionalidades estão operando corretamente

## Extensão e Personalização

### Adição de Novos Conectores

1. Crie uma nova classe herdando de `odoo.integration.connector`
2. Implemente os métodos específicos:
   - `_connect_[tipo]`
   - `_send_request_[tipo]`
3. Adicione o novo tipo à seleção de tipos de conector
4. Implemente os sincronizadores específicos

### Personalização de Dashboards

1. Crie novos widgets personalizados:
   - Estenda a classe `odoo.integration.dashboard.widget`
   - Implemente métodos de obtenção de dados
2. Adicione novos tipos de visualização:
   - Implemente o frontend em JavaScript
   - Registre o widget no sistema

### Extensão do Agente

1. Adicione novas intenções:
   - Atualize o mapeamento de intenções para métodos
   - Implemente os métodos de ação correspondentes
2. Personalize respostas:
   - Modifique os templates de resposta
   - Ajuste parâmetros de geração

## Referências

### APIs e Documentação Externa

- [Documentação da API do Mercado Livre](https://developers.mercadolivre.com.br/pt_br/api-docs-pt-br)
- [Documentação do MCP-Crew](https://docs.mcp-crew.example.com)
- [Documentação do Odoo 16](https://www.odoo.com/documentation/16.0)

### Módulos Relacionados

- **MCP-Mercado Livre**: Conector específico para o Mercado Livre
- **MCP-Crew**: Sistema central de gerenciamento de crews de IA

## Suporte

Para suporte técnico, entre em contato com:

- Email: support@manus.ai
- Website: https://www.manus.ai/support
