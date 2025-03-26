#!/usr/bin/env python3
"""
Monitor de Testes de Ponta a Ponta

Este script monitora a execução dos testes de ponta a ponta do ChatwootAI,
exibindo informações em tempo real sobre o fluxo de mensagens e o estado do sistema.

Uso:
    python test_monitor.py [--webhook-log ARQUIVO] [--hub-log ARQUIVO] [--test-log ARQUIVO]
"""

import os
import sys
import time
import argparse
import re
import threading
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from colorama import Fore, Back, Style, init

# Inicializar colorama para formatação de cores no terminal
init(autoreset=True)

# Definir cores para diferentes componentes
COLORS = {
    'webhook': Fore.CYAN,
    'hub': Fore.GREEN,
    'test': Fore.MAGENTA,
    'error': Fore.RED + Style.BRIGHT,
    'warning': Fore.YELLOW,
    'info': Fore.WHITE,
    'debug': Fore.BLUE,
    'message': Fore.MAGENTA + Style.BRIGHT,
    'chatwoot': Fore.YELLOW + Style.BRIGHT,
    'highlight': Back.YELLOW + Fore.BLACK,
    'success': Fore.GREEN + Style.BRIGHT,
    'crew': Fore.BLUE + Style.BRIGHT,
    'agent': Fore.CYAN + Style.BRIGHT,
    'data': Fore.YELLOW,
    'domain': Fore.GREEN + Style.BRIGHT,
}

# Padrões para identificar componentes nos logs
PATTERNS = {
    'webhook': r'webhook|ChatwootWebhookHandler',
    'hub': r'hub|HubCrew|OrchestratorAgent',
    'crew': r'Crew|SalesCrew|SupportCrew|MarketingCrew',
    'agent': r'Agent|DataProxyAgent|ContextManagerAgent',
    'data': r'DataServiceHub|ProductDataService|CustomerDataService',
    'domain': r'DomainManager|domain',
    'client': r'client_id|cliente|ClientMapper',
    'message': r'message|mensagem',
    'error': r'(?i)(error|exception|fail|traceback)',
    'warning': r'(?i)(warning|warn|attention)',
    'account': r'account_id|conta|Chatwoot',
}

class TestMonitor:
    """
    Monitor de testes de ponta a ponta para o ChatwootAI.
    """
    
    def __init__(
        self, 
        webhook_log: str = "logs/webhook.log",
        hub_log: str = "logs/hub.log",
        test_log: str = "logs/end_to_end_test.log",
        output_dir: str = "logs/monitor"
    ):
        """
        Inicializa o monitor de testes.
        
        Args:
            webhook_log: Caminho para o log do webhook
            hub_log: Caminho para o log do hub
            test_log: Caminho para o log do teste
            output_dir: Diretório para salvar os resultados
        """
        self.webhook_log = webhook_log
        self.hub_log = hub_log
        self.test_log = test_log
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado do monitor
        self.running = True
        self.conversation_flow = []
        self.current_test = None
        self.current_message = None
        self.current_domain = None
        self.current_client_id = None
        self.current_client_name = None
        self.current_account_id = None
        self.start_time = datetime.now()
        
        # Posições nos arquivos de log
        self.log_positions = {
            'webhook': 0,
            'hub': 0,
            'test': 0
        }
        
        # Threads de monitoramento
        self.threads = {}
    
    def start(self):
        """
        Inicia o monitoramento dos logs.
        """
        print(f"{Style.BRIGHT}Iniciando monitor de testes de ponta a ponta{Style.RESET_ALL}")
        print(f"Logs monitorados:")
        print(f"  Webhook: {self.webhook_log}")
        print(f"  Hub: {self.hub_log}")
        print(f"  Teste: {self.test_log}")
        print("\n" + "="*80)
        
        # Iniciar threads de monitoramento
        self.threads['webhook'] = threading.Thread(
            target=self._monitor_log,
            args=('webhook', self.webhook_log)
        )
        self.threads['hub'] = threading.Thread(
            target=self._monitor_log,
            args=('hub', self.hub_log)
        )
        self.threads['test'] = threading.Thread(
            target=self._monitor_log,
            args=('test', self.test_log)
        )
        
        # Iniciar threads
        for thread in self.threads.values():
            thread.daemon = True
            thread.start()
        
        # Aguardar interrupção
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(f"\n{Style.BRIGHT}Monitoramento interrompido pelo usuário{Style.RESET_ALL}")
            self.running = False
            
            # Aguardar threads
            for thread in self.threads.values():
                thread.join(timeout=1)
            
            # Gerar relatório final
            self._generate_report()
    
    def _monitor_log(self, log_type: str, log_path: str):
        """
        Monitora um arquivo de log.
        
        Args:
            log_type: Tipo de log (webhook, hub, test)
            log_path: Caminho para o arquivo de log
        """
        if not os.path.exists(log_path):
            print(f"{COLORS['error']}Arquivo de log não encontrado: {log_path}")
            return
        
        # Posicionar no final do arquivo
        with open(log_path, 'r') as f:
            f.seek(0, os.SEEK_END)
            self.log_positions[log_type] = f.tell()
        
        while self.running:
            try:
                with open(log_path, 'r') as f:
                    f.seek(self.log_positions[log_type])
                    for line in f:
                        self._process_log_line(log_type, line.strip())
                    self.log_positions[log_type] = f.tell()
            except Exception as e:
                print(f"{COLORS['error']}Erro ao monitorar log {log_type}: {str(e)}")
            
            time.sleep(0.1)
    
    def _process_log_line(self, log_type: str, line: str):
        """
        Processa uma linha de log.
        
        Args:
            log_type: Tipo de log (webhook, hub, test)
            line: Linha de log
        """
        # Extrair timestamp e nível
        timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - .* - (\w+) - (.*)$', line)
        if timestamp_match:
            timestamp = timestamp_match.group(1)
            level = timestamp_match.group(2)
            message = timestamp_match.group(3)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            level = "INFO"
            message = line
        
        # Determinar cor com base no tipo de log e conteúdo
        color = COLORS.get(log_type, COLORS['info'])
        
        # Verificar padrões específicos
        for pattern_name, pattern in PATTERNS.items():
            if re.search(pattern, line, re.IGNORECASE):
                color = COLORS.get(pattern_name, color)
                break
        
        # Verificar nível de log
        if level.upper() == "ERROR":
            color = COLORS['error']
        elif level.upper() == "WARNING":
            color = COLORS['warning']
        elif level.upper() == "DEBUG":
            color = COLORS['debug']
        
        # Exibir linha formatada
        print(f"{color}[{log_type.upper()}] {timestamp} - {message}")
        
        # Processar informações específicas
        self._extract_test_info(log_type, line)
        
        # Registrar no fluxo de conversa
        self.conversation_flow.append({
            'timestamp': timestamp,
            'log_type': log_type,
            'level': level,
            'message': message,
            'test': self.current_test,
            'current_message': self.current_message,
            'domain': self.current_domain,
            'client_id': self.current_client_id,
            'client_name': self.current_client_name,
            'account_id': self.current_account_id
        })
    
    def _extract_test_info(self, log_type: str, line: str):
        """
        Extrai informações de teste da linha de log.
        
        Args:
            log_type: Tipo de log
            line: Linha de log
        """
        # Extrair informações de teste
        if log_type == 'test':
            # Extrair informações do cliente
            client_match = re.search(r'Cliente: ([^(]+) \(ID: ([^)]+)\)', line)
            if client_match:
                self.current_client_name = client_match.group(1).strip()
                self.current_client_id = client_match.group(2).strip()
                print(f"{COLORS['highlight']}Cliente: {self.current_client_name} (ID: {self.current_client_id})")
            
            # Extrair domínio
            domain_match = re.search(r'Domínio: (\w+)', line)
            if domain_match:
                self.current_domain = domain_match.group(1)
                print(f"{COLORS['highlight']}Domínio de teste: {self.current_domain}")
            
            # Extrair account_id
            account_match = re.search(r'Account ID Chatwoot: (\d+)', line)
            if account_match:
                self.current_account_id = account_match.group(1)
                print(f"{COLORS['highlight']}Account ID Chatwoot: {self.current_account_id}")
            
            # Extrair teste atual
            test_match = re.search(r'Executando teste (\d+)/\d+: (.*)', line)
            if test_match:
                test_number = test_match.group(1)
                test_message = test_match.group(2)
                self.current_test = f"test_{test_number}"
                self.current_message = test_message
                print(f"{COLORS['highlight']}Teste atual: {self.current_test} - Mensagem: {self.current_message}")
            
            # Extrair resultado de teste
            result_match = re.search(r'Teste (test_\w+) (concluído com sucesso|falhou)', line)
            if result_match:
                test_id = result_match.group(1)
                success = "concluído com sucesso" in line
                status = "SUCESSO" if success else "FALHA"
                color = COLORS['success'] if success else COLORS['error']
                print(f"{color}Resultado do teste {test_id}: {status}")
                
        # Extrair informações de cliente do webhook
        elif log_type == 'webhook':
            client_match = re.search(r'Cliente identificado pelo account_id (\d+): (.*)', line)
            if client_match:
                account_id = client_match.group(1)
                client_info = client_match.group(2)
                print(f"{COLORS['client']}Webhook: Cliente identificado para account_id {account_id}: {client_info}")
    
    def _generate_report(self):
        """
        Gera um relatório do monitoramento.
        """
        # Calcular tempo total
        end_time = datetime.now()
        total_time = (end_time - self.start_time).total_seconds()
        
        # Criar relatório
        report = {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_time": total_time,
            "domain": self.current_domain,
            "client_id": self.current_client_id,
            "client_name": self.current_client_name,
            "account_id": self.current_account_id,
            "conversation_flow": self.conversation_flow
        }
        
        # Salvar relatório
        report_path = self.output_dir / f"monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Style.BRIGHT}Relatório de monitoramento gerado: {report_path}")
        print(f"Tempo total de monitoramento: {total_time:.2f}s")


def parse_arguments():
    """
    Analisa os argumentos da linha de comando.
    
    Returns:
        argparse.Namespace: Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Monitor de testes de ponta a ponta para o ChatwootAI")
    parser.add_argument(
        "--webhook-log", 
        default="logs/webhook.log",
        help="Caminho para o log do webhook"
    )
    parser.add_argument(
        "--hub-log", 
        default="logs/hub.log",
        help="Caminho para o log do hub"
    )
    parser.add_argument(
        "--test-log", 
        default="logs/end_to_end_test.log",
        help="Caminho para o log do teste"
    )
    parser.add_argument(
        "--output", 
        default="logs/monitor",
        help="Diretório para salvar os resultados"
    )
    return parser.parse_args()


def main():
    """
    Função principal.
    """
    args = parse_arguments()
    
    # Criar monitor
    monitor = TestMonitor(
        webhook_log=args.webhook_log,
        hub_log=args.hub_log,
        test_log=args.test_log,
        output_dir=args.output
    )
    
    # Iniciar monitoramento
    monitor.start()


if __name__ == "__main__":
    main()
