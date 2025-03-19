"""
Utilitários para processamento de texto.
Este módulo contém funções para preparar textos para geração de embeddings.
"""
from typing import Dict, Any, List, Optional
import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    Normaliza um texto removendo caracteres especiais e normalizando espaços.
    
    Args:
        text: Texto a ser normalizado.
        
    Returns:
        Texto normalizado.
    """
    if not text:
        return ""
        
    # Normalizar acentos e caracteres especiais
    text = unicodedata.normalize('NFKD', text)
    
    # Remover caracteres especiais e números
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Normalizar espaços
    text = re.sub(r'\s+', ' ', text)
    
    # Converter para minúsculas
    text = text.lower().strip()
    
    return text

def prepare_product_text(product: Dict[str, Any]) -> str:
    """
    Prepara o texto de um produto para geração de embedding.
    
    Esta função combina os campos relevantes do produto em um único texto
    que será usado para gerar o embedding.
    
    Args:
        product: Dicionário com os dados do produto.
        
    Returns:
        Texto preparado para geração de embedding.
    """
    # Campos a serem incluídos no texto (em ordem de importância)
    fields = [
        ('name', 'Nome: '),
        ('description', 'Descrição: '),
        ('benefits', 'Benefícios: '),
        ('ingredients', 'Ingredientes: '),
        ('usage', 'Modo de uso: '),
        ('detailed_information', 'Informações detalhadas: ')
    ]
    
    # Combinar campos em um único texto
    text_parts = []
    for field, prefix in fields:
        if field in product and product[field]:
            value = str(product[field]).strip()
            if value:
                text_parts.append(f"{prefix}{value}")
    
    # Adicionar categoria se disponível
    if 'category_id' in product and product['category_id']:
        text_parts.append(f"Categoria ID: {product['category_id']}")
    
    # Combinar todas as partes
    combined_text = " ".join(text_parts)
    
    # Normalizar o texto final
    return normalize_text(combined_text)

def prepare_business_rule_text(rule: Dict[str, Any]) -> str:
    """
    Prepara o texto de uma regra de negócio para geração de embedding.
    
    Esta função combina os campos relevantes da regra em um único texto
    que será usado para gerar o embedding.
    
    Args:
        rule: Dicionário com os dados da regra de negócio.
        
    Returns:
        Texto preparado para geração de embedding.
    """
    # Campos a serem incluídos no texto (em ordem de importância)
    fields = [
        ('name', 'Nome: '),
        ('description', 'Descrição: '),
        ('rule_text', 'Regra: '),
        ('examples', 'Exemplos: '),
        ('exceptions', 'Exceções: ')
    ]
    
    # Combinar campos em um único texto
    text_parts = []
    for field, prefix in fields:
        if field in rule and rule[field]:
            value = str(rule[field]).strip()
            if value:
                text_parts.append(f"{prefix}{value}")
    
    # Adicionar categoria se disponível
    if 'category' in rule and rule['category']:
        text_parts.append(f"Categoria: {rule['category']}")
    
    # Combinar todas as partes
    combined_text = " ".join(text_parts)
    
    # Normalizar o texto final
    return normalize_text(combined_text)

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extrai palavras-chave de um texto.
    
    Esta função é útil para gerar tags ou termos de busca a partir de um texto.
    
    Args:
        text: Texto do qual extrair palavras-chave.
        max_keywords: Número máximo de palavras-chave a retornar.
        
    Returns:
        Lista de palavras-chave extraídas.
    """
    # Lista de stopwords em português
    stopwords = {
        'a', 'ao', 'aos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aquilo', 'as', 'até',
        'com', 'como', 'da', 'das', 'de', 'dela', 'delas', 'dele', 'deles', 'depois',
        'do', 'dos', 'e', 'ela', 'elas', 'ele', 'eles', 'em', 'entre', 'era',
        'eram', 'éramos', 'essa', 'essas', 'esse', 'esses', 'esta', 'estas',
        'este', 'estes', 'eu', 'foi', 'fomos', 'for', 'foram', 'fosse', 'fossem',
        'há', 'isso', 'isto', 'já', 'lhe', 'lhes', 'mais', 'mas', 'me', 'mesmo',
        'meu', 'meus', 'minha', 'minhas', 'muito', 'muitos', 'na', 'não', 'nas',
        'nem', 'no', 'nos', 'nós', 'nossa', 'nossas', 'nosso', 'nossos', 'num',
        'numa', 'o', 'os', 'ou', 'para', 'pela', 'pelas', 'pelo', 'pelos', 'por',
        'qual', 'quando', 'que', 'quem', 'são', 'se', 'seja', 'sejam', 'sem',
        'será', 'seu', 'seus', 'só', 'somos', 'sua', 'suas', 'também', 'te',
        'tem', 'temos', 'tenho', 'ter', 'teu', 'teus', 'tu', 'tua', 'tuas',
        'um', 'uma', 'você', 'vocês', 'vos'
    }
    
    # Normalizar o texto
    normalized_text = normalize_text(text)
    
    # Dividir em palavras
    words = normalized_text.split()
    
    # Remover stopwords e palavras muito curtas
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    
    # Contar frequência das palavras
    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Ordenar por frequência
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Retornar as palavras mais frequentes
    return [word for word, _ in sorted_words[:max_keywords]]
