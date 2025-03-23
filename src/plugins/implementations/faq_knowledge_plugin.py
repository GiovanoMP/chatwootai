"""
Plugin para integração com base de conhecimento e FAQs.

Este plugin permite consultar uma base de conhecimento para responder
perguntas frequentes dos clientes automaticamente.
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple

from src.plugins.base.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class FAQKnowledgePlugin(BasePlugin):
    """
    Plugin para integração com base de conhecimento e FAQs.
    
    Permite consultar uma base de conhecimento para responder
    perguntas frequentes dos clientes automaticamente.
    """
    
    def initialize(self):
        """
        Inicializa o plugin carregando a base de conhecimento.
        """
        logger.info("Inicializando plugin de base de conhecimento e FAQs")
        
        # Carregar base de conhecimento da configuração ou usar dados de exemplo
        self.knowledge_base = self.config.get("knowledge_base", self._load_sample_knowledge_base())
        
        # Configurações
        self.min_similarity_score = self.config.get("min_similarity_score", 0.7)
        self.max_results = self.config.get("max_results", 3)
        
        logger.info(f"Plugin de FAQs inicializado com {len(self.knowledge_base)} itens na base de conhecimento")
    
    def _load_sample_knowledge_base(self) -> List[Dict[str, Any]]:
        """
        Carrega uma base de conhecimento de exemplo para testes.
        
        Returns:
            Lista de itens da base de conhecimento
        """
        return [
            {
                "question": "Como faço para devolver um produto?",
                "answer": "Para devolver um produto, você tem até 7 dias após o recebimento. Entre em contato com nosso suporte pelo WhatsApp ou email com o número do pedido e o motivo da devolução. Enviaremos instruções para o processo de devolução.",
                "tags": ["devolução", "troca", "produto", "pedido"],
                "category": "pós-venda"
            },
            {
                "question": "Qual o prazo de entrega?",
                "answer": "O prazo de entrega varia conforme sua localização. Após a confirmação do pagamento, o prazo médio é de 2 a 5 dias úteis para capitais e 5 a 10 dias úteis para demais localidades. Você receberá o código de rastreamento por email.",
                "tags": ["entrega", "prazo", "frete", "envio"],
                "category": "logística"
            },
            {
                "question": "Vocês têm loja física?",
                "answer": "Sim, temos lojas físicas em São Paulo, Rio de Janeiro e Belo Horizonte. Você pode encontrar os endereços e horários de funcionamento em nosso site na seção 'Nossas Lojas'.",
                "tags": ["loja", "física", "endereço", "presencial"],
                "category": "institucional"
            },
            {
                "question": "Como aplicar o protetor solar corretamente?",
                "answer": "Para aplicar o protetor solar corretamente, use aproximadamente uma colher de chá para o rosto e pescoço. Aplique 30 minutos antes da exposição ao sol e reaplique a cada 2 horas ou após nadar ou suar. Não esqueça de áreas como orelhas e nuca.",
                "tags": ["protetor", "solar", "aplicação", "uso", "dicas"],
                "category": "uso de produtos"
            },
            {
                "question": "Quais produtos são indicados para pele oleosa?",
                "answer": "Para pele oleosa, recomendamos produtos oil-free, não comedogênicos e com ingredientes como ácido salicílico, niacinamida e argilas. Nossa linha Controle de Oleosidade foi desenvolvida especialmente para esse tipo de pele.",
                "tags": ["pele", "oleosa", "produto", "recomendação"],
                "category": "recomendação"
            },
            {
                "question": "Como faço para rastrear meu pedido?",
                "answer": "Para rastrear seu pedido, acesse a seção 'Meus Pedidos' em sua conta no site ou use o código de rastreamento enviado por email na página dos Correios ou transportadora responsável pela entrega.",
                "tags": ["rastreio", "pedido", "entrega", "status"],
                "category": "logística"
            },
            {
                "question": "Vocês testam produtos em animais?",
                "answer": "Não, não testamos nossos produtos em animais. Somos uma empresa cruelty-free certificada e comprometida com práticas éticas e sustentáveis em toda nossa cadeia produtiva.",
                "tags": ["cruelty-free", "animais", "testes", "ética"],
                "category": "institucional"
            },
            {
                "question": "Como posso me tornar um revendedor?",
                "answer": "Para se tornar um revendedor, preencha o formulário disponível em nosso site na seção 'Seja um Revendedor'. Nossa equipe analisará seu cadastro e entrará em contato em até 5 dias úteis com mais informações.",
                "tags": ["revenda", "revendedor", "cadastro", "parceria"],
                "category": "comercial"
            },
            {
                "question": "Quais formas de pagamento vocês aceitam?",
                "answer": "Aceitamos cartões de crédito (parcelamento em até 6x sem juros), cartões de débito, boleto bancário, PIX e transferência bancária. Para compras acima de R$300, oferecemos parcelamento em até 10x sem juros.",
                "tags": ["pagamento", "cartão", "boleto", "pix", "parcelamento"],
                "category": "financeiro"
            },
            {
                "question": "Os produtos têm garantia?",
                "answer": "Sim, todos os nossos produtos têm garantia de 30 dias contra defeitos de fabricação. Caso identifique algum problema, entre em contato com nosso suporte com fotos do produto e descrição do defeito.",
                "tags": ["garantia", "defeito", "qualidade", "troca"],
                "category": "pós-venda"
            }
        ]
    
    def _calculate_similarity(self, query: str, reference: str) -> float:
        """
        Calcula a similaridade entre duas strings (versão simplificada).
        
        Em uma implementação real, usaria embeddings e comparação vetorial
        ou algoritmos mais sofisticados como BM25.
        
        Args:
            query: Texto da consulta
            reference: Texto de referência
            
        Returns:
            Pontuação de similaridade entre 0 e 1
        """
        # Normalizar textos
        query = query.lower()
        reference = reference.lower()
        
        # Extrair palavras
        query_words = set(re.findall(r'\w+', query))
        reference_words = set(re.findall(r'\w+', reference))
        
        if not query_words or not reference_words:
            return 0.0
        
        # Calcular interseção de palavras
        common_words = query_words.intersection(reference_words)
        
        # Calcular coeficiente de Jaccard
        similarity = len(common_words) / (len(query_words) + len(reference_words) - len(common_words))
        
        return similarity
    
    def search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca na base de conhecimento por itens relevantes para a consulta.
        
        Args:
            query: Texto da consulta
            
        Returns:
            Lista de itens relevantes com pontuação de similaridade
        """
        results = []
        
        for item in self.knowledge_base:
            # Calcular similaridade com a pergunta
            question_similarity = self._calculate_similarity(query, item["question"])
            
            # Calcular similaridade com as tags
            tags_text = " ".join(item.get("tags", []))
            tags_similarity = self._calculate_similarity(query, tags_text) * 0.8  # Peso menor para tags
            
            # Usar a maior similaridade encontrada
            similarity = max(question_similarity, tags_similarity)
            
            if similarity >= self.min_similarity_score:
                results.append({
                    "item": item,
                    "similarity": similarity
                })
        
        # Ordenar por similaridade (maior primeiro)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Limitar número de resultados
        return results[:self.max_results]
    
    def get_faq_response(self, query: str) -> Tuple[Optional[str], float]:
        """
        Obtém uma resposta da base de conhecimento para a consulta.
        
        Args:
            query: Texto da consulta
            
        Returns:
            Tupla com a resposta encontrada e a pontuação de similaridade,
            ou (None, 0.0) se nenhuma resposta relevante for encontrada
        """
        results = self.search_knowledge_base(query)
        
        if not results:
            return None, 0.0
            
        # Retornar o melhor resultado
        best_match = results[0]
        return best_match["item"]["answer"], best_match["similarity"]
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem, buscando respostas na base de conhecimento.
        
        Args:
            message: Texto da mensagem
            context: Contexto da conversa
            
        Returns:
            Contexto atualizado com informações da base de conhecimento
        """
        if not message:
            return context
            
        # Buscar resposta na base de conhecimento
        faq_response, similarity = self.get_faq_response(message)
        
        # Atualizar contexto
        updated_context = context.copy()
        updated_context["faq_match"] = {
            "found": faq_response is not None,
            "response": faq_response,
            "similarity": similarity
        }
        
        if faq_response:
            logger.info(f"FAQ encontrado para a consulta com similaridade {similarity:.2f}")
        
        return updated_context
    
    def get_response(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Obtém uma resposta da base de conhecimento com base no contexto.
        
        Args:
            context: Contexto da conversa
            
        Returns:
            Resposta da base de conhecimento ou None se não houver match
        """
        faq_match = context.get("faq_match", {})
        
        if faq_match.get("found", False) and faq_match.get("similarity", 0) >= self.min_similarity_score:
            return faq_match.get("response")
            
        return None
