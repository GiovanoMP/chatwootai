# -*- coding: utf-8 -*-

"""
Gerenciador de mapeamento de canais.
Este módulo contém funções para gerenciar o mapeamento de canais do Chatwoot.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class MappingManager:
    """
    Gerenciador de mapeamento de canais.
    """
    
    def __init__(self, base_dir: str = None):
        """
        Inicializa o gerenciador de mapeamento.
        
        Args:
            base_dir: Diretório base para os arquivos de mapeamento
        """
        self.base_dir = base_dir or os.path.join(os.getcwd(), "config")
        self.yaml_path = os.path.join(self.base_dir, "chatwoot_mapping.yaml")
        self.json_path = os.path.join(self.base_dir, "chatwoot_mapping.json")
        
        # Garantir que o diretório existe
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Inicializar estrutura de dados
        self.mapping_data = {
            "accounts": {},
            "inboxes": {},
            "fallbacks": [],
            "special_numbers": []
        }
        
        # Carregar dados existentes
        self._load_mapping()
    
    def _load_mapping(self) -> None:
        """
        Carrega o mapeamento existente.
        """
        # Tentar carregar do JSON primeiro (formato preferido)
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data:
                        self.mapping_data = data
                        logger.info(f"Mapeamento carregado do JSON: {self.json_path}")
                        return
            except Exception as e:
                logger.warning(f"Erro ao carregar mapeamento do JSON: {str(e)}")
        
        # Se não conseguir carregar do JSON, tentar do YAML
        if os.path.exists(self.yaml_path):
            try:
                with open(self.yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data:
                        self.mapping_data = data
                        logger.info(f"Mapeamento carregado do YAML: {self.yaml_path}")
                        # Salvar em JSON para uso futuro
                        self._save_json()
                        return
            except Exception as e:
                logger.warning(f"Erro ao carregar mapeamento do YAML: {str(e)}")
        
        # Se não conseguir carregar de nenhum formato, usar o padrão
        logger.info("Usando mapeamento padrão")
    
    def _save_json(self) -> bool:
        """
        Salva o mapeamento em formato JSON.
        
        Returns:
            True se o salvamento foi bem-sucedido, False caso contrário
        """
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.mapping_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Mapeamento salvo em JSON: {self.json_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar mapeamento em JSON: {str(e)}")
            return False
    
    def _save_yaml(self) -> bool:
        """
        Salva o mapeamento em formato YAML.
        
        Returns:
            True se o salvamento foi bem-sucedido, False caso contrário
        """
        try:
            with open(self.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.mapping_data, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Mapeamento salvo em YAML: {self.yaml_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar mapeamento em YAML: {str(e)}")
            return False
    
    def save(self) -> bool:
        """
        Salva o mapeamento em ambos os formatos.
        
        Returns:
            True se pelo menos um formato foi salvo com sucesso, False caso contrário
        """
        json_success = self._save_json()
        yaml_success = self._save_yaml()
        return json_success or yaml_success
    
    def update_account_mapping(self, chatwoot_account_id: str, internal_account_id: str, domain: str) -> None:
        """
        Atualiza o mapeamento de uma conta.
        
        Args:
            chatwoot_account_id: ID da conta no Chatwoot
            internal_account_id: ID interno da conta
            domain: Domínio da conta
        """
        self.mapping_data["accounts"][str(chatwoot_account_id)] = {
            "account_id": internal_account_id,
            "domain": domain
        }
    
    def update_inbox_mapping(self, chatwoot_inbox_id: str, internal_account_id: str, domain: str) -> None:
        """
        Atualiza o mapeamento de uma caixa de entrada.
        
        Args:
            chatwoot_inbox_id: ID da caixa de entrada no Chatwoot
            internal_account_id: ID interno da conta
            domain: Domínio da conta
        """
        self.mapping_data["inboxes"][str(chatwoot_inbox_id)] = {
            "account_id": internal_account_id,
            "domain": domain
        }
    
    def update_fallback(self, internal_account_id: str, domain: str, is_fallback: bool, sequence: int = 10) -> None:
        """
        Atualiza o fallback de uma conta.
        
        Args:
            internal_account_id: ID interno da conta
            domain: Domínio da conta
            is_fallback: Se a conta é um fallback
            sequence: Sequência do fallback
        """
        # Remover fallback existente para este account_id (se houver)
        self.mapping_data["fallbacks"] = [f for f in self.mapping_data["fallbacks"]
                                        if f.get("account_id") != internal_account_id]
        
        # Adicionar novo fallback se necessário
        if is_fallback:
            self.mapping_data["fallbacks"].append({
                "domain": domain,
                "account_id": internal_account_id,
                "sequence": sequence
            })
            
            # Ordenar fallbacks por sequência
            self.mapping_data["fallbacks"].sort(key=lambda x: x.get("sequence", 10))
    
    def update_special_numbers(self, internal_account_id: str, domain: str, 
                              special_numbers: List[Dict[str, Any]]) -> None:
        """
        Atualiza os números especiais de uma conta.
        
        Args:
            internal_account_id: ID interno da conta
            domain: Domínio da conta
            special_numbers: Lista de números especiais
        """
        # Remover números existentes para este account_id
        self.mapping_data["special_numbers"] = [n for n in self.mapping_data["special_numbers"]
                                              if n.get("account_id") != internal_account_id]
        
        # Adicionar novos números especiais
        for number_data in special_numbers:
            number = number_data.get("number")
            crew = number_data.get("crew", "analytics")
            
            if number:
                self.mapping_data["special_numbers"].append({
                    "number": number,
                    "crew": crew,
                    "domain": domain,
                    "account_id": internal_account_id
                })
    
    def get_account_domain(self, chatwoot_account_id: str) -> Optional[str]:
        """
        Obtém o domínio de uma conta.
        
        Args:
            chatwoot_account_id: ID da conta no Chatwoot
            
        Returns:
            Domínio da conta ou None se não encontrado
        """
        account_info = self.mapping_data["accounts"].get(str(chatwoot_account_id))
        if account_info and isinstance(account_info, dict):
            return account_info.get("domain")
        return None
    
    def get_inbox_mapping(self, chatwoot_inbox_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém o mapeamento de uma caixa de entrada.
        
        Args:
            chatwoot_inbox_id: ID da caixa de entrada no Chatwoot
            
        Returns:
            Mapeamento da caixa de entrada ou None se não encontrado
        """
        return self.mapping_data["inboxes"].get(str(chatwoot_inbox_id))
    
    def get_fallbacks(self) -> List[Dict[str, Any]]:
        """
        Obtém a lista de fallbacks.
        
        Returns:
            Lista de fallbacks
        """
        return self.mapping_data["fallbacks"]
    
    def get_special_numbers(self) -> List[Dict[str, Any]]:
        """
        Obtém a lista de números especiais.
        
        Returns:
            Lista de números especiais
        """
        return self.mapping_data["special_numbers"]
    
    def get_all_mapping(self) -> Dict[str, Any]:
        """
        Obtém todo o mapeamento.
        
        Returns:
            Mapeamento completo
        """
        return self.mapping_data

# Instância global para uso em todo o sistema
mapping_manager = MappingManager()
