# Manual do Usuário - Gerenciador de Credenciais para IA

## Índice

1. [Introdução](#introdução)
2. [Instalação](#instalação)
3. [Configuração Inicial](#configuração-inicial)
4. [Gerenciamento de Credenciais](#gerenciamento-de-credenciais)
   - [Criando uma Nova Credencial](#criando-uma-nova-credencial)
   - [Campos Obrigatórios](#campos-obrigatórios)
   - [Campos Opcionais](#campos-opcionais)
5. [Integração com Arquivos YAML](#integração-com-arquivos-yaml)
   - [Estrutura dos Arquivos YAML](#estrutura-dos-arquivos-yaml)
   - [Sincronização de Credenciais](#sincronização-de-credenciais)
6. [Fila de Sincronização](#fila-de-sincronização)
7. [Logs de Acesso](#logs-de-acesso)
8. [Integrações com Redes Sociais e Marketplaces](#integrações-com-redes-sociais-e-marketplaces)
9. [Solução de Problemas](#solução-de-problemas)

## Introdução

O módulo **Gerenciador de Credenciais para IA** fornece uma solução centralizada e segura para gerenciar todas as credenciais de autenticação utilizadas na integração entre o Odoo e sistemas externos, com foco inicial em sistemas de Inteligência Artificial.

Este módulo permite:
- Armazenar credenciais de forma segura e criptografada
- Sincronizar credenciais com arquivos YAML para uso pelos agentes de IA
- Monitorar o acesso às credenciais através de logs detalhados
- Gerenciar operações de sincronização através de uma fila com retry automático

## Instalação

1. Instale o módulo através do menu Aplicativos do Odoo
2. Certifique-se de que a biblioteca Python `cryptography` esteja instalada no servidor:
   ```bash
   pip3 install cryptography
   ```
3. Reinicie o servidor Odoo após a instalação da biblioteca

## Configuração Inicial

Após a instalação, você encontrará um novo menu "Credenciais de IA" no painel principal do Odoo. Este menu só está disponível para usuários com permissões de administrador.

## Gerenciamento de Credenciais

### Criando uma Nova Credencial

1. Acesse o menu **Credenciais de IA > Credenciais**
2. Clique em **Criar**
3. Preencha os campos necessários (detalhados abaixo)
4. Clique em **Salvar**

### Campos Obrigatórios

#### Informações Básicas
- **Nome**: Um nome descritivo para identificar esta credencial (ex: "Credenciais Empresa A")
- **ID da Conta**: Identificador único da conta no formato `account_X` (ex: "account_1"). **MUITO IMPORTANTE**: Este campo deve corresponder exatamente ao nome do diretório na estrutura YAML (`config/domains/[domínio]/[account_id]/`)
- **Token**: Gerado automaticamente, usado como referência segura nos arquivos YAML
- **Área de Negócio**: Selecione a área de negócio correspondente (ex: "cosmetics"). Este campo determina o diretório de domínio na estrutura YAML

#### Credenciais do Odoo
- **URL do Odoo**: URL completa do servidor Odoo (ex: "https://odoo.suaempresa.com" ou "http://localhost:8069")
- **Banco de Dados**: Nome do banco de dados Odoo (ex: "account_1")
- **Usuário**: Nome de usuário para autenticação no Odoo
- **Senha**: Senha para autenticação no Odoo (armazenada de forma criptografada)

### Campos Opcionais

#### Sistema de IA
- **URL do Sistema de IA**: URL base do sistema de IA (ex: "https://ai-system.example.com")
- **Usar Ngrok**: Ative para usar Ngrok em ambiente de desenvolvimento
- **URL Ngrok**: URL Ngrok para ambiente de desenvolvimento (ex: "https://xxxx-xxx-xxx.ngrok.io")

#### Armazenamento
- **Coleção Qdrant**: Nome da coleção no Qdrant (se não preenchido, será usado "business_rules_[account_id]")
- **Prefixo Redis**: Prefixo para chaves no Redis (se não preenchido, será usado o account_id)

#### Redes Sociais
Credenciais para integração com Facebook e Instagram:
- **Facebook App ID**
- **Facebook App Secret**
- **Facebook Access Token**
- **Instagram Client ID**
- **Instagram Client Secret**
- **Instagram Access Token**

#### Marketplaces
Credenciais para integração com Mercado Livre:
- **Mercado Livre App ID**
- **Mercado Livre Client Secret**
- **Mercado Livre Access Token**

## Integração com Arquivos YAML

O módulo sincroniza as credenciais com arquivos YAML que são utilizados pelos agentes de IA. Esta sincronização é feita através do botão "Sincronizar com YAML" na tela de credenciais.

### Estrutura dos Arquivos YAML

Os arquivos YAML seguem a seguinte estrutura de diretórios:
```
config/
└── domains/
    └── [domínio]/
        └── [account_id]/
            └── config.yaml
```

Exemplo:
```
config/
└── domains/
    └── cosmetics/
        └── account_1/
    hooks        └── config.yaml
```

O arquivo `config.yaml` gerado terá a seguinte estrutura:

```yaml
account_id: account_1
name: Nome do Cliente
description: Configuração para Nome do Cliente
integrations:
  mcp:
    type: odoo-mcp
    config:
      url: http://localhost:8069
      db: account_1
      username: admin
      credential_ref: a1b2c3d4-e5f6-g7h8-i9j0  # Referência ao token, não a senha real
  qdrant:
    collection: business_rules_account_1
  redis:
    prefix: account_1
```

### Sincronização de Credenciais

Para sincronizar as credenciais com os arquivos YAML:

1. Abra a credencial que deseja sincronizar
2. Clique no botão **Sincronizar com YAML**
3. Uma mensagem de confirmação será exibida se a sincronização for bem-sucedida

**IMPORTANTE**: A sincronização cria ou atualiza o arquivo YAML com referências seguras às credenciais, não com as credenciais reais. Isso garante que informações sensíveis não sejam armazenadas em texto claro nos arquivos de configuração.

## Fila de Sincronização

O módulo inclui um sistema de fila para operações de sincronização, acessível através do menu **Credenciais de IA > Fila de Sincronização**.

A fila permite:
- Monitorar o status das operações de sincronização
- Reprocessar operações que falharam
- Cancelar operações pendentes

Cada operação na fila contém:
- **Credencial**: A credencial associada à operação
- **Módulo**: O módulo Odoo que iniciou a operação (ex: "business_rules")
- **Operação**: O tipo de operação (ex: "sync", "generate")
- **Estado**: O estado atual da operação (pendente, processando, concluído, falha)
- **Dados**: Os dados enviados na operação (formato JSON)
- **Resultado**: O resultado da operação (quando concluída com sucesso)
- **Mensagem de Erro**: Detalhes do erro (quando falha)

## Logs de Acesso

O módulo registra todos os acessos às credenciais, acessível através do menu **Credenciais de IA > Logs de Acesso**.

Cada log contém:
- **Credencial**: A credencial acessada
- **Data e Hora**: Quando o acesso ocorreu
- **Endereço IP**: O endereço IP de onde o acesso foi feito
- **Operação**: A operação realizada (ex: "get_credentials", "test_connection")
- **Sucesso**: Se a operação foi bem-sucedida
- **Mensagem de Erro**: Detalhes do erro (quando falha)

## Integrações com Redes Sociais e Marketplaces

O módulo suporta o armazenamento de credenciais para redes sociais (Facebook, Instagram) e marketplaces (Mercado Livre). Estas credenciais são armazenadas de forma segura e podem ser utilizadas pelos agentes de IA para interagir com estas plataformas.

Para configurar estas integrações:
1. Abra a credencial desejada
2. Acesse a aba "Redes Sociais" ou "Marketplaces"
3. Preencha os campos necessários
4. Clique em **Salvar**

## Solução de Problemas

### Erro de Criptografia
Se você encontrar erros relacionados à criptografia, verifique se a biblioteca `cryptography` está instalada corretamente:
```bash
pip3 list | grep cryptography
```

### Erro de Sincronização com YAML
Se a sincronização com YAML falhar:
1. Verifique se o diretório `config/domains/[domínio]/[account_id]/` existe e tem permissões de escrita
2. Verifique se os campos obrigatórios estão preenchidos corretamente
3. Verifique os logs do Odoo para mais detalhes sobre o erro

### Erro de Conexão com o Sistema de IA
Se o teste de conexão falhar:
1. Verifique se a URL do sistema de IA está correta
2. Verifique se o sistema de IA está acessível a partir do servidor Odoo
3. Se estiver usando Ngrok, verifique se a URL Ngrok está atualizada

### Operações na Fila com Falha
Se operações na fila estiverem falhando:
1. Verifique a mensagem de erro na operação
2. Corrija o problema indicado na mensagem
3. Clique em "Tentar Novamente" para reprocessar a operação
