# Módulo: Integração de Tenants e MCP (tenant_mcp_integration)

## 1. Propósito

Este módulo Odoo 16 visa fornecer uma solução centralizada para o gerenciamento de múltiplos tenants e a integração com Múltiplas Centrais de Processamento (MCPs). Ele é projetado para:

*   Gerenciar informações de tenants.
*   Manter um catálogo de serviços de Inteligência Artificial (IA) oferecidos por módulos Odoo.
*   Controlar o acesso granular dos tenants a esses serviços de IA.
*   Facilitar a configuração e o monitoramento da integração.

## 2. Modelos Principais

*   `tenant_mcp.tenant`: Armazena informações detalhadas sobre cada tenant.
*   `tenant_mcp.type`: Define diferentes tipos de tenants (ex: Cliente, Interno). (Dados iniciais em `data/tenant_mcp_type_data.xml`)
*   `tenant_mcp.configuration`: Previsto para configurações gerais da integração MCP (desenvolvimento inicial).
*   `tenant_mcp.ia.service.catalog`: Catálogo de módulos Odoo que são identificados como provedores de serviços de IA. Permite marcar quais módulos estão disponíveis como serviços e adicionar metadados.
*   `tenant_mcp.tenant.service.access`: Modelo de ligação que define quais tenants têm acesso a quais serviços de IA do catálogo, e se esse acesso está habilitado.

## 3. Funcionalidades Chave Implementadas (Parcialmente)

*   **Catálogo de Serviços de IA:**
    *   Modelo `tenant_mcp.ia.service.catalog` para listar módulos Odoo.
    *   Funcionalidade para sincronizar módulos instaláveis do Odoo para dentro do catálogo.
    *   Campos para marcar um módulo como um "Serviço de IA Disponível" e adicionar nome e descrição específicos para o serviço.
    *   Views (tree, form, search) e item de menu para gerenciamento do catálogo.
*   **Controle de Acesso de Tenant a Serviços de IA:**
    *   Modelo `tenant_mcp.tenant.service.access` para associar tenants a serviços do catálogo.
    *   Campo `is_enabled_for_tenant` para habilitar/desabilitar o acesso.
    *   Views (tree, form, search) e item de menu para gerenciamento granular desses acessos.
*   **Integração com o Modelo de Tenant:**
    *   Adicionada uma aba "Acesso a Serviços de IA" no formulário do tenant (`tenant_mcp.tenant`).
    *   Nesta aba, é possível visualizar e gerenciar diretamente os serviços de IA aos quais o tenant tem acesso.

## 4. Estado Atual do Desenvolvimento (IMPORTANTE)

**Situação da Instalação/Atualização:**

O módulo está atualmente enfrentando um problema crítico durante a instalação ou atualização no Odoo, resultando no erro:
`psycopg2.errors.UndefinedTable: relation "tenant_mcp_ia_service_catalog" does not exist`

Este erro ocorre porque o Odoo tenta acessar a tabela `tenant_mcp_ia_service_catalog` (ou tabelas relacionadas a ela através de campos `related` com `store=True`) antes que a tabela seja efetivamente criada no banco de dados durante o processo de atualização do esquema.

**Tentativas de Correção Realizadas:**

1.  **Verificação e Correção do `ir.model.access.csv`**:
    *   Remoção de linhas em branco.
    *   Comentário temporário das linhas de acesso para os novos modelos (`tenant_mcp.ia.service.catalog` e `tenant_mcp.tenant.service.access`). Esta abordagem sozinha não resolveu o erro `UndefinedTable`.
2.  **Modificação de Campos `store=True` para `store=False`:**
    *   Nos modelos `tenant_mcp.tenant.service.access` e `tenant_mcp.ia.service.catalog`, todos os campos `related` e `compute` que originalmente tinham `store=True` foram alterados para `store=False`.
    *   **O resultado desta última tentativa (alterar `store=False` nos campos de `tenant_mcp.ia.service.catalog`) ainda precisa ser validado para confirmar se o módulo pode ser instalado/atualizado sem erros.**

**Devido a este problema, o módulo não está atualmente em um estado funcional estável para instalação ou atualização direta sem possíveis erros.**

## 5. Dependências

*   `base`
*   `mail`

## 6. Como Instalar/Atualizar (Procedimento Recomendado Dado o Estado Atual)

**ATENÇÃO:** Devido ao problema de `UndefinedTable`, a instalação pode falhar.

1.  Certifique-se de que as últimas alterações (com campos `store=False` nos modelos `tenant_mcp.ia.service.catalog` e `tenant_mcp.tenant.service.access`) estão aplicadas no código.
2.  Coloque o módulo `tenant_mcp_integration` no seu diretório de addons.
3.  Reinicie o servidor Odoo.
4.  Tente atualizar a lista de aplicativos e depois instalar/atualizar o módulo `tenant_mcp_integration` através da interface de Aplicativos do Odoo.
5.  **Monitore os logs do Odoo de perto para qualquer erro.**

Se a instalação for bem-sucedida após as últimas modificações:
1.  Descomente as linhas no arquivo `security/ir.model.access.csv`.
2.  Reinicie o Odoo e atualize o módulo novamente.
3.  Considere reavaliar a necessidade de `store=True` para os campos que foram alterados, planejando essa alteração cuidadosamente para evitar a reintrodução do erro.

## 7. Próximos Passos (Após Estabilização da Instalação)

1.  **Confirmar a resolução do problema de instalação/atualização.**
2.  Testar exaustivamente as funcionalidades implementadas.
3.  Confirmar requisitos de autenticação e conexão para a integração MCP-CREW.
4.  Implementar controladores e endpoints API para comunicação bidirecional.
5.  Expandir o modelo `tenant_mcp.configuration`.
6.  Criar documentação técnica e de usuário mais detalhada.
