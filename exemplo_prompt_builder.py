"""
Exemplo de implementação do PromptBuilder para o sistema ChatwootAI.

Este arquivo demonstra como o PromptBuilder pode ser usado para criar prompts
dinâmicos usando templates Jinja2.
"""

import jinja2
import os
from typing import Dict, Any, Optional, List
import json

class PromptBuilder:
    """
    Classe responsável por construir prompts dinâmicos usando templates Jinja2.
    """
    
    def __init__(self, templates_dir: str = None):
        """
        Inicializa o PromptBuilder.
        
        Args:
            templates_dir: Diretório contendo os templates de prompts.
                           Se None, usa o diretório padrão.
        """
        if templates_dir is None:
            # Obter o diretório do módulo atual
            current_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(current_dir, "templates")
        
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=False,  # Desabilitar escape automático para prompts
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Registrar filtros personalizados
        self._register_custom_filters()
    
    def _register_custom_filters(self):
        """Registra filtros personalizados para uso nos templates."""
        # Filtro para formatar listas em texto
        def format_list(items, bullet="•"):
            if not items:
                return ""
            return "\n".join(f"{bullet} {item}" for item in items)
        
        # Filtro para formatar dicionários em texto
        def format_dict(data, indent=0):
            if not data:
                return ""
            result = []
            spaces = " " * indent
            for key, value in data.items():
                if isinstance(value, dict):
                    result.append(f"{spaces}{key}:")
                    result.append(format_dict(value, indent + 2))
                elif isinstance(value, list):
                    result.append(f"{spaces}{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            result.append(format_dict(item, indent + 2))
                        else:
                            result.append(f"{spaces}  • {item}")
                else:
                    result.append(f"{spaces}{key}: {value}")
            return "\n".join(result)
        
        # Filtro para truncar texto
        def truncate_text(text, max_length=100):
            if not text or len(text) <= max_length:
                return text
            return text[:max_length] + "..."
        
        # Filtro para formatar data/hora
        def format_datetime(dt, format="%d/%m/%Y %H:%M"):
            if not dt:
                return ""
            if isinstance(dt, str):
                # Tentar converter de string para datetime
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                except (ValueError, ImportError):
                    return dt
            try:
                return dt.strftime(format)
            except:
                return str(dt)
        
        # Registrar os filtros
        self.env.filters["format_list"] = format_list
        self.env.filters["format_dict"] = format_dict
        self.env.filters["truncate"] = truncate_text
        self.env.filters["format_datetime"] = format_datetime
    
    def build_prompt(self, template_name: str, language: str = "pt", **kwargs) -> str:
        """
        Constrói um prompt a partir de um template.
        
        Args:
            template_name: Nome do template (sem extensão)
            language: Código do idioma (pt, en, etc.)
            **kwargs: Variáveis a serem passadas para o template
            
        Returns:
            Prompt renderizado
        """
        template_path = f"{language}/{template_name}.j2"
        try:
            template = self.env.get_template(template_path)
            return template.render(**kwargs)
        except jinja2.exceptions.TemplateNotFound:
            # Fallback para o idioma padrão se o template não existir no idioma solicitado
            if language != "pt":
                return self.build_prompt(template_name, "pt", **kwargs)
            # Se já estamos no idioma padrão, propagar o erro
            raise
    
    def add_template(self, template_name: str, language: str, content: str) -> None:
        """
        Adiciona um novo template ao ambiente.
        Útil para testes ou para adicionar templates dinamicamente.
        
        Args:
            template_name: Nome do template (sem extensão)
            language: Código do idioma (pt, en, etc.)
            content: Conteúdo do template
        """
        template_path = f"{language}/{template_name}.j2"
        self.env.loader.mapping[template_path] = content


# Exemplos de uso

def exemplo_intencao():
    """Exemplo de uso do PromptBuilder para um prompt de intenção."""
    # Criar um PromptBuilder com templates em memória para o exemplo
    builder = PromptBuilder()
    
    # Adicionar um template de intenção
    builder.add_template("intention", "pt", """
Você é um assistente especializado em identificar a intenção do cliente em mensagens.

Mensagem do cliente: {{ message }}

{% if context and context.history %}
Histórico da conversa:
{% for msg in context.history %}
{{ msg.role }}: {{ msg.content }}
{% endfor %}
{% endif %}

Analise a mensagem e identifique a intenção principal do cliente. Escolha uma das seguintes categorias:
{{ categories | format_list }}

Responda apenas com a categoria, sem explicações adicionais.
""")
    
    # Construir o prompt
    prompt = builder.build_prompt(
        "intention",
        language="pt",
        message="Olá, gostaria de saber o status do meu pedido #12345",
        categories=["informacao_produto", "suporte_tecnico", "reclamacao", "agendamento", "consulta_pedido", "duvida_geral"],
        context={
            "history": [
                {"role": "user", "content": "Olá, bom dia!"},
                {"role": "assistant", "content": "Bom dia! Como posso ajudar?"}
            ]
        }
    )
    
    print("=== EXEMPLO DE PROMPT DE INTENÇÃO ===")
    print(prompt)
    print()


def exemplo_regras_negocio():
    """Exemplo de uso do PromptBuilder para um prompt de regras de negócio."""
    # Criar um PromptBuilder com templates em memória para o exemplo
    builder = PromptBuilder()
    
    # Adicionar um template de regras de negócio
    builder.add_template("business_rules", "pt", """
Você é um assistente especializado em aplicar regras de negócio para responder a consultas de clientes.

Mensagem do cliente: {{ message }}

Intenção identificada: {{ intention }}

{% if business_rules %}
Regras de negócio aplicáveis:
{{ business_rules | format_dict }}
{% endif %}

{% if product_info %}
Informações do produto:
{{ product_info | format_dict }}
{% endif %}

Com base nas regras de negócio e nas informações disponíveis, forneça uma resposta clara e concisa para o cliente.
Mantenha um tom {{ communication_style }} e use {{ emoji_usage }} emojis.
""")
    
    # Construir o prompt
    prompt = builder.build_prompt(
        "business_rules",
        language="pt",
        message="Posso devolver um produto após 15 dias da compra?",
        intention="duvida_geral",
        business_rules={
            "politica_devolucao": {
                "prazo_maximo": "30 dias",
                "condicoes": [
                    "Produto em perfeito estado",
                    "Com embalagem original",
                    "Nota fiscal"
                ],
                "excecoes": [
                    "Produtos perecíveis",
                    "Produtos personalizados"
                ]
            }
        },
        product_info=None,
        communication_style="amigável",
        emoji_usage="moderado"
    )
    
    print("=== EXEMPLO DE PROMPT DE REGRAS DE NEGÓCIO ===")
    print(prompt)
    print()


def exemplo_resposta_final():
    """Exemplo de uso do PromptBuilder para um prompt de resposta final."""
    # Criar um PromptBuilder com templates em memória para o exemplo
    builder = PromptBuilder()
    
    # Adicionar um template de resposta final
    builder.add_template("response", "pt", """
Você é um assistente de atendimento ao cliente para {{ company_name }}.

Mensagem do cliente: {{ message }}

Intenção identificada: {{ intention }}

{% if business_rules_result %}
Resultado da consulta às regras de negócio:
{{ business_rules_result }}
{% endif %}

{% if product_info_result %}
Resultado da consulta às informações de produto:
{{ product_info_result }}
{% endif %}

{% if mcp_result %}
Resultado da consulta ao sistema:
{{ mcp_result | format_dict }}
{% endif %}

Gere uma resposta final para o cliente, integrando todas as informações disponíveis.
Mantenha um tom {{ communication_style }} e use {{ emoji_usage }} emojis.
Assine a mensagem como "{{ signature }}".
""")
    
    # Construir o prompt
    prompt = builder.build_prompt(
        "response",
        language="pt",
        company_name="Loja Virtual XYZ",
        message="Qual o prazo de entrega para o CEP 12345-678?",
        intention="consulta_entrega",
        business_rules_result="O prazo de entrega varia de acordo com a região e disponibilidade do produto.",
        product_info_result=None,
        mcp_result={
            "prazo_entrega": {
                "cep": "12345-678",
                "prazo_minimo": 3,
                "prazo_maximo": 5,
                "valor_frete": 15.90,
                "transportadora": "Entrega Rápida"
            }
        },
        communication_style="profissional",
        emoji_usage="moderado",
        signature="Atendimento Virtual XYZ"
    )
    
    print("=== EXEMPLO DE PROMPT DE RESPOSTA FINAL ===")
    print(prompt)
    print()


if __name__ == "__main__":
    exemplo_intencao()
    exemplo_regras_negocio()
    exemplo_resposta_final()
