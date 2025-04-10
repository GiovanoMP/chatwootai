#!/usr/bin/env python3
"""
Monitor de Mapeamento de Clientes

Este script monitora os logs do sistema para verificar se o mapeamento de clientes
está funcionando corretamente, sem modificar nenhum arquivo importante.

Uso:
    python client_mapping_monitor.py [caminho_do_log]

Se nenhum caminho for fornecido, o script usará o arquivo de log padrão.
"""

import os
import sys
import re
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ClientMappingMonitor")

# Cores para o terminal
COLORS = {
    'reset': '\033[0m',
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'bold': '\033[1m',
    'underline': '\033[4m'
}

class ClientMappingMonitor:
    """
    Monitor para verificar o mapeamento de clientes nos logs do sistema.
    """
    
    def __init__(self, log_path: Optional[str] = None):
        """
        Inicializa o monitor.
        
        Args:
            log_path: Caminho para o arquivo de log. Se None, usa o padrão.
        """
        # Define o caminho do log
        self.log_path = log_path or "/home/giovano/Projetos/Chatwoot V4/logs/webhook.log"
        
        # Verifica se o arquivo existe
        if not os.path.exists(self.log_path):
            logger.error(f"Arquivo de log não encontrado: {self.log_path}")
            raise FileNotFoundError(f"Arquivo de log não encontrado: {self.log_path}")
            
        logger.info(f"Monitorando arquivo de log: {self.log_path}")
        
        # Posição atual no arquivo
        self.current_position = os.path.getsize(self.log_path)
        
        # Estatísticas
        self.stats = {
            "total_messages": 0,
            "identified_clients": 0,
            "unidentified_clients": 0,
            "account_ids": {},
            "client_ids": {}
        }
        
        # Padrões para identificar informações nos logs
        self.patterns = {
            'account_id': re.compile(r'account_id["\s:]+(\d+)'),
            'inbox_id': re.compile(r'inbox_id["\s:]+(\d+)'),
            'client_id': re.compile(r'client_id["\s:]+([^",\s]+)'),
            'domain': re.compile(r'domain["\s:]+([^",\s]+)'),
            'webhook': re.compile(r'Webhook recebido'),
            'client_mapper': re.compile(r'ClientMapper'),
            'error': re.compile(r'(?i)(error|exception|fail|traceback)'),
        }
        
        # Flag para controle de execução
        self.running = True
    
    def start(self):
        """
        Inicia o monitoramento.
        """
        logger.info("Iniciando monitoramento de mapeamento de clientes...")
        print(f"{COLORS['bold']}{COLORS['green']}Monitor de Mapeamento de Clientes iniciado{COLORS['reset']}")
        print(f"Monitorando: {COLORS['cyan']}{self.log_path}{COLORS['reset']}")
        print(f"Pressione {COLORS['bold']}Ctrl+C{COLORS['reset']} para encerrar\n")
        
        try:
            while self.running:
                self._check_new_logs()
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{COLORS['yellow']}Monitoramento interrompido pelo usuário{COLORS['reset']}")
        finally:
            self._print_summary()
    
    def _check_new_logs(self):
        """
        Verifica se há novas entradas no log.
        """
        # Obtém o tamanho atual do arquivo
        current_size = os.path.getsize(self.log_path)
        
        # Se o arquivo foi truncado, reinicia a posição
        if current_size < self.current_position:
            logger.warning("Arquivo de log truncado, reiniciando posição")
            self.current_position = 0
        
        # Se há novas entradas, processa-as
        if current_size > self.current_position:
            with open(self.log_path, 'r') as f:
                f.seek(self.current_position)
                new_lines = f.readlines()
                
                for line in new_lines:
                    self._process_log_line(line)
                
                # Atualiza a posição
                self.current_position = current_size
    
    def _process_log_line(self, line: str):
        """
        Processa uma linha de log.
        
        Args:
            line: Linha de log
        """
        # Verifica se é uma linha de webhook
        if self.patterns['webhook'].search(line):
            self.stats["total_messages"] += 1
            
            # Extrai account_id e inbox_id
            account_id_match = self.patterns['account_id'].search(line)
            inbox_id_match = self.patterns['inbox_id'].search(line)
            
            if account_id_match:
                account_id = account_id_match.group(1)
                
                # Registra o account_id nas estatísticas
                if account_id not in self.stats["account_ids"]:
                    self.stats["account_ids"][account_id] = 0
                self.stats["account_ids"][account_id] += 1
                
                print(f"{COLORS['blue']}Webhook com account_id: {account_id}{COLORS['reset']}")
            
            # Verifica se há informações de cliente
            client_id_match = self.patterns['client_id'].search(line)
            domain_match = self.patterns['domain'].search(line)
            
            if client_id_match:
                client_id = client_id_match.group(1)
                domain = domain_match.group(1) if domain_match else "desconhecido"
                
                # Registra o client_id nas estatísticas
                if client_id not in self.stats["client_ids"]:
                    self.stats["client_ids"][client_id] = 0
                self.stats["client_ids"][client_id] += 1
                
                self.stats["identified_clients"] += 1
                print(f"{COLORS['green']}Cliente identificado: {client_id} (Domínio: {domain}){COLORS['reset']}")
            elif account_id_match:
                self.stats["unidentified_clients"] += 1
                print(f"{COLORS['yellow']}Cliente não identificado para account_id: {account_id}{COLORS['reset']}")
        
        # Verifica se há erros
        if self.patterns['error'].search(line):
            print(f"{COLORS['red']}ERRO: {line.strip()}{COLORS['reset']}")
        
        # Verifica se há menções ao ClientMapper
        if self.patterns['client_mapper'].search(line):
            print(f"{COLORS['magenta']}ClientMapper: {line.strip()}{COLORS['reset']}")
    
    def _print_summary(self):
        """
        Imprime um resumo das estatísticas.
        """
        print(f"\n{COLORS['bold']}Resumo do Monitoramento:{COLORS['reset']}")
        print(f"Total de mensagens: {self.stats['total_messages']}")
        print(f"Clientes identificados: {self.stats['identified_clients']}")
        print(f"Clientes não identificados: {self.stats['unidentified_clients']}")
        
        if self.stats["account_ids"]:
            print(f"\n{COLORS['bold']}Account IDs encontrados:{COLORS['reset']}")
            for account_id, count in self.stats["account_ids"].items():
                print(f"  - Account ID {account_id}: {count} ocorrências")
        
        if self.stats["client_ids"]:
            print(f"\n{COLORS['bold']}Client IDs encontrados:{COLORS['reset']}")
            for client_id, count in self.stats["client_ids"].items():
                print(f"  - Client ID {client_id}: {count} ocorrências")

def main():
    """
    Função principal.
    """
    parser = argparse.ArgumentParser(description='Monitor de Mapeamento de Clientes')
    parser.add_argument('log_path', nargs='?', help='Caminho para o arquivo de log')
    args = parser.parse_args()
    
    try:
        monitor = ClientMappingMonitor(args.log_path)
        monitor.start()
    except Exception as e:
        logger.error(f"Erro ao iniciar o monitor: {e}")
        print(f"{COLORS['red']}Erro ao iniciar o monitor: {e}{COLORS['reset']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
