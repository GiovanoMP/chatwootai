"""
Plugin para enriquecimento de respostas.

Este plugin adiciona informações complementares às respostas,
como sugestões de produtos relacionados, dicas de uso e promoções.
"""
import logging
import random
from typing import Dict, List, Any, Optional

from src.plugins.base.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class ResponseEnhancerPlugin(BasePlugin):
    """
    Plugin para enriquecimento de respostas.
    
    Adiciona informações complementares às respostas do sistema,
    como sugestões de produtos relacionados, dicas de uso e promoções ativas.
    """
    
    def initialize(self):
        """
        Inicializa o plugin carregando recursos necessários.
        """
        logger.info("Inicializando plugin de enriquecimento de respostas")
        
        # Carregar templates de enriquecimento da configuração ou usar padrões
        self.templates = self.config.get("templates", {
            "product_suggestion": [
                "🔍 Você também pode gostar de: {product}",
                "✨ Sugestão: Experimente também {product}",
                "👉 Complemento perfeito: {product}"
            ],
            "usage_tip": [
                "💡 Dica: {tip}",
                "🌟 Sabia que? {tip}",
                "📝 Recomendação: {tip}"
            ],
            "promotion": [
                "🎁 OFERTA: {promotion}",
                "💰 PROMOÇÃO: {promotion}",
                "🔥 APROVEITE: {promotion}"
            ]
        })
        
        # Carregar dicas de uso da configuração ou usar padrões
        self.usage_tips = self.config.get("usage_tips", {
            "cosmetics": [
                "Produtos com ácido hialurônico são ideais para hidratação profunda",
                "Aplique protetor solar mesmo em dias nublados",
                "Limpe o rosto antes de dormir para evitar acne",
                "Esfoliantes devem ser usados no máximo 2x por semana"
            ],
            "health": [
                "Beba pelo menos 2 litros de água por dia",
                "Exercícios físicos regulares melhoram a circulação",
                "Alimentos ricos em ômega 3 ajudam na saúde da pele",
                "Consulte um dermatologista anualmente para check-up"
            ],
            "retail": [
                "Produtos naturais têm menor risco de alergias",
                "Verifique a data de validade antes de usar",
                "Guarde seus produtos em local fresco e seco",
                "Produtos em gel são ideais para peles oleosas"
            ]
        })
        
        # Carregar promoções ativas da configuração ou usar padrões
        self.active_promotions = self.config.get("active_promotions", [
            "15% OFF em compras acima de R$150",
            "Leve 3, pague 2 em toda linha facial",
            "Frete grátis para compras acima de R$100",
            "Ganhe um brinde exclusivo nas compras online"
        ])
        
        # Configurações
        self.enhancement_probability = self.config.get("enhancement_probability", 0.7)
        self.max_enhancements = self.config.get("max_enhancements", 2)
        
        logger.info(f"Plugin de enriquecimento inicializado com {len(self.templates)} tipos de templates")
    
    def get_product_suggestions(self, context: Dict[str, Any], product_type: str = None) -> List[str]:
        """
        Obtém sugestões de produtos relacionados.
        
        Args:
            context: Contexto da conversa
            product_type: Tipo de produto para sugestões
            
        Returns:
            Lista de sugestões de produtos
        """
        # Em uma implementação real, isso consultaria o DataProxyAgent
        # para obter produtos relacionados do catálogo
        
        # Simulação de sugestões por categoria
        suggestions = {
            "creme": ["Creme Hidratante Noturno", "Sérum Facial Vitamina C", "Máscara Facial Hidratante"],
            "protetor": ["Protetor Solar Facial FPS 60", "Protetor Labial FPS 30", "Protetor Solar Corporal FPS 50"],
            "maquiagem": ["Base Líquida Matte", "Corretivo Facial", "Pó Compacto Translúcido"],
            "cabelo": ["Shampoo Reparador", "Condicionador Hidratante", "Máscara Capilar Nutritiva"],
            "perfume": ["Eau de Parfum Floral", "Body Splash Frutal", "Perfume Amadeirado"]
        }
        
        if product_type and product_type.lower() in suggestions:
            return suggestions[product_type.lower()]
        
        # Se não houver tipo específico, retorna sugestões aleatórias
        all_suggestions = []
        for products in suggestions.values():
            all_suggestions.extend(products)
            
        return random.sample(all_suggestions, min(3, len(all_suggestions)))
    
    def get_usage_tip(self, domain: str = None) -> str:
        """
        Obtém uma dica de uso aleatória.
        
        Args:
            domain: Domínio para dicas específicas
            
        Returns:
            Dica de uso
        """
        if domain and domain in self.usage_tips:
            tips = self.usage_tips[domain]
        else:
            # Combinar todas as dicas se não houver domínio específico
            tips = []
            for domain_tips in self.usage_tips.values():
                tips.extend(domain_tips)
                
        return random.choice(tips) if tips else "Consulte um especialista para dicas personalizadas"
    
    def get_active_promotion(self) -> str:
        """
        Obtém uma promoção ativa aleatória.
        
        Returns:
            Descrição da promoção
        """
        return random.choice(self.active_promotions) if self.active_promotions else "Sem promoções ativas no momento"
    
    def format_enhancement(self, enhancement_type: str, value: str) -> str:
        """
        Formata um enriquecimento usando um template aleatório.
        
        Args:
            enhancement_type: Tipo de enriquecimento (product_suggestion, usage_tip, promotion)
            value: Valor a ser inserido no template
            
        Returns:
            Texto formatado do enriquecimento
        """
        templates = self.templates.get(enhancement_type, ["{value}"])
        template = random.choice(templates)
        
        if enhancement_type == "product_suggestion":
            return template.format(product=value)
        elif enhancement_type == "usage_tip":
            return template.format(tip=value)
        elif enhancement_type == "promotion":
            return template.format(promotion=value)
        else:
            return value
    
    def enhance_response(self, response: str, context: Dict[str, Any]) -> str:
        """
        Enriquece uma resposta com informações adicionais.
        
        Args:
            response: Resposta original
            context: Contexto da conversa
            
        Returns:
            Resposta enriquecida
        """
        if not response or random.random() > self.enhancement_probability:
            return response
            
        # Determinar domínio ativo
        domain = context.get("domain", {}).get("name", "cosmetics")
        
        # Determinar tipo de produto mencionado (simulação simples)
        product_type = None
        for keyword in ["creme", "protetor", "maquiagem", "cabelo", "perfume"]:
            if keyword in response.lower() or keyword in context.get("last_message", "").lower():
                product_type = keyword
                break
        
        # Selecionar tipos de enriquecimento a aplicar
        enhancement_types = ["product_suggestion", "usage_tip", "promotion"]
        selected_types = random.sample(
            enhancement_types, 
            min(self.max_enhancements, len(enhancement_types))
        )
        
        enhancements = []
        
        for enhancement_type in selected_types:
            if enhancement_type == "product_suggestion" and product_type:
                suggestions = self.get_product_suggestions(context, product_type)
                if suggestions:
                    enhancement = self.format_enhancement(
                        enhancement_type, 
                        random.choice(suggestions)
                    )
                    enhancements.append(enhancement)
                    
            elif enhancement_type == "usage_tip":
                tip = self.get_usage_tip(domain)
                enhancement = self.format_enhancement(enhancement_type, tip)
                enhancements.append(enhancement)
                
            elif enhancement_type == "promotion":
                promotion = self.get_active_promotion()
                enhancement = self.format_enhancement(enhancement_type, promotion)
                enhancements.append(enhancement)
        
        # Adicionar enriquecimentos à resposta
        enhanced_response = response
        
        if enhancements:
            enhanced_response += "\n\n" + "\n".join(enhancements)
            
        return enhanced_response
    
    def process_response(self, response: str, context: Dict[str, Any]) -> str:
        """
        Processa uma resposta, enriquecendo-a com informações adicionais.
        
        Args:
            response: Resposta original
            context: Contexto da conversa
            
        Returns:
            Resposta enriquecida
        """
        return self.enhance_response(response, context)
    
    def process_message(self, message: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Processa uma mensagem recebida. Este método é implementado para compatibilidade
        com a interface de plugins, mas este plugin específico atua apenas em respostas,
        não em mensagens recebidas.
        
        Args:
            message: Mensagem a ser processada
            context: Contexto da conversa (opcional)
            
        Returns:
            Contexto atualizado ou a própria mensagem
        """
        # Se não houver contexto, inicializa um dicionário vazio
        if context is None:
            context = {}
            
        # Este plugin não modifica mensagens recebidas, apenas respostas
        # Retorna o contexto sem alterações
        return context
