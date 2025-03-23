# Sistema de Plugins do ChatwootAI

## Introdução

O sistema de plugins do ChatwootAI permite estender as funcionalidades da plataforma sem modificar o código base. Isso facilita a adaptação do sistema para diferentes domínios de negócio (cosméticos, saúde, varejo, etc.) e permite adicionar novas capacidades de forma modular.

Este documento descreve a interface esperada para plugins, propõe melhorias para a classe base e explica como implementar validação durante o carregamento de plugins.

## Interface de Plugins

### Métodos Obrigatórios

Todos os plugins devem implementar os seguintes métodos:

| Método | Descrição | Parâmetros | Retorno |
|--------|-----------|------------|---------|
| `initialize()` | Inicializa recursos do plugin | Nenhum | Nenhum |
| `process_message(message, context)` | Processa uma mensagem recebida | `message`: String com o texto da mensagem<br>`context`: Dicionário com o contexto da conversa | Dicionário com o contexto atualizado |
| `validate_config()` | Valida a configuração do plugin | Nenhum | Boolean indicando se a configuração é válida |

### Métodos Opcionais

Os seguintes métodos são opcionais, mas recomendados para funcionalidades específicas:

| Método | Descrição | Parâmetros | Retorno |
|--------|-----------|------------|---------|
| `process_response(response, context)` | Processa uma resposta antes de enviá-la | `response`: String com a resposta<br>`context`: Dicionário com o contexto | String com a resposta processada |
| `get_metadata()` | Retorna metadados do plugin | Nenhum | Dicionário com metadados |
| `cleanup()` | Libera recursos ao desativar o plugin | Nenhum | Nenhum |

### Exemplo de Implementação Mínima

```python
from src.plugins.base.base_plugin import BasePlugin
from typing import Dict, Any

class MeuPlugin(BasePlugin):
    def initialize(self):
        # Inicialização de recursos
        pass
        
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Processamento da mensagem
        updated_context = context.copy()
        # Lógica do plugin...
        return updated_context
        
    def validate_config(self) -> bool:
        # Validação da configuração
        required_keys = ["param1", "param2"]
        return all(key in self.config for key in required_keys)
```

## Melhorias para a Classe BasePlugin

A classe `BasePlugin` atual fornece funcionalidades básicas, mas pode ser aprimorada para facilitar o desenvolvimento de novos plugins. Aqui estão algumas melhorias propostas:

### 1. Implementações Padrão para Métodos Comuns

```python
class BasePlugin:
    # ... código existente ...
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Implementação padrão para processamento de mensagens.
        Os plugins devem sobrescrever este método para adicionar funcionalidades.
        
        Args:
            message: Texto da mensagem
            context: Contexto da conversa (opcional)
            
        Returns:
            Contexto atualizado
        """
        if context is None:
            context = {}
        return context
    
    def process_response(self, response: str, context: Dict[str, Any] = None) -> str:
        """
        Implementação padrão para processamento de respostas.
        Os plugins devem sobrescrever este método para adicionar funcionalidades.
        
        Args:
            response: Texto da resposta
            context: Contexto da conversa (opcional)
            
        Returns:
            Resposta processada
        """
        return response
    
    def cleanup(self):
        """
        Implementação padrão para limpeza de recursos.
        Os plugins devem sobrescrever este método se precisarem liberar recursos.
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Retorna metadados do plugin.
        
        Returns:
            Dicionário com metadados do plugin
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "version": self.config.get("version", "1.0.0"),
            "description": self.__doc__ or "Sem descrição disponível"
        }
```

### 2. Gerenciamento de Dependências

```python
def check_dependencies(self) -> bool:
    """
    Verifica se todas as dependências do plugin estão disponíveis.
    
    Returns:
        True se todas as dependências estão disponíveis, False caso contrário
    """
    dependencies = self.config.get("dependencies", [])
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"Plugin {self.name}: Dependências faltando: {', '.join(missing)}")
        return False
    
    return True
```

### 3. Sistema de Logs Integrado

```python
import logging

# No construtor
self.logger = logging.getLogger(f"plugin.{self.name}")

def log(self, level: str, message: str, *args, **kwargs):
    """
    Registra uma mensagem de log.
    
    Args:
        level: Nível do log (debug, info, warning, error, critical)
        message: Mensagem a ser registrada
        args, kwargs: Argumentos adicionais para formatação da mensagem
    """
    getattr(self.logger, level.lower())(message, *args, **kwargs)
```

## Validação Durante o Carregamento de Plugins

Para garantir que os plugins implementem todos os métodos necessários e sejam compatíveis com o sistema, podemos adicionar validação durante o carregamento:

### Implementação no PluginManager

```python
def validate_plugin(self, plugin_instance) -> bool:
    """
    Valida se um plugin implementa todos os métodos necessários.
    
    Args:
        plugin_instance: Instância do plugin a ser validada
        
    Returns:
        True se o plugin é válido, False caso contrário
    """
    # Métodos obrigatórios que todos os plugins devem implementar
    required_methods = [
        "initialize",
        "process_message",
        "validate_config"
    ]
    
    # Verificar se todos os métodos obrigatórios estão implementados
    for method in required_methods:
        if not hasattr(plugin_instance, method) or not callable(getattr(plugin_instance, method)):
            self.logger.error(f"Plugin {plugin_instance.name} não implementa o método obrigatório '{method}'")
            return False
    
    # Verificar a assinatura do método process_message
    import inspect
    try:
        sig = inspect.signature(plugin_instance.process_message)
        params = list(sig.parameters.keys())
        if len(params) < 2 or params[0] != 'self':
            self.logger.error(f"Plugin {plugin_instance.name}: método process_message tem assinatura inválida")
            return False
    except Exception as e:
        self.logger.error(f"Erro ao verificar assinatura do método process_message: {str(e)}")
        return False
    
    # Verificar se a configuração é válida
    if not plugin_instance.validate_config():
        self.logger.error(f"Plugin {plugin_instance.name}: configuração inválida")
        return False
    
    # Verificar dependências
    if hasattr(plugin_instance, "check_dependencies") and callable(plugin_instance.check_dependencies):
        if not plugin_instance.check_dependencies():
            self.logger.error(f"Plugin {plugin_instance.name}: dependências não satisfeitas")
            return False
    
    return True
```

### Uso no Método load_plugins

```python
def load_plugins(self):
    """
    Carrega e inicializa os plugins habilitados.
    
    Returns:
        Dict[str, BasePlugin]: Dicionário com os plugins carregados
    """
    loaded_plugins = {}
    
    for plugin_name in self.config.get("enabled_plugins", []):
        try:
            # Importar e instanciar o plugin
            plugin_instance = self._import_plugin(plugin_name)
            
            # Validar o plugin
            if not self.validate_plugin(plugin_instance):
                self.logger.warning(f"Plugin {plugin_name} falhou na validação e não será carregado")
                continue
            
            # Adicionar ao dicionário de plugins carregados
            loaded_plugins[plugin_name] = plugin_instance
            self.logger.info(f"Plugin {plugin_name} carregado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar plugin {plugin_name}: {str(e)}")
    
    return loaded_plugins
```

## Plugins vs. Tools do CrewAI: Complementares, não Redundantes

### Diferenças Fundamentais

| Característica | Plugins do ChatwootAI | Tools do CrewAI |
|----------------|------------------------|------------------|
| **Escopo** | Sistema-wide, afetam todo o fluxo de mensagens | Específicas para agentes individuais |
| **Persistência** | Persistentes durante toda a execução | Utilizadas apenas durante a execução de um agente |
| **Configuração** | Configuráveis via YAML por domínio | Definidas no código dos agentes |
| **Extensibilidade** | Facilmente extensíveis sem modificar o código base | Requerem modificação dos agentes |
| **Integração** | Integrados ao pipeline de processamento de mensagens | Utilizadas sob demanda pelos agentes |
| **Momento de Atuação** | Atuam como middleware, antes e depois dos agentes | Utilizadas durante o processamento dos agentes |
| **Flexibilidade** | Podem ser ativados/desativados por domínio | Geralmente fixas para cada tipo de agente |

### Vantagens dos Plugins no Contexto do Projeto

1. **Processamento Transversal**: Os plugins podem processar todas as mensagens e respostas, independentemente do agente que as está manipulando. Isso permite funcionalidades como análise de sentimento, enriquecimento de respostas e integração com FAQs de forma consistente.

2. **Adaptação por Domínio**: Os plugins podem ser ativados ou desativados com base no domínio de negócio atual, permitindo comportamentos específicos para cada domínio sem modificar os agentes.

3. **Separação de Responsabilidades**: Os plugins lidam com funcionalidades específicas (como análise de sentimento), enquanto os agentes se concentram na lógica de negócios e no fluxo de conversação.

4. **Reutilização**: Os plugins podem ser reutilizados em diferentes partes do sistema, enquanto as tools são específicas para agentes.

5. **Configuração Dinâmica**: Os plugins podem ser configurados via YAML, permitindo ajustes sem recompilar o código.

### Por que Manter Ambos?

No contexto da nossa arquitetura hub-and-spoke com domínios configuráveis, manter tanto plugins quanto tools do CrewAI oferece vantagens significativas:

1. **Separação de Responsabilidades**: 
   - **Plugins**: Cuidam de aspectos transversais como análise de sentimento, enriquecimento de respostas e integração com FAQs.
   - **Tools**: Permitem que agentes realizem ações específicas como consultas a bancos de dados, cálculos e chamadas a APIs externas.

2. **Flexibilidade por Domínio**: 
   - Os plugins podem ser facilmente ativados/desativados por domínio via YAML, enquanto as tools permanecem consistentes.
   - Isso permite adaptar o comportamento do sistema para diferentes domínios sem modificar o código dos agentes.

3. **Arquitetura Hub-and-Spoke**: 
   - O `HubCrew` central pode aplicar plugins universalmente a todas as mensagens.
   - As crews especializadas (SalesCrew, SupportCrew, etc.) podem usar tools específicas para suas necessidades.

### Exemplo Prático: Fluxo de uma Mensagem

Vamos ver como plugins e tools trabalham juntos no fluxo de uma mensagem típica:

```
Cliente: "Você tem creme para as mãos?"
```

#### 1. Processamento de Entrada (Plugins)

```python
# A mensagem chega ao sistema e é processada pelos plugins ativos
plugins = plugin_manager.get_active_plugins()

# Contexto inicial vazio
context = {}

# Cada plugin processa a mensagem e atualiza o contexto
for plugin in plugins:
    if plugin.is_enabled():
        context = plugin.process_message("Você tem creme para as mãos?", context)

# Após processamento pelos plugins, o contexto pode conter:
# {
#    "sentiment": {"sentiment": "neutral", "confidence": 0.92},
#    "faq_match": {"matched": False, "confidence": 0.15}
# }
```

#### 2. Processamento pelo Agente (Tools)

```python
# O HubCrew determina que esta é uma consulta de produto e encaminha para o SalesAgent
sales_agent = SalesAgent(config)

# O agente processa a mensagem usando suas tools
def process(self, message, context):
    # Verificar o sentimento (adicionado pelo plugin)
    sentiment = context.get("sentiment", {}).get("sentiment", "neutral")
    
    # Usar a tool de busca de produtos
    product_results = self.tools["search_product"].execute("creme para as mãos")
    
    # Usar a tool de verificação de estoque
    inventory = self.tools["check_inventory"].execute(product_results["product_ids"])
    
    # Gerar resposta com base nas informações obtidas
    response = f"Sim, temos {len(inventory)} opções de cremes para as mãos disponíveis."
    
    return response, context
```

#### 3. Processamento de Saída (Plugins)

```python
# A resposta gerada pelo agente é processada pelos plugins de saída
response = "Sim, temos 5 opções de cremes para as mãos disponíveis."

# Cada plugin processa a resposta
for plugin in plugins:
    if plugin.is_enabled() and hasattr(plugin, "process_response"):
        response = plugin.process_response(response, context)

# Após processamento, a resposta pode ser enriquecida:
# "Sim, temos 5 opções de cremes para as mãos disponíveis. 
# Nossa linha premium Hydra+ está com 15% de desconto esta semana! 
# Gostaria de conhecer as opções?"
```

### Uso Complementar na Arquitetura

No contexto do ChatwootAI, plugins e tools do CrewAI são complementares, não redundantes:

- **Plugins**: Funcionam como camadas de middleware que processam todas as mensagens e respostas, independentemente do agente que as está manipulando.
- **Tools do CrewAI**: São ferramentas específicas que os agentes usam para realizar tarefas durante seu processamento.

#### Diagrama de Fluxo

```
[Cliente] → [Chatwoot] → [Webhook] → [HubCrew]
                                        |
                                        ↓
[Plugins de Entrada] → [Contexto Enriquecido]
                                        |
                                        ↓
[Agente com Tools] → [Resposta Inicial]
                                        |
                                        ↓
[Plugins de Saída] → [Resposta Enriquecida]
                                        |
                                        ↓
[HubCrew] → [Chatwoot] → [Cliente]
```

### Exemplo de Código Completo

```python
# Um agente usando tools enquanto se beneficia de plugins
class SalesAgent(Agent):
    def __init__(self, config):
        super().__init__(config)
        self.tools = {
            "search_product": SearchProductTool(),  # Tool para busca de produtos
            "check_inventory": CheckInventoryTool(),  # Tool para verificar estoque
            "calculate_price": CalculatePriceTool()  # Tool para cálculo de preços
        }
    
    def process(self, message, context):
        # O contexto já foi enriquecido pelos plugins
        # Por exemplo, o SentimentAnalysisPlugin adicionou informações de sentimento
        sentiment = context.get("sentiment", {}).get("sentiment", "neutral")
        
        # O FAQKnowledgePlugin verificou se há uma resposta pronta
        faq_match = context.get("faq_match", {})
        
        # Se houver uma resposta pronta com alta confiança, usá-la
        if faq_match.get("matched", False) and faq_match.get("confidence", 0) > 0.8:
            return faq_match.get("response"), context
        
        # Caso contrário, usar tools para buscar informações
        if "creme" in message.lower() or "produto" in message.lower():
            # Usar a tool de busca de produtos
            product_info = self.tools["search_product"].execute(message)
            
            # Verificar estoque usando outra tool
            inventory = self.tools["check_inventory"].execute(product_info["product_ids"])
            
            # Calcular preços com desconto usando uma terceira tool
            prices = self.tools["calculate_price"].execute(
                product_info["product_ids"], 
                context.get("customer", {}).get("loyalty_level", "regular")
            )
            
            # Construir resposta com as informações obtidas
            response = f"Encontrei {len(inventory)} produtos que podem te interessar."
            
            # A resposta será processada pelos plugins de saída antes de ser enviada
            # Por exemplo, o ResponseEnhancerPlugin pode adicionar sugestões
            return response, context
        
        # Resposta padrão
        return "Como posso ajudar com nossos produtos?", context
```

Neste exemplo completo, vemos como os plugins enriquecem o contexto antes do agente processá-lo, e como o agente usa tools específicas para realizar tarefas durante seu processamento. Depois, os plugins de saída podem enriquecer a resposta antes de enviá-la ao cliente.

Esta abordagem combinada oferece o melhor dos dois mundos: processamento transversal consistente via plugins e ações específicas flexíveis via tools.

## Conclusão

O sistema de plugins do ChatwootAI fornece uma camada de extensibilidade poderosa que complementa as tools do CrewAI. Enquanto as tools permitem que agentes individuais realizem ações específicas, os plugins afetam todo o fluxo de mensagens e podem ser configurados por domínio.

Ao implementar as melhorias propostas para a classe BasePlugin e adicionar validação durante o carregamento, o sistema se tornará mais robusto e fácil de estender, permitindo a criação de novos plugins com menos esforço e maior confiabilidade.
