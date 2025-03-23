"""
Tasks para o WhatsApp Channel Crew.

Este módulo define as tasks específicas para processamento de mensagens do WhatsApp
na arquitetura hub-and-spoke.
"""

import logging
from typing import Dict, Any, List, Optional
from crewai import Task
from crewai.agent import Agent

logger = logging.getLogger(__name__)


def create_message_normalization_task(agent: Agent) -> Task:
    """
    Cria uma task para normalização de mensagens do WhatsApp.
    
    Esta task é responsável por padronizar o formato das mensagens recebidas
    do WhatsApp, extraindo informações relevantes e preparando-as para
    processamento posterior.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de normalização de mensagens
    """
    return Task(
        description="""
        Normalize a mensagem recebida do WhatsApp para um formato padrão.
        
        Analise a mensagem e extraia as seguintes informações:
        1. Conteúdo principal da mensagem
        2. Informações do remetente
        3. Metadados da conversa
        4. Anexos (se houver)
        
        Formate a mensagem em um formato padronizado que possa ser processado
        pelos demais componentes do sistema.
        """,
        expected_output="""
        {
            "normalized_content": "Conteúdo normalizado da mensagem",
            "sender_info": {
                "name": "Nome do remetente",
                "phone": "Número de telefone",
                "profile": "Informações de perfil disponíveis"
            },
            "metadata": {
                "timestamp": "Data e hora da mensagem",
                "conversation_id": "ID da conversa",
                "message_type": "Tipo de mensagem (texto, mídia, etc.)"
            },
            "attachments": [
                {
                    "type": "Tipo do anexo",
                    "url": "URL do anexo",
                    "filename": "Nome do arquivo"
                }
            ]
        }
        """,
        agent=agent,
        name="Normalização de Mensagem do WhatsApp"
    )


def create_intent_detection_task(agent: Agent) -> Task:
    """
    Cria uma task para detecção de intenção em mensagens do WhatsApp.
    
    Esta task analisa o conteúdo normalizado da mensagem para identificar
    a intenção do usuário, categorizando-a para roteamento adequado.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de detecção de intenção
    """
    return Task(
        description="""
        Analise a mensagem normalizada do WhatsApp e detecte a intenção do usuário.
        
        Considere as seguintes categorias de intenção:
        - sales_inquiry: Perguntas sobre produtos, preços, promoções
        - support_request: Solicitações de ajuda, problemas técnicos
        - scheduling_request: Agendamentos, consultas, reservas
        - info_request: Informações gerais sobre a empresa, produtos, serviços
        - feedback: Avaliações, opiniões, sugestões
        - general_inquiry: Outras mensagens que não se encaixam nas categorias acima
        
        Analise cuidadosamente o conteúdo da mensagem, identificando palavras-chave,
        contexto e padrões que indiquem a intenção do usuário.
        """,
        expected_output="""
        {
            "primary_intent": "Intenção principal detectada",
            "confidence_score": 0.95,
            "secondary_intents": ["Intenção secundária 1", "Intenção secundária 2"],
            "keywords_detected": ["palavra-chave1", "palavra-chave2"],
            "intent_analysis": "Análise detalhada da intenção detectada"
        }
        """,
        agent=agent,
        name="Detecção de Intenção em Mensagem do WhatsApp"
    )


def create_metadata_extraction_task(agent: Agent) -> Task:
    """
    Cria uma task para extração de metadados de mensagens do WhatsApp.
    
    Esta task extrai informações adicionais da mensagem e do contexto
    da conversa para enriquecer o processamento.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de extração de metadados
    """
    return Task(
        description="""
        Extraia metadados relevantes da mensagem do WhatsApp e do contexto da conversa.
        
        Identifique e extraia:
        1. Informações do dispositivo (se disponíveis)
        2. Localização do usuário (se disponível)
        3. Horário da mensagem e fuso horário
        4. Histórico recente da conversa
        5. Status da conversa (nova, em andamento, reaberta)
        
        Estes metadados serão utilizados para enriquecer o contexto da mensagem
        e melhorar a precisão do processamento.
        """,
        expected_output="""
        {
            "device_info": {
                "type": "Tipo de dispositivo",
                "os": "Sistema operacional",
                "app_version": "Versão do aplicativo"
            },
            "location": {
                "country": "País",
                "region": "Região",
                "timezone": "Fuso horário"
            },
            "conversation_status": "Status da conversa",
            "conversation_history": [
                {
                    "timestamp": "Data e hora",
                    "sender": "Remetente",
                    "content": "Conteúdo resumido"
                }
            ],
            "additional_context": {
                "business_hours": true,
                "previous_interactions": 5,
                "customer_segment": "Segmento do cliente"
            }
        }
        """,
        agent=agent,
        name="Extração de Metadados de Mensagem do WhatsApp"
    )


def create_message_preparation_task(agent: Agent) -> Task:
    """
    Cria uma task para preparação de mensagem para o Hub Crew.
    
    Esta task combina os resultados das tasks anteriores e prepara
    a mensagem para ser enviada ao Hub Crew para roteamento.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de preparação de mensagem
    """
    return Task(
        description="""
        Prepare a mensagem normalizada, com intenção detectada e metadados extraídos,
        para ser enviada ao Hub Crew para roteamento.
        
        Combine os resultados das tasks anteriores em um formato estruturado
        que contenha todas as informações necessárias para o Hub Crew
        rotear a mensagem para a crew funcional apropriada.
        
        Adicione quaisquer informações adicionais que possam ser úteis
        para o processamento posterior.
        """,
        expected_output="""
        {
            "normalized_message": {
                "content": "Conteúdo normalizado",
                "sender_info": {},
                "metadata": {},
                "attachments": []
            },
            "intent_analysis": {
                "primary_intent": "Intenção principal",
                "confidence_score": 0.95,
                "secondary_intents": []
            },
            "extracted_metadata": {
                "device_info": {},
                "location": {},
                "conversation_status": "",
                "conversation_history": []
            },
            "channel_specific": {
                "whatsapp_specific_feature1": "Valor",
                "whatsapp_specific_feature2": "Valor"
            },
            "routing_suggestion": "Nome da crew funcional sugerida",
            "processing_priority": "Prioridade sugerida (alta, média, baixa)"
        }
        """,
        agent=agent,
        name="Preparação de Mensagem para Hub Crew"
    )


def create_response_formatting_task(agent: Agent) -> Task:
    """
    Cria uma task para formatação de resposta para o WhatsApp.
    
    Esta task recebe a resposta gerada pela crew funcional e a formata
    de acordo com as especificidades do canal WhatsApp.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de formatação de resposta
    """
    return Task(
        description="""
        Formate a resposta gerada pela crew funcional para o canal WhatsApp.
        
        Considere as seguintes diretrizes:
        1. Respeite os limites de caracteres do WhatsApp
        2. Utilize formatação adequada (negrito, itálico, listas)
        3. Adapte links e referências para o formato do WhatsApp
        4. Prepare anexos e mídias de forma adequada
        5. Segmente mensagens longas de forma lógica, se necessário
        
        A resposta deve ser clara, concisa e otimizada para visualização
        em dispositivos móveis, seguindo as melhores práticas do WhatsApp.
        """,
        expected_output="""
        {
            "formatted_response": "Resposta formatada para o WhatsApp",
            "message_segments": [
                "Segmento 1 da mensagem",
                "Segmento 2 da mensagem"
            ],
            "has_formatting": true,
            "formatting_applied": ["negrito", "itálico", "listas"],
            "media_attachments": [
                {
                    "type": "Tipo de mídia",
                    "url": "URL da mídia",
                    "caption": "Legenda da mídia"
                }
            ],
            "quick_replies": [
                "Resposta rápida 1",
                "Resposta rápida 2"
            ]
        }
        """,
        agent=agent,
        name="Formatação de Resposta para WhatsApp"
    )


def create_whatsapp_tasks(processor_agent: Agent, monitor_agent: Agent) -> List[Task]:
    """
    Cria todas as tasks necessárias para o WhatsApp Channel Crew.
    
    Args:
        processor_agent: Agente de processamento de mensagens
        monitor_agent: Agente de monitoramento do canal
        
    Returns:
        List[Task]: Lista de todas as tasks para o WhatsApp Channel Crew
    """
    tasks = [
        create_message_normalization_task(processor_agent),
        create_intent_detection_task(processor_agent),
        create_metadata_extraction_task(processor_agent),
        create_message_preparation_task(processor_agent),
        create_response_formatting_task(processor_agent)
    ]
    
    return tasks
