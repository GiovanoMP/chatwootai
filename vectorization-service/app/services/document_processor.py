"""
Serviço para processamento e chunking de documentos.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from math import ceil

from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Serviço para processamento e chunking de documentos."""
    
    @staticmethod
    def split_into_chunks(
        text: str, 
        chunk_size: int = 800, 
        overlap: int = 150,
        min_chunk_size: int = 100
    ) -> List[str]:
        """
        Divide um texto em chunks com sobreposição.
        
        Args:
            text: Texto a ser dividido
            chunk_size: Tamanho aproximado de cada chunk em caracteres
            overlap: Sobreposição entre chunks em caracteres
            min_chunk_size: Tamanho mínimo para um chunk ser considerado válido
            
        Returns:
            Lista de chunks de texto
        """
        # Remover espaços em branco extras
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Se o texto for menor que o tamanho do chunk, retornar como um único chunk
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Determinar o fim do chunk atual
            end = start + chunk_size
            
            if end >= len(text):
                # Se chegamos ao final do texto
                chunk = text[start:]
                if len(chunk) >= min_chunk_size:
                    chunks.append(chunk)
                break
            
            # Procurar por um bom ponto de quebra (final de frase ou parágrafo)
            # Prioridade: parágrafo > frase > espaço > qualquer caractere
            paragraph_break = text.rfind('\n', start, end)
            sentence_break = text.rfind('. ', start, end)
            space_break = text.rfind(' ', start, end)
            
            if paragraph_break > start + min_chunk_size:
                end = paragraph_break + 1  # Incluir a quebra de parágrafo
            elif sentence_break > start + min_chunk_size:
                end = sentence_break + 2  # Incluir o ponto e o espaço
            elif space_break > start + min_chunk_size:
                end = space_break + 1  # Incluir o espaço
            # Se não encontrar um bom ponto de quebra, usar o tamanho máximo
            
            # Adicionar o chunk atual
            chunk = text[start:end].strip()
            if len(chunk) >= min_chunk_size:
                chunks.append(chunk)
            
            # Avançar para o próximo chunk com sobreposição
            start = end - overlap
        
        return chunks
    
    @staticmethod
    def extract_metadata(
        document: Dict[str, Any],
        chunk_index: int = 0,
        total_chunks: int = 1
    ) -> Dict[str, Any]:
        """
        Extrai metadados de um documento.
        
        Args:
            document: Documento original
            chunk_index: Índice do chunk atual
            total_chunks: Total de chunks do documento
            
        Returns:
            Dicionário com metadados
        """
        return {
            "id": document.get("id"),
            "name": document.get("name"),
            "document_type": document.get("document_type"),
            "account_id": document.get("account_id"),
            "business_rule_id": document.get("business_rule_id"),
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "is_chunk": total_chunks > 1,
            "last_updated": document.get("last_updated")
        }
    
    @staticmethod
    def format_chunk_for_embedding(
        chunk: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Formata um chunk para embedding, adicionando contexto.
        
        Args:
            chunk: Texto do chunk
            metadata: Metadados do documento
            
        Returns:
            Texto formatado para embedding
        """
        chunk_context = ""
        if metadata.get("is_chunk"):
            chunk_context = f"[Parte {metadata['chunk_index'] + 1} de {metadata['total_chunks']}] "
        
        return f"""
        Documento: {metadata['name']}
        Tipo: {metadata['document_type']}
        {chunk_context}
        
        Conteúdo:
        {chunk}
        """
    
    @staticmethod
    def process_document(
        document: Dict[str, Any],
        account_id: str,
        business_rule_id: int,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Processa um documento, dividindo em chunks se necessário.
        
        Args:
            document: Documento a ser processado
            account_id: ID da conta
            business_rule_id: ID da regra de negócio
            chunk_size: Tamanho do chunk (opcional)
            overlap: Sobreposição entre chunks (opcional)
            
        Returns:
            Lista de documentos processados com metadados
        """
        if chunk_size is None:
            chunk_size = settings.DOCUMENT_CHUNK_SIZE
        
        if overlap is None:
            overlap = settings.DOCUMENT_CHUNK_OVERLAP
        
        # Adicionar informações da conta ao documento
        document["account_id"] = account_id
        document["business_rule_id"] = business_rule_id
        
        content = document.get("content", "")
        
        # Se o conteúdo for pequeno, não dividir em chunks
        if len(content) <= chunk_size:
            metadata = DocumentProcessor.extract_metadata(document)
            formatted_text = DocumentProcessor.format_chunk_for_embedding(content, metadata)
            
            return [{
                "original": document,
                "metadata": metadata,
                "content": content,
                "formatted_text": formatted_text
            }]
        
        # Dividir em chunks
        chunks = DocumentProcessor.split_into_chunks(
            content, 
            chunk_size=chunk_size, 
            overlap=overlap
        )
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            metadata = DocumentProcessor.extract_metadata(
                document,
                chunk_index=i,
                total_chunks=len(chunks)
            )
            
            formatted_text = DocumentProcessor.format_chunk_for_embedding(chunk, metadata)
            
            processed_chunks.append({
                "original": document,
                "metadata": metadata,
                "content": chunk,
                "formatted_text": formatted_text
            })
        
        return processed_chunks
