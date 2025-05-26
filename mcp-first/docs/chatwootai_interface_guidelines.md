# Guia de Design e Layout para Interfaces ChatwootAI

Este documento define os padrões de design e layout para interfaces do ChatwootAI, com foco especial nas configurações de atendimento. Estes padrões devem ser aplicados consistentemente em todos os módulos e componentes do sistema para garantir uma experiência de usuário coesa e de alta qualidade.

## 1. Princípios Fundamentais

Seguimos os princípios de design inspirados no Stripe e Linear, priorizando:

- **Simplicidade Elegante**: Interfaces limpas com espaço em branco adequado
- **Hierarquia Visual Clara**: Estrutura visual que guia o usuário naturalmente
- **Feedback Imediato**: Respostas visuais para todas as interações
- **Consistência**: Padrões visuais e interativos uniformes em todo o sistema
- **Contextualização**: Informações e controles apresentados no momento e local adequados
- **Mobile-First**: Design responsivo otimizado para PWA e uso em dispositivos móveis

## 2. Estrutura Geral e Organização

### 2.1 Estrutura de Página

```
┌─────────────────────────────────────────────────┐
│ Banner Informativo                              │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ Seção Principal                             │ │
│ │ ┌─────────────────────────────────────────┐ │ │
│ │ │ Card de Conteúdo                        │ │ │
│ │ └─────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Seção Principal                             │ │
│ │ ┌─────────────────────────────────────────┐ │ │
│ │ │ Card de Conteúdo                        │ │ │
│ │ └─────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Rodapé Informativo                              │
└─────────────────────────────────────────────────┘
```

### 2.2 Componentes Estruturais

- **Banner Informativo**: Alerta no topo com informações contextuais
- **Seções Principais**: Containers com título, ícone e descrição
- **Cards de Conteúdo**: Agrupamentos de controles relacionados
- **Rodapé Informativo**: Dicas e informações adicionais

## 3. Sistema de Cores

### 3.1 Paleta Principal

| Cor | Código Hex | Uso |
|-----|------------|-----|
| Azul Primário | #2196F3 | Ações primárias, elementos informativos |
| Verde | #4CAF50 | Sucesso, confirmação, ações positivas |
| Amarelo | #FFC107 | Avisos, atenção, destaques |
| Vermelho | #F44336 | Erros, ações destrutivas |
| Roxo | #673AB7 | Elementos de personalidade, ações especiais |

### 3.2 Cores Neutras

| Cor | Código Hex | Uso |
|-----|------------|-----|
| Branco | #FFFFFF | Fundo de cards e áreas de conteúdo |
| Cinza Claro | #F8F9FA | Fundo de containers e áreas secundárias |
| Cinza Médio | #E9ECEF | Bordas e separadores |
| Cinza Escuro | #6C757D | Texto secundário e dicas |
| Preto | #212529 | Texto principal |

### 3.3 Cores Contextuais

| Contexto | Cor de Fundo | Cor de Texto | Cor de Borda |
|----------|--------------|--------------|--------------|
| Informação | #E3F2FD | #0D47A1 | #2196F3 |
| Sucesso | #E8F5E9 | #1B5E20 | #4CAF50 |
| Aviso | #FFF8E1 | #F57F17 | #FFC107 |
| Erro | #FFEBEE | #B71C1C | #F44336 |

## 4. Tipografia

### 4.1 Hierarquia de Texto

| Elemento | Tamanho | Peso | Cor |
|----------|---------|------|-----|
| Título de Página | 24px | Bold | #212529 |
| Título de Seção | 20px | Bold | #212529 |
| Título de Card | 16px | Bold | #212529 |
| Texto Normal | 14px | Regular | #212529 |
| Texto Secundário | 14px | Regular | #6C757D |
| Dicas e Ajuda | 12px | Italic | #6C757D |

### 4.2 Espaçamento de Texto

- Espaçamento entre linhas: 1.5
- Espaçamento entre parágrafos: 16px
- Espaçamento entre seções: 24px
- Espaçamento entre elementos relacionados: 8px

## 5. Componentes de Interface

### 5.1 Alertas e Banners

```html
<div class="alert alert-info mb-4" role="alert" style="border-left: 4px solid #2196F3; background-color: #f8f9fa;">
    <div class="d-flex">
        <i class="fa fa-magic fa-2x me-3 text-primary"></i>
        <div>
            <h4 class="alert-heading">Título do Alerta</h4>
            <p class="mb-0">Texto explicativo do alerta.</p>
        </div>
    </div>
</div>
```

### 5.2 Containers de Seção

```html
<div class="o_settings_container mb-4 p-3" style="background-color: #f8f9fa; border-radius: 8px;">
    <div class="d-flex align-items-center mb-3">
        <i class="fa fa-icon fa-2x me-2" style="color: #colorcode;"></i>
        <div>
            <h3 class="m-0">Título da Seção</h3>
            <p class="text-muted mb-0">Descrição da seção</p>
        </div>
    </div>
    
    <!-- Conteúdo da seção -->
</div>
```

### 5.3 Cards

```html
<div class="card shadow-sm mb-4">
    <div class="card-header bg-light">
        <h5 class="card-title m-0"><i class="fa fa-icon me-2 text-primary"></i>Título do Card</h5>
    </div>
    <div class="card-body">
        <!-- Conteúdo do card -->
    </div>
    <div class="card-footer bg-light">
        <small class="text-muted"><i class="fa fa-info-circle me-1"></i> Dica ou informação adicional.</small>
    </div>
</div>
```

### 5.4 Campos e Controles

#### 5.4.1 Toggles e Switches

```html
<div class="form-check form-switch">
    <field name="campo_boolean" widget="boolean_toggle" class="form-check-input"/>
    <label for="campo_boolean" class="form-check-label fw-bold">Título da Opção</label>
    <div class="text-muted small mt-1">Descrição detalhada da opção</div>
</div>
```

#### 5.4.2 Campos de Texto

```html
<label for="campo_texto" class="form-label fw-bold">Título do Campo</label>
<field name="campo_texto" placeholder="Texto de exemplo..." class="form-control" help="Texto de ajuda sobre o campo"/>
```

#### 5.4.3 Seletores de Opção

```html
<!-- IMPORTANTE: Usar apenas UM tipo de seletor por campo para evitar sobreposição -->
<!-- Opção 1: Radio buttons (recomendado para poucas opções) -->
<field name="campo_selection" widget="radio" options="{'horizontal': True}" help="Texto de ajuda sobre as opções"/>
<div class="mt-2 small text-muted fst-italic">Dica: Informação adicional sobre a escolha.</div>

<!-- Opção 2: Dropdown (recomendado para muitas opções) -->
<field name="campo_selection" widget="selection" class="form-select" help="Texto de ajuda sobre as opções"/>
<div class="mt-2 small text-muted fst-italic">Dica: Informação adicional sobre a escolha.</div>

<!-- NUNCA combinar widgets diferentes para o mesmo campo -->
```

### 5.5 Elementos Especiais

#### 5.5.1 Timeline de Processo

```html
<div class="d-flex mb-4">
    <div class="me-3 text-center">
        <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
            <i class="fa fa-icon"></i>
        </div>
        <div class="mt-2 mb-2" style="border-left: 2px dashed #ccc; height: 30px;"></div>
    </div>
    <div class="flex-grow-1">
        <div class="card border-primary">
            <div class="card-header bg-primary text-white">
                <h6 class="m-0">Título da Etapa</h6>
            </div>
            <div class="card-body">
                <!-- Conteúdo da etapa -->
            </div>
        </div>
    </div>
</div>
```

#### 5.5.2 Simulação de Chat

```html
<div class="chat-message">
    <!-- Mensagem do agente -->
    <div class="d-flex mb-3">
        <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center me-2" style="width: 40px; height: 40px;">
            <i class="fa fa-robot"></i>
        </div>
        <div class="chat-bubble p-3 rounded" style="background-color: #e9ecef; max-width: 80%;">
            <p class="mb-0">Texto da mensagem do agente</p>
        </div>
    </div>
    
    <!-- Mensagem do cliente -->
    <div class="d-flex justify-content-end mb-3">
        <div class="chat-bubble p-3 rounded" style="background-color: #dcf8c6; max-width: 80%;">
            <p class="mb-0">Texto da mensagem do cliente</p>
        </div>
        <div class="rounded-circle bg-success text-white d-flex align-items-center justify-content-center ms-2" style="width: 40px; height: 40px;">
            <i class="fa fa-user"></i>
        </div>
    </div>
</div>
```

### 5.5.3 Caixa de Diálogo Interativa

```html
<div class="card shadow-sm mb-4">
    <div class="card-header bg-primary text-white">
        <h5 class="card-title m-0 d-flex align-items-center">
            <i class="fa fa-comments me-2"></i>
            Testar Agente de IA
            <span class="badge bg-warning text-dark ms-auto">Pré-visualização</span>
        </h5>
    </div>
    <div class="card-body">
        <div class="chat-container border rounded p-3 mb-3" style="height: 300px; overflow-y: auto;">
            <div id="chat-messages">
                <!-- Mensagens serão adicionadas dinamicamente aqui -->
                <div class="d-flex mb-3">
                    <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center me-2" style="width: 40px; height: 40px;">
                        <i class="fa fa-robot"></i>
                    </div>
                    <div class="chat-bubble p-3 rounded" style="background-color: #e9ecef; max-width: 80%;">
                        <p class="mb-0" t-esc="record.greeting_message || 'Olá! Como posso ajudar?'"></p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="input-group">
            <input type="text" id="user-message" class="form-control" placeholder="Digite sua mensagem..." disabled="disabled"/>
            <button class="btn btn-primary" type="button" id="send-message" disabled="disabled">
                <i class="fa fa-paper-plane"></i>
            </button>
        </div>
        
        <div class="mt-3 text-center">
            <button class="btn btn-success" type="button" id="sync-ai">
                <i class="fa fa-refresh me-1"></i> Sincronizar com Sistema de IA
            </button>
            <div class="mt-2 small text-muted">
                <i class="fa fa-info-circle me-1"></i> Sincronize as configurações com o sistema de IA para testar o agente em tempo real
            </div>
        </div>
    </div>
</div>
```

## 6. Padrões de Interação

### 6.1 Visibilidade Condicional

```html
<div attrs="{'invisible': [('campo_condicional', '=', False)]}">
    <!-- Conteúdo que aparece apenas quando a condição é atendida -->
</div>
```

### 6.2 Pré-visualizações

```html
<div class="mt-3">
    <span class="o_form_label">Pré-visualização</span>
    <div class="border rounded p-3 bg-light">
        <!-- Conteúdo da pré-visualização -->
    </div>
</div>
```

### 6.3 Feedback Visual

- Use cores consistentes para estados (verde para sucesso, vermelho para erro)
- Forneça feedback imediato para ações do usuário
- Use ícones para reforçar mensagens e estados

## 7. Iconografia

### 7.1 Sistema de Ícones

Utilizamos a biblioteca Font Awesome para ícones, com uso consistente em todo o sistema:

| Contexto | Ícone | Código |
|----------|-------|--------|
| Introdução/Personalização | `fa-magic` | `<i class="fa fa-magic"></i>` |
| Fluxo de Conversa | `fa-exchange` | `<i class="fa fa-exchange"></i>` |
| Personalidade | `fa-user-circle` | `<i class="fa fa-user-circle"></i>` |
| Configurações | `fa-cog` | `<i class="fa fa-cog"></i>` |
| Finalização | `fa-flag-checkered` | `<i class="fa fa-flag-checkered"></i>` |
| Informações | `fa-info-circle` | `<i class="fa fa-info-circle"></i>` |
| Avaliação | `fa-star` | `<i class="fa fa-star"></i>` |
| Comunicação | `fa-comments` | `<i class="fa fa-comments"></i>` |
| Agente | `fa-robot` | `<i class="fa fa-robot"></i>` |
| Cliente | `fa-user` | `<i class="fa fa-user"></i>` |

### 7.2 Tamanhos de Ícones

- Ícones grandes (cabeçalhos de seção): `fa-2x`
- Ícones médios (cabeçalhos de card): `fa-lg`
- Ícones pequenos (dentro de texto): tamanho padrão

## 8. Responsividade

### 8.1 Breakpoints

| Nome | Tamanho | Comportamento |
|------|---------|---------------|
| Extra pequeno | < 576px | Empilhamento vertical de todos os elementos |
| Pequeno | ≥ 576px | Empilhamento vertical com margens maiores |
| Médio | ≥ 768px | Layout de duas colunas para alguns elementos |
| Grande | ≥ 992px | Layout completo de múltiplas colunas |
| Extra grande | ≥ 1200px | Layout otimizado com mais espaço em branco |

### 8.2 Classes Responsivas

- Use `col-lg-6` para layout de duas colunas em telas grandes
- Use `d-flex flex-wrap` para elementos que precisam se adaptar
- Use `img-fluid` para imagens responsivas

## 9. Padrões de Comunicação com o Cliente

### 9.1 Linguagem e Tom

- **Clareza**: Instruções diretas e objetivas
- **Positividade**: Foco em "o que fazer" em vez de "o que não fazer"
- **Orientação**: Dicas e sugestões para ajudar na escolha
- **Contextualização**: Explicação do impacto de cada configuração

### 9.2 Elementos de Ajuda

- **Tooltips**: Texto de ajuda em campos com explicações detalhadas
- **Dicas Visuais**: Textos em itálico com sugestões de melhores práticas
- **Pré-visualizações**: Exemplos visuais do resultado das configurações

## 10. Exemplos de Implementação

### 10.1 Seção de Fluxo de Conversa

```html
<div class="o_settings_container mb-4 p-3" style="background-color: #f8f9fa; border-radius: 8px;">
    <div class="d-flex align-items-center mb-3">
        <i class="fa fa-exchange fa-2x me-2" style="color: #2196F3;"></i>
        <div>
            <h3 class="m-0">Fluxo de Conversa</h3>
            <p class="text-muted mb-0">Configure as mensagens e interações do início ao fim da conversa</p>
        </div>
    </div>
    
    <div class="card shadow-sm mb-4">
        <div class="card-header bg-light">
            <h5 class="card-title m-0"><i class="fa fa-comments-o me-2 text-primary"></i>Etapas da Conversa</h5>
        </div>
        <div class="card-body">
            <!-- Início da conversa -->
            <div class="d-flex mb-4">
                <div class="me-3 text-center">
                    <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                        <i class="fa fa-play"></i>
                    </div>
                    <div class="mt-2 mb-2" style="border-left: 2px dashed #ccc; height: 30px;"></div>
                </div>
                <div class="flex-grow-1">
                    <div class="card border-primary">
                        <div class="card-header bg-primary text-white">
                            <h6 class="m-0">Início da Conversa</h6>
                        </div>
                        <div class="card-body">
                            <label for="greeting_message" class="form-label fw-bold">Mensagem de Boas-vindas</label>
                            <field name="greeting_message" placeholder="Ex: Olá! Sou o assistente virtual da [Nome da Empresa]. Como posso ajudar hoje?" class="w-100" help="Mensagem inicial que o agente de IA enviará ao iniciar uma conversa com o cliente."/>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Outras etapas da conversa aqui -->
        </div>
    </div>
</div>
```

### 10.2 Seção de Personalidade do Agente

```html
<div class="o_settings_container mb-4 p-3" style="background-color: #f8f9fa; border-radius: 8px;">
    <div class="d-flex align-items-center mb-3">
        <i class="fa fa-user-circle fa-2x me-2" style="color: #673AB7;"></i>
        <div>
            <h3 class="m-0">Personalidade do Agente</h3>
            <p class="text-muted mb-0">Configure o estilo de comunicação e personalidade do seu assistente virtual</p>
        </div>
    </div>
    
    <div class="card shadow-sm mb-4">
        <div class="card-header bg-light">
            <h5 class="card-title m-0"><i class="fa fa-sliders me-2 text-primary"></i>Ajustes de Personalidade</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <!-- Tom de Comunicação -->
                <div class="col-lg-6 mb-4">
                    <div class="card border-primary h-100">
                        <div class="card-header bg-primary text-white">
                            <div class="d-flex align-items-center">
                                <i class="fa fa-comment me-2"></i>
                                <h6 class="m-0">Tom de Comunicação</h6>
                            </div>
                        </div>
                        <div class="card-body">
                            <p class="text-muted small mb-3">Como o agente deve soar nas conversas com os clientes</p>
                            <field name="tone" widget="radio" options="{'horizontal': True}" help="Define o tom geral que o agente de IA usará nas conversas. Escolha o que melhor representa a personalidade da sua marca."/>
                            <div class="mt-2 small text-muted fst-italic">Dica: O tom "Amigável" é ideal para a maioria dos negócios.</div>
                        </div>
                    </div>
                </div>
                
                <!-- Outros ajustes de personalidade aqui -->
            </div>
        </div>
    </div>
</div>
```

## 11. Problemas Comuns e Soluções

### 11.1 Duplicação de Configurações

**Problema**: Configurações similares aparecem em múltiplas seções, causando confusão.

**Solução**: 
- Cada configuração deve existir em apenas um local lógico
- Use referências visuais (ícones, cores) para indicar relações entre configurações
- Agrupe configurações relacionadas na mesma seção

**Exemplo**: A opção "Permitir agente incluir redes sociais" deve aparecer apenas na seção "Outras Configurações", não no "Fluxo da Conversa".

### 11.2 Sobreposição de Elementos de Interface

**Problema**: Múltiplos widgets de seleção para o mesmo campo causam sobreposição visual.

**Solução**:
- Use apenas um widget por campo
- Mantenha consistência no tipo de widget para campos similares
- Teste a renderização em diferentes tamanhos de tela

**Exemplo**: Para campos de seleção, escolha entre radio buttons OU dropdown, nunca ambos.

### 11.3 Pré-visualização Desconectada

**Problema**: Pré-visualizações estáticas não refletem as configurações reais.

**Solução**:
- Implemente pré-visualizações dinâmicas que reagem às mudanças de configuração
- Use JavaScript para atualizar a pré-visualização em tempo real
- Forneça feedback visual quando a pré-visualização não estiver sincronizada

## 12. Caixa de Diálogo Interativa

### 12.1 Propósito e Funcionalidade

A caixa de diálogo interativa serve como uma ferramenta de teste em tempo real para as configurações do agente de IA:

- **Posicionamento**: Ao final de todas as seções de configuração
- **Sincronização**: Conecta-se ao sistema de IA para testes reais
- **Feedback Visual**: Mostra exatamente como o cliente verá o agente
- **Interatividade**: Permite testar diferentes cenários de conversa

### 12.2 Estados da Caixa de Diálogo

1. **Estado Inicial (Desconectado)**:
   - Interface desabilitada
   - Botão "Sincronizar com Sistema de IA" proeminente
   - Mensagem informativa sobre necessidade de sincronização

2. **Estado Sincronizado**:
   - Interface totalmente funcional
   - Mensagens refletem configurações atuais
   - Botão para reiniciar conversa disponível
   - Indicador visual de conexão ativa

3. **Estado de Erro**:
   - Mensagem de erro clara
   - Opções para resolução de problemas
   - Botão para tentar novamente

### 12.3 Implementação Técnica

- Use WebSockets para comunicação em tempo real
- Implemente cache local para configurações frequentes
- Forneça feedback visual durante a sincronização
- Registre interações para análise e melhoria

## 13. Adaptação para Outras Aplicações

Para replicar este estilo em outras aplicações, siga estas diretrizes:

1. **Mantenha a Consistência Visual**: Use a mesma paleta de cores, iconografia e estilos de componentes
2. **Preserve a Hierarquia**: Mantenha a estrutura de seções, cards e agrupamentos
3. **Adapte o Conteúdo**: Ajuste os textos e campos para o contexto específico da aplicação
4. **Mantenha as Pré-visualizações**: Sempre que possível, inclua exemplos visuais do resultado das configurações
5. **Evite Duplicações**: Cada configuração deve existir em apenas um local lógico
6. **Teste em Dispositivos Móveis**: Garanta que a interface funcione bem em PWA e dispositivos móveis

## 14. Verificação de Qualidade

Antes de finalizar qualquer interface, verifique:

- **Consistência Visual**: Todos os elementos seguem o mesmo estilo?
- **Hierarquia Clara**: A organização visual guia o usuário naturalmente?
- **Feedback Adequado**: Todas as ações têm feedback visual claro?
- **Responsividade**: A interface funciona bem em diferentes tamanhos de tela?
- **Acessibilidade**: Contraste de cores, tamanhos de fonte e interações são acessíveis?
- **Clareza**: As instruções e descrições são claras e objetivas?

---

Este guia foi desenvolvido com base no módulo `company_services`, especificamente na aba "Configurações de Atendimento", e deve ser aplicado consistentemente em todas as interfaces do ChatwootAI para garantir uma experiência de usuário coesa e de alta qualidade.
