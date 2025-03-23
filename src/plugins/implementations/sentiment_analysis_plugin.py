"""
Plugin para análise de sentimento das mensagens.

Este plugin analisa o sentimento das mensagens dos clientes
para adaptar o tom das respostas.
"""
import logging
from typing import Dict, Any, Optional
import re

from src.plugins.base.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class SentimentAnalysisPlugin(BasePlugin):
    """
    Plugin para análise de sentimento das mensagens.
    
    Analisa o sentimento das mensagens dos clientes para adaptar
    o tom das respostas de acordo com o estado emocional detectado.
    """
    
    def initialize(self):
        """
        Inicializa o plugin carregando recursos necessários.
        """
        logger.info("Inicializando plugin de análise de sentimento")
        
        # Palavras positivas e negativas para análise simples
        self.positive_words = self.config.get("positive_words", [
            "bom", "ótimo", "excelente", "adorei", "gostei", "maravilhoso",
            "perfeito", "fantástico", "incrível", "satisfeito", "feliz"
        ])
        
        self.negative_words = self.config.get("negative_words", [
            "ruim", "péssimo", "horrível", "detestei", "odiei", "terrível",
            "insatisfeito", "decepcionado", "frustrado", "chateado", "irritado"
        ])
        
        # Configurações
        self.threshold = self.config.get("threshold", 0.3)
        
        logger.info(f"Plugin de análise de sentimento inicializado com {len(self.positive_words)} palavras positivas e {len(self.negative_words)} palavras negativas")
    
    def analyze_sentiment(self, message: str) -> Dict[str, Any]:
        """
        Analisa o sentimento de uma mensagem.
        
        Args:
            message: Texto da mensagem a ser analisada
            
        Returns:
            Dict contendo o sentimento detectado e sua pontuação
        """
        if not message:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        
        # Normalizar texto
        text = message.lower()
        words = re.findall(r'\w+', text)
        
        if not words:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        
        # Contar palavras positivas e negativas
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        # Calcular pontuação
        total_sentiment_words = positive_count + negative_count
        total_words = len(words)
        
        if total_sentiment_words == 0:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.5}
        
        # Pontuação entre -1 (negativo) e 1 (positivo)
        score = (positive_count - negative_count) / total_sentiment_words
        
        # Confiança baseada na proporção de palavras de sentimento no texto
        confidence = min(1.0, total_sentiment_words / total_words + 0.2)
        
        # Determinar sentimento
        if score > self.threshold:
            sentiment = "positive"
        elif score < -self.threshold:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "details": {
                "positive_words": positive_count,
                "negative_words": negative_count,
                "total_words": total_words
            }
        }
    
    def adapt_response(self, response: str, sentiment: Dict[str, Any]) -> str:
        """
        Adapta a resposta com base no sentimento detectado.
        
        Args:
            response: Resposta original
            sentiment: Resultado da análise de sentimento
            
        Returns:
            Resposta adaptada ao sentimento do cliente
        """
        if not response:
            return response
            
        detected = sentiment.get("sentiment", "neutral")
        
        # Adaptar resposta conforme sentimento
        if detected == "positive":
            # Cliente está feliz, manter tom positivo
            return response
        elif detected == "negative":
            # Cliente está insatisfeito, adicionar empatia
            templates = [
                f"Entendo sua frustração. {response}",
                f"Lamento que esteja enfrentando dificuldades. {response}",
                f"Peço desculpas pelo inconveniente. {response}"
            ]
            import random
            return random.choice(templates)
        else:
            # Sentimento neutro, resposta normal
            return response
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem, analisando seu sentimento.
        
        Args:
            message: Texto da mensagem
            context: Contexto da conversa
            
        Returns:
            Contexto atualizado com informações de sentimento
        """
        sentiment = self.analyze_sentiment(message)
        
        # Atualizar contexto com o sentimento
        updated_context = context.copy()
        updated_context["sentiment"] = sentiment
        
        logger.info(f"Sentimento detectado: {sentiment['sentiment']} (score: {sentiment['score']:.2f}, confiança: {sentiment['confidence']:.2f})")
        
        return updated_context
    
    def process_response(self, response: str, context: Dict[str, Any]) -> str:
        """
        Processa uma resposta, adaptando-a ao sentimento do cliente.
        
        Args:
            response: Resposta original
            context: Contexto da conversa
            
        Returns:
            Resposta adaptada
        """
        if "sentiment" not in context:
            return response
            
        sentiment = context["sentiment"]
        adapted_response = self.adapt_response(response, sentiment)
        
        return adapted_response
