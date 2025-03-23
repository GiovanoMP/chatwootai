"""
ConversationAnalyticsService - Serviço para análise e persistência de conversas.

Este serviço implementa funcionalidades para analisar conversas, extrair
informações relevantes e construir perfis enriquecidos de clientes com base
nas interações.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Union, Optional, Tuple

from .base_data_service import BaseDataService

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationAnalyticsService(BaseDataService):
    """
    Serviço de dados especializado em análise de conversas.
    
    Responsabilidades:
    - Analisar conversas para extrair pontos-chave, entidades, tópicos e sentimento
    - Armazenar resumos de conversas para análise posterior
    - Atualizar perfis de clientes com insights obtidos das conversas
    - Identificar tendências e padrões em conversas
    """
    
    def __init__(self, data_service_hub, nlp_processor=None):
        """
        Inicializa o serviço de análise de conversas.
        
        Args:
            data_service_hub: Instância do DataServiceHub.
            nlp_processor: Processador de linguagem natural (opcional).
                           Se não fornecido, usa uma implementação simples.
        """
        super().__init__(data_service_hub)
        self.nlp_processor = nlp_processor or SimplifiedNLPProcessor()
        logger.info("ConversationAnalyticsService inicializado")
    
    def get_entity_type(self) -> str:
        """
        Retorna o tipo de entidade gerenciada por este serviço.
        
        Returns:
            String representando o tipo de entidade.
        """
        return "conversation_analytics"
    
    def store_conversation_summary(self, conversation_id: str, customer_id: int, 
                                  channel: str, messages: List[Dict[str, Any]], 
                                  metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analisa e armazena um resumo da conversa, extraindo pontos-chave.
        
        Args:
            conversation_id: ID da conversa.
            customer_id: ID do cliente.
            channel: Canal da conversa (ex: whatsapp, web, instagram).
            messages: Lista de mensagens da conversa.
            metadata: Metadados adicionais da conversa.
            
        Returns:
            Resumo da conversa com análises.
        """
        logger.info(f"Analisando conversa: {conversation_id} (Cliente: {customer_id})")
        
        # Extrair apenas o conteúdo textual das mensagens
        message_texts = [msg.get('content', '') for msg in messages 
                         if isinstance(msg.get('content', ''), str)]
        
        # Calcular duração da conversa
        duration = self._calculate_conversation_duration(messages)
        
        # Analisar conversa utilizando processador de NLP
        sentiment_score = self.nlp_processor.analyze_sentiment(message_texts)
        entities = self.nlp_processor.extract_entities(message_texts)
        topics = self.nlp_processor.extract_topics(message_texts)
        key_points = self.nlp_processor.extract_key_points(message_texts)
        
        # Preparar dados para armazenamento
        now = datetime.now()
        
        # Serializar para JSON - garantir que são strings válidas
        topics_json = json.dumps(topics, default=self.hub._json_encoder)
        entities_json = json.dumps(entities, default=self.hub._json_encoder)
        key_points_json = json.dumps(key_points, default=self.hub._json_encoder)
        
        analytics_data = {
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "sentiment_score": sentiment_score,
            "topics": topics_json,
            "entities": entities_json,
            "key_points": key_points_json,
            "duration": duration,
            "message_count": len(messages),
            "created_at": now,
            "updated_at": now
        }
        
        # Verificar se já existe análise para esta conversa
        check_query = """
            SELECT id FROM conversation_analytics
            WHERE conversation_id = %(conversation_id)s
        """
        
        existing = self.hub.execute_query(check_query, 
                                         {"conversation_id": conversation_id}, 
                                         fetch_all=False)
        
        if existing:
            # Atualizar análise existente
            analytics_data['id'] = existing['id']
            
            set_clauses = [f"{key} = %({key})s" for key in analytics_data.keys()]
            set_clause = ", ".join(set_clauses)
            
            query = f"""
                UPDATE conversation_analytics
                SET {set_clause}
                WHERE id = %(id)s
                RETURNING *
            """
        else:
            # Inserir nova análise
            columns = ", ".join(analytics_data.keys())
            placeholders = ", ".join([f"%({key})s" for key in analytics_data.keys()])
            
            query = f"""
                INSERT INTO conversation_analytics ({columns})
                VALUES ({placeholders})
                RETURNING *
            """
        
        result = self.hub.execute_query(query, analytics_data, fetch_all=False)
        
        if not result:
            logger.error(f"Falha ao armazenar análise da conversa: {conversation_id}")
            return {}
        
        # Converter campos JSON para objetos Python
        for field in ['topics', 'entities', 'key_points']:
            if isinstance(result.get(field), str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    result[field] = []
        
        # Atualizar perfil do cliente com insights da conversa
        self._update_customer_profile_with_insights(customer_id, result)
        
        logger.info(f"Análise da conversa {conversation_id} armazenada com sucesso")
        return result
    
    def get_conversation_analysis(self, conversation_id: str) -> Dict[str, Any]:
        """
        Recupera a análise de uma conversa específica.
        
        Args:
            conversation_id: ID da conversa.
            
        Returns:
            Análise da conversa ou dicionário vazio se não encontrada.
        """
        query = """
            SELECT * FROM conversation_analytics
            WHERE conversation_id = %(conversation_id)s
        """
        
        result = self.hub.execute_query(query, {"conversation_id": conversation_id}, fetch_all=False)
        
        if not result:
            logger.warning(f"Análise não encontrada para conversa: {conversation_id}")
            return {}
        
        # Converter campos JSON para objetos Python
        for field in ['topics', 'entities', 'key_points']:
            if isinstance(result.get(field), str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    result[field] = []
        
        return result
    
    def get_conversation_insights(self, conversation_id: str) -> Dict[str, Any]:
        """
        Recupera insights e análise de uma conversa específica.
        
        Args:
            conversation_id: ID da conversa.
            
        Returns:
            Insights da conversa ou dicionário vazio se não encontrada.
        """
        # Verificar se tem no cache primeiro
        cache_key = f"conversation_insights:{conversation_id}"
        cached_data = self.hub.cache_get(cache_key)
        
        if cached_data:
            logger.info(f"Insights da conversa {conversation_id} recuperados do cache")
            # Verificar se os dados em cache são uma string JSON e deserializar
            if isinstance(cached_data, (str, bytes)):
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    logger.error(f"Erro ao deserializar insights em cache para conversa {conversation_id}")
            else:
                return cached_data
            
        # Se não estiver no cache, buscar do banco de dados
        result = self.get_conversation_analysis(conversation_id)
        
        # Armazenar no cache para futuras consultas - garantir que está serializado corretamente
        if result:
            # Serializar para JSON e depois deserializar para garantir que temos um objeto completamente serializável
            serialized_result = json.dumps(result, default=self.hub._json_encoder)
            self.hub.cache_set(cache_key, serialized_result, ttl=3600)  # 1 hora de TTL
            result = json.loads(serialized_result)
            
        return result
    
    def get_customer_conversation_history(self, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera o histórico de análises de conversas de um cliente.
        
        Args:
            customer_id: ID do cliente.
            limit: Número máximo de análises a retornar.
            
        Returns:
            Lista de análises de conversas do cliente.
        """
        query = """
            SELECT * FROM conversation_analytics
            WHERE customer_id = %(customer_id)s
            ORDER BY created_at DESC
            LIMIT %(limit)s
        """
        
        params = {
            "customer_id": customer_id,
            "limit": limit
        }
        
        results = self.hub.execute_query(query, params) or []
        
        # Converter campos JSON para objetos Python
        for result in results:
            for field in ['topics', 'entities', 'key_points']:
                if isinstance(result.get(field), str):
                    try:
                        result[field] = json.loads(result[field])
                    except json.JSONDecodeError:
                        result[field] = []
        
        return results
    
    def get_common_topics_for_customer(self, customer_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Identifica os tópicos mais comuns nas conversas de um cliente.
        
        Args:
            customer_id: ID do cliente.
            limit: Número máximo de tópicos a retornar.
            
        Returns:
            Lista dos tópicos mais comuns nas conversas do cliente.
        """
        # Recuperar todas as análises recentes
        analyses = self.get_customer_conversation_history(customer_id, limit=20)
        
        # Extrair e contar tópicos
        topic_counter = {}
        for analysis in analyses:
            for topic in analysis.get('topics', []):
                topic_name = topic.get('name', '')
                if topic_name:
                    if topic_name in topic_counter:
                        topic_counter[topic_name]['count'] += 1
                        topic_counter[topic_name]['confidence'] += topic.get('confidence', 0)
                    else:
                        topic_counter[topic_name] = {
                            'name': topic_name,
                            'count': 1,
                            'confidence': topic.get('confidence', 0)
                        }
        
        # Calcular confiança média e ordenar por contagem
        for topic in topic_counter.values():
            topic['confidence'] = topic['confidence'] / topic['count']
        
        sorted_topics = sorted(
            topic_counter.values(), 
            key=lambda x: (x['count'], x['confidence']), 
            reverse=True
        )
        
        return sorted_topics[:limit]
    
    def get_entity_preferences(self, customer_id: int, entity_type: str = None) -> List[Dict[str, Any]]:
        """
        Identifica as preferências do cliente com base em entidades extraídas.
        
        Args:
            customer_id: ID do cliente.
            entity_type: Tipo específico de entidade a filtrar (opcional).
            
        Returns:
            Lista de entidades preferidas pelo cliente.
        """
        # Recuperar todas as análises recentes
        analyses = self.get_customer_conversation_history(customer_id, limit=20)
        
        # Extrair e contar entidades
        entity_counter = {}
        for analysis in analyses:
            for entity in analysis.get('entities', []):
                entity_name = entity.get('text', '')
                entity_category = entity.get('category', '')
                
                # Filtrar por tipo se especificado
                if entity_type and entity_category != entity_type:
                    continue
                
                if entity_name and entity_category:
                    key = f"{entity_category}:{entity_name}"
                    if key in entity_counter:
                        entity_counter[key]['count'] += 1
                        entity_counter[key]['confidence'] += entity.get('confidence', 0)
                    else:
                        entity_counter[key] = {
                            'text': entity_name,
                            'category': entity_category,
                            'count': 1,
                            'confidence': entity.get('confidence', 0)
                        }
        
        # Calcular confiança média e ordenar por contagem
        for entity in entity_counter.values():
            entity['confidence'] = entity['confidence'] / entity['count']
        
        sorted_entities = sorted(
            entity_counter.values(), 
            key=lambda x: (x['count'], x['confidence']), 
            reverse=True
        )
        
        return sorted_entities
    
    def get_topic_trends(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Identifica as tendências de tópicos em todas as conversas.
        
        Args:
            days: Número de dias a considerar.
            limit: Número máximo de tópicos a retornar.
            
        Returns:
            Lista dos tópicos em tendência.
        """
        query = """
            SELECT 
                topics
            FROM conversation_analytics
            WHERE created_at >= NOW() - INTERVAL '%(days)s days'
            ORDER BY created_at DESC
        """
        
        params = {"days": days}
        
        results = self.hub.execute_query(query, params) or []
        
        # Extrair e contar tópicos
        topic_counter = {}
        for result in results:
            topics = result.get('topics', '[]')
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                except json.JSONDecodeError:
                    topics = []
            
            for topic in topics:
                topic_name = topic.get('name', '')
                if topic_name:
                    if topic_name in topic_counter:
                        topic_counter[topic_name]['count'] += 1
                    else:
                        topic_counter[topic_name] = {
                            'name': topic_name,
                            'count': 1
                        }
        
        # Ordenar por contagem
        sorted_topics = sorted(
            topic_counter.values(), 
            key=lambda x: x['count'], 
            reverse=True
        )
        
        return sorted_topics[:limit]
    
    def get_sentiment_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analisa tendências de sentimento ao longo do tempo.
        
        Args:
            days: Número de dias a considerar.
            
        Returns:
            Análise de tendências de sentimento.
        """
        query = """
            SELECT 
                DATE_TRUNC('day', created_at) as day,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(*) as conversation_count
            FROM conversation_analytics
            WHERE created_at >= NOW() - INTERVAL '%(days)s days'
            GROUP BY DATE_TRUNC('day', created_at)
            ORDER BY day
        """
        
        params = {"days": days}
        
        results = self.hub.execute_query(query, params) or []
        
        # Calcular estatísticas gerais
        total_count = sum(r.get('conversation_count', 0) for r in results)
        avg_sentiment = sum(r.get('avg_sentiment', 0) * r.get('conversation_count', 0) 
                          for r in results) / total_count if total_count > 0 else 0
        
        # Classificar dias por sentimento
        positive_days = sum(1 for r in results if r.get('avg_sentiment', 0) > 0.2)
        negative_days = sum(1 for r in results if r.get('avg_sentiment', 0) < -0.2)
        neutral_days = len(results) - positive_days - negative_days
        
        return {
            'daily_trends': results,
            'total_conversations': total_count,
            'average_sentiment': avg_sentiment,
            'positive_days': positive_days,
            'neutral_days': neutral_days,
            'negative_days': negative_days,
            'days_analyzed': len(results)
        }
    
    def _calculate_conversation_duration(self, messages: List[Dict[str, Any]]) -> Optional[int]:
        """
        Calcula a duração de uma conversa em segundos.
        
        Args:
            messages: Lista de mensagens da conversa.
            
        Returns:
            Duração em segundos ou None se não for possível calcular.
        """
        if not messages or len(messages) < 2:
            return None
        
        # Ordenar mensagens por timestamp
        sorted_messages = sorted(
            messages, 
            key=lambda x: x.get('created_at', ''),
            reverse=False
        )
        
        try:
            first_time = datetime.fromisoformat(sorted_messages[0].get('created_at', '').replace('Z', '+00:00'))
            last_time = datetime.fromisoformat(sorted_messages[-1].get('created_at', '').replace('Z', '+00:00'))
            
            duration = (last_time - first_time).total_seconds()
            return int(duration)
        except (ValueError, TypeError, AttributeError):
            logger.warning("Não foi possível calcular a duração da conversa")
            return None
    
    def _update_customer_profile_with_insights(self, customer_id: int, analysis: Dict[str, Any]) -> bool:
        """
        Atualiza o perfil do cliente com insights da conversa.
        
        Args:
            customer_id: ID do cliente.
            analysis: Análise da conversa.
            
        Returns:
            True se atualizado com sucesso, False caso contrário.
        """
        try:
            # Obter serviço de cliente
            customer_service = self.hub.get_service('CustomerDataService')
            if not customer_service:
                logger.warning("CustomerDataService não encontrado, não foi possível atualizar perfil do cliente")
                return False
            
            # Extrair tópicos e entidades relevantes
            topics = analysis.get('topics', [])
            entities = analysis.get('entities', [])
            
            # Atualizar preferências do cliente
            
            # 1. Armazenar tópicos de interesse
            if topics:
                topics_of_interest = customer_service.get_preference(customer_id, 'topics_of_interest') or []
                
                # Adicionar novos tópicos
                for topic in topics:
                    topic_name = topic.get('name', '')
                    if topic_name and topic_name not in [t.get('name') for t in topics_of_interest]:
                        topics_of_interest.append({
                            'name': topic_name,
                            'first_mentioned': datetime.now().isoformat(),
                            'mentions': 1
                        })
                    else:
                        # Incrementar menções para tópicos existentes
                        for t in topics_of_interest:
                            if t.get('name') == topic_name:
                                t['mentions'] = t.get('mentions', 0) + 1
                
                # Armazenar preferências atualizadas
                customer_service.set_preference(customer_id, 'topics_of_interest', topics_of_interest)
            
            # 2. Armazenar entidades (produtos, locais, etc)
            for entity in entities:
                category = entity.get('category', '')
                if category in ['PRODUCT', 'LOCATION', 'ORGANIZATION']:
                    pref_key = f"{category.lower()}_mentions"
                    mentions = customer_service.get_preference(customer_id, pref_key) or []
                    
                    entity_text = entity.get('text', '')
                    if entity_text:
                        # Verificar se já existe
                        found = False
                        for mention in mentions:
                            if mention.get('text') == entity_text:
                                mention['count'] = mention.get('count', 0) + 1
                                found = True
                                break
                        
                        # Adicionar nova menção
                        if not found:
                            mentions.append({
                                'text': entity_text,
                                'count': 1,
                                'first_mentioned': datetime.now().isoformat()
                            })
                        
                        # Armazenar preferências atualizadas
                        customer_service.set_preference(customer_id, pref_key, mentions)
            
            # 3. Atualizar sentimento geral do cliente
            sentiment_history = customer_service.get_preference(customer_id, 'sentiment_history') or []
            sentiment_history.append({
                'timestamp': datetime.now().isoformat(),
                'score': analysis.get('sentiment_score', 0),
                'conversation_id': analysis.get('conversation_id')
            })
            
            # Manter apenas os últimos 10 registros de sentimento
            if len(sentiment_history) > 10:
                sentiment_history = sentiment_history[-10:]
            
            customer_service.set_preference(customer_id, 'sentiment_history', sentiment_history)
            
            logger.info(f"Perfil do cliente {customer_id} atualizado com insights da conversa")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil do cliente com insights: {str(e)}")
            return False


class SimplifiedNLPProcessor:
    """
    Implementação simplificada de processador de linguagem natural.
    
    Em um ambiente de produção, você usaria uma biblioteca como spaCy,
    NLTK, ou um serviço de NLP como OpenAI, Google NLP, etc.
    """
    
    def analyze_sentiment(self, texts: List[str]) -> float:
        """
        Analisa o sentimento do texto.
        
        Args:
            texts: Lista de textos para analisar.
            
        Returns:
            Pontuação de sentimento entre -1.0 (muito negativo) e 1.0 (muito positivo).
        """
        # Implementação simplificada - em produção, use uma API de NLP real
        positive_words = ['bom', 'excelente', 'ótimo', 'adorei', 'feliz', 'agradecido', 'satisfeito']
        negative_words = ['ruim', 'péssimo', 'horrível', 'odiei', 'irritado', 'chateado', 'insatisfeito']
        
        # Concatenar textos
        full_text = " ".join(texts).lower()
        
        # Contar ocorrências
        positive_count = sum(1 for word in positive_words if word in full_text)
        negative_count = sum(1 for word in negative_words if word in full_text)
        
        # Calcular pontuação
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        return (positive_count - negative_count) / total
    
    def extract_entities(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Extrai entidades dos textos.
        
        Args:
            texts: Lista de textos para analisar.
            
        Returns:
            Lista de entidades extraídas.
        """
        # Implementação simplificada - em produção, use uma API de NLP real
        entities = []
        
        # Concatenar textos
        full_text = " ".join(texts).lower()
        
        # Produtos conhecidos
        products = ['smartphone', 'notebook', 'tablet', 'monitor', 'smartwatch', 'fone', 'carregador']
        for product in products:
            if product in full_text:
                entities.append({
                    'text': product,
                    'category': 'PRODUCT',
                    'confidence': 0.8
                })
        
        # Locais conhecidos
        locations = ['são paulo', 'rio de janeiro', 'belo horizonte', 'brasília', 'curitiba']
        for location in locations:
            if location in full_text:
                entities.append({
                    'text': location,
                    'category': 'LOCATION',
                    'confidence': 0.8
                })
        
        return entities
    
    def extract_topics(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Extrai tópicos dos textos.
        
        Args:
            texts: Lista de textos para analisar.
            
        Returns:
            Lista de tópicos extraídos.
        """
        # Implementação simplificada - em produção, use uma API de NLP real
        topics = []
        
        # Concatenar textos
        full_text = " ".join(texts).lower()
        
        # Tópicos conhecidos
        topic_keywords = {
            'compra': ['comprar', 'comprei', 'adquirir', 'preço', 'custo', 'valor'],
            'suporte': ['ajuda', 'suporte', 'problema', 'quebrou', 'defeito', 'erro'],
            'entrega': ['entrega', 'receber', 'envio', 'correio', 'prazo', 'chegou'],
            'devolução': ['devolver', 'devolução', 'reembolso', 'trocar', 'troca'],
            'informação': ['informação', 'dúvida', 'como', 'quando', 'onde', 'quem']
        }
        
        # Verificar tópicos
        for topic, keywords in topic_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in full_text)
            if matches > 0:
                confidence = min(0.5 + (matches * 0.1), 0.9)  # Máximo de 0.9
                topics.append({
                    'name': topic,
                    'confidence': confidence
                })
        
        return topics
    
    def extract_key_points(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Extrai pontos-chave dos textos.
        
        Args:
            texts: Lista de textos para analisar.
            
        Returns:
            Lista de pontos-chave extraídos.
        """
        # Implementação simplificada - em produção, use uma API de NLP real
        key_points = []
        
        # Concatenar textos
        full_text = " ".join(texts)
        
        # Dividir em frases
        sentences = [s.strip() for s in full_text.split('.') if s.strip()]
        
        # Identificar sentenças importantes (simplificado)
        important_phrases = ['preciso', 'quero', 'gostaria', 'problema', 'ajuda', 'como']
        
        for sentence in sentences:
            if any(phrase in sentence.lower() for phrase in important_phrases):
                key_points.append({
                    'text': sentence,
                    'importance': 0.7
                })
        
        return key_points
