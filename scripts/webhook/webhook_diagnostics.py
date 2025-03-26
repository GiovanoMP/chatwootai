#!/usr/bin/env python3
"""
Script para diagnóstico avançado de webhooks do Chatwoot.

Este script:
1. Analisa os logs do webhook em tempo real
2. Identifica padrões de eventos e problemas
3. Gera estatísticas sobre os tipos de eventos
4. Fornece recomendações para otimização

Uso:
    python webhook_diagnostics.py [--webhook-log ARQUIVO] [--output DIRETÓRIO]
"""

import os
import sys
import json
import argparse
import logging
import time
import re
import threading
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict
from colorama import Fore, Back, Style, init

# Inicializar colorama para formatação de cores no terminal
init(autoreset=True)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("webhook_diagnostics")

# Definir cores para diferentes tipos de logs
COLORS = {
    'error': Fore.RED + Style.BRIGHT,
    'warning': Fore.YELLOW,
    'info': Fore.WHITE,
    'debug': Fore.BLUE,
    'message_created': Fore.GREEN,
    'conversation_created': Fore.CYAN,
    'conversation_updated': Fore.MAGENTA,
    'contact_created': Fore.YELLOW,
    'unknown': Fore.RED,
    'success': Fore.GREEN + Style.BRIGHT,
}

class WebhookDiagnostics:
    """Classe para diagnóstico de webhooks do Chatwoot."""
    
    def __init__(self, webhook_log, output_dir):
        """
        Inicializa o diagnóstico de webhooks.
        
        Args:
            webhook_log (str): Caminho para o arquivo de log do webhook
            output_dir (str): Diretório para salvar os resultados
        """
        self.webhook_log = webhook_log
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Estatísticas
        self.stats = {
            "total_events": 0,
            "events_by_type": Counter(),
            "events_without_type": 0,
            "errors": Counter(),
            "warnings": Counter(),
            "processing_times": defaultdict(list),
            "event_patterns": defaultdict(int),
        }
        
        # Padrões para análise de logs
        self.patterns = {
            'webhook_received': r'Webhook recebido: (\{.*\})',
            'processing_webhook': r'Processando webhook: (\{.*\})',
            'event_type': r'Tipo de evento: (\w+)',
            'error': r'(?i)(error|exception|fail|traceback)',
            'warning': r'(?i)(warning|warn|attention)',
            'ignored': r'Ignorando mensagem não-recebida \(tipo: (.*?)\)',
            'processing_time': r'Tempo de processamento: (\d+\.\d+)s',
        }
        
        # Mapeamento de eventos
        self.event_mapping = {
            'message_created': 'Mensagem criada',
            'conversation_created': 'Conversa criada',
            'conversation_updated': 'Conversa atualizada',
            'conversation_status_changed': 'Status da conversa alterado',
            'contact_created': 'Contato criado',
            'contact_updated': 'Contato atualizado',
            'message_updated': 'Mensagem atualizada',
            'webwidget_triggered': 'Widget web acionado',
        }
        
        # Eventos sem tipo
        self.typeless_events = []
        
        # Flag para controle de execução
        self.running = True
    
    def parse_log_line(self, line):
        """
        Analisa uma linha de log e extrai informações relevantes.
        
        Args:
            line (str): Linha de log
            
        Returns:
            dict: Informações extraídas da linha
        """
        result = {
            'timestamp': None,
            'level': None,
            'message': None,
            'event_type': None,
            'event_data': None,
            'error': None,
            'warning': None,
            'ignored': None,
            'processing_time': None,
        }
        
        # Extrair timestamp e nível de log
        timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - .* - (\w+) - (.*)$', line)
        if timestamp_match:
            result['timestamp'] = timestamp_match.group(1)
            result['level'] = timestamp_match.group(2)
            result['message'] = timestamp_match.group(3)
        
        # Extrair dados do webhook
        for pattern_name, pattern in self.patterns.items():
            match = re.search(pattern, line)
            if match:
                if pattern_name in ['webhook_received', 'processing_webhook']:
                    try:
                        result['event_data'] = json.loads(match.group(1))
                        result['event_type'] = result['event_data'].get('event')
                    except json.JSONDecodeError:
                        pass
                elif pattern_name == 'event_type':
                    result['event_type'] = match.group(1)
                elif pattern_name == 'error':
                    result['error'] = match.group(0)
                elif pattern_name == 'warning':
                    result['warning'] = match.group(0)
                elif pattern_name == 'ignored':
                    result['ignored'] = match.group(1)
                elif pattern_name == 'processing_time':
                    result['processing_time'] = float(match.group(1))
        
        return result
    
    def update_stats(self, parsed_line):
        """
        Atualiza as estatísticas com base na linha analisada.
        
        Args:
            parsed_line (dict): Linha analisada
        """
        # Atualizar estatísticas de eventos
        if parsed_line['event_data']:
            self.stats['total_events'] += 1
            
            event_type = parsed_line['event_type'] or 'unknown'
            self.stats['events_by_type'][event_type] += 1
            
            # Registrar eventos sem tipo
            if not parsed_line['event_type'] and parsed_line['event_data']:
                self.stats['events_without_type'] += 1
                self.typeless_events.append(parsed_line['event_data'])
        
        # Atualizar estatísticas de erros e avisos
        if parsed_line['error']:
            self.stats['errors'][parsed_line['error']] += 1
        
        if parsed_line['warning']:
            self.stats['warnings'][parsed_line['warning']] += 1
        
        # Atualizar estatísticas de tempo de processamento
        if parsed_line['processing_time']:
            event_type = parsed_line['event_type'] or 'unknown'
            self.stats['processing_times'][event_type].append(parsed_line['processing_time'])
        
        # Atualizar estatísticas de mensagens ignoradas
        if parsed_line['ignored']:
            self.stats['event_patterns'][f"ignored:{parsed_line['ignored']}"] += 1
    
    def analyze_logs(self):
        """
        Analisa os logs do webhook e gera estatísticas.
        """
        logger.info(f"Analisando logs do webhook: {self.webhook_log}")
        
        if not os.path.exists(self.webhook_log):
            logger.error(f"Arquivo de log não encontrado: {self.webhook_log}")
            return
        
        with open(self.webhook_log, 'r') as f:
            for line in f:
                parsed_line = self.parse_log_line(line)
                self.update_stats(parsed_line)
        
        logger.info(f"Análise concluída. {self.stats['total_events']} eventos processados.")
    
    def monitor_logs(self):
        """
        Monitora os logs do webhook em tempo real.
        """
        logger.info(f"Iniciando monitoramento de logs: {self.webhook_log}")
        
        if not os.path.exists(self.webhook_log):
            logger.error(f"Arquivo de log não encontrado: {self.webhook_log}")
            return
        
        # Posicionar no final do arquivo
        with open(self.webhook_log, 'r') as f:
            f.seek(0, os.SEEK_END)
            position = f.tell()
        
        while self.running:
            with open(self.webhook_log, 'r') as f:
                f.seek(position)
                for line in f:
                    parsed_line = self.parse_log_line(line)
                    self.update_stats(parsed_line)
                    self.display_log_line(line, parsed_line)
                position = f.tell()
            
            time.sleep(0.1)
    
    def display_log_line(self, line, parsed_line):
        """
        Exibe uma linha de log formatada.
        
        Args:
            line (str): Linha de log original
            parsed_line (dict): Linha analisada
        """
        # Determinar a cor com base no tipo de evento ou nível de log
        color = COLORS.get('info')
        
        if parsed_line['event_type']:
            color = COLORS.get(parsed_line['event_type'], COLORS.get('info'))
        elif parsed_line['level']:
            level = parsed_line['level'].lower()
            color = COLORS.get(level, COLORS.get('info'))
        
        if parsed_line['error']:
            color = COLORS.get('error')
        elif parsed_line['warning']:
            color = COLORS.get('warning')
        
        # Exibir linha formatada
        print(f"{color}{line.strip()}")
    
    def generate_report(self):
        """
        Gera um relatório com as estatísticas coletadas.
        """
        logger.info("Gerando relatório de diagnóstico...")
        
        # Calcular estatísticas adicionais
        avg_processing_times = {}
        for event_type, times in self.stats['processing_times'].items():
            if times:
                avg_processing_times[event_type] = sum(times) / len(times)
        
        # Criar relatório
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_events": self.stats['total_events'],
            "events_by_type": dict(self.stats['events_by_type']),
            "events_without_type": self.stats['events_without_type'],
            "errors": dict(self.stats['errors']),
            "warnings": dict(self.stats['warnings']),
            "avg_processing_times": avg_processing_times,
            "event_patterns": dict(self.stats['event_patterns']),
            "typeless_events_sample": self.typeless_events[:10],  # Amostra de até 10 eventos sem tipo
        }
        
        # Salvar relatório em arquivo JSON
        report_path = self.output_dir / "webhook_diagnostics_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Relatório salvo em: {report_path}")
        
        # Exibir resumo no console
        self.display_report_summary(report)
        
        return report
    
    def display_report_summary(self, report):
        """
        Exibe um resumo do relatório no console.
        
        Args:
            report (dict): Relatório gerado
        """
        print("\n" + "="*80)
        print(f"{Style.BRIGHT}RELATÓRIO DE DIAGNÓSTICO DE WEBHOOKS{Style.RESET_ALL}")
        print("="*80)
        
        print(f"\n{Style.BRIGHT}Estatísticas Gerais:{Style.RESET_ALL}")
        print(f"  Total de eventos: {report['total_events']}")
        print(f"  Eventos sem tipo: {report['events_without_type']}")
        
        print(f"\n{Style.BRIGHT}Eventos por Tipo:{Style.RESET_ALL}")
        for event_type, count in sorted(report['events_by_type'].items(), key=lambda x: x[1], reverse=True):
            event_name = self.event_mapping.get(event_type, event_type)
            color = COLORS.get(event_type, COLORS.get('info'))
            print(f"  {color}{event_name}: {count}")
        
        if report['errors']:
            print(f"\n{Style.BRIGHT}{Fore.RED}Erros Encontrados:{Style.RESET_ALL}")
            for error, count in report['errors'].items():
                print(f"  {Fore.RED}{error}: {count}")
        
        if report['warnings']:
            print(f"\n{Style.BRIGHT}{Fore.YELLOW}Avisos Encontrados:{Style.RESET_ALL}")
            for warning, count in report['warnings'].items():
                print(f"  {Fore.YELLOW}{warning}: {count}")
        
        if report['avg_processing_times']:
            print(f"\n{Style.BRIGHT}Tempo Médio de Processamento:{Style.RESET_ALL}")
            for event_type, avg_time in sorted(report['avg_processing_times'].items(), key=lambda x: x[1], reverse=True):
                event_name = self.event_mapping.get(event_type, event_type)
                print(f"  {event_name}: {avg_time:.4f}s")
        
        print(f"\n{Style.BRIGHT}Padrões de Eventos:{Style.RESET_ALL}")
        for pattern, count in sorted(report['event_patterns'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {pattern}: {count}")
        
        if report['typeless_events_sample']:
            print(f"\n{Style.BRIGHT}{Fore.YELLOW}Amostra de Eventos Sem Tipo:{Style.RESET_ALL}")
            for i, event in enumerate(report['typeless_events_sample']):
                print(f"  {i+1}. Chaves: {list(event.keys())}")
        
        print("\n" + "="*80)
        print(f"{Style.BRIGHT}RECOMENDAÇÕES:{Style.RESET_ALL}")
        
        # Gerar recomendações com base nas estatísticas
        if report['events_without_type'] > 0:
            print(f"{Fore.YELLOW}1. Há {report['events_without_type']} eventos sem tipo definido.")
            print("   Recomendação: Implemente tratamento específico para eventos sem tipo.")
            print("   Verifique a estrutura desses eventos para identificar padrões.")
        
        if 'unknown' in report['events_by_type'] and report['events_by_type']['unknown'] > 0:
            print(f"{Fore.YELLOW}2. Há {report['events_by_type']['unknown']} eventos de tipo desconhecido.")
            print("   Recomendação: Verifique a configuração do webhook no Chatwoot.")
        
        if report['errors']:
            print(f"{Fore.RED}3. Foram encontrados erros nos logs.")
            print("   Recomendação: Corrija os erros identificados para melhorar a estabilidade.")
        
        print(f"{Fore.GREEN}4. Configure o Chatwoot para enviar apenas os eventos necessários:")
        for event_type in self.event_mapping.keys():
            if event_type in report['events_by_type'] and report['events_by_type'][event_type] > 0:
                print(f"   - {self.event_mapping[event_type]}: {report['events_by_type'].get(event_type, 0)} eventos")
        
        print("\n" + "="*80)
    
    def generate_recommendations(self):
        """
        Gera recomendações com base nas estatísticas coletadas.
        
        Returns:
            list: Lista de recomendações
        """
        recommendations = []
        
        # Analisar eventos sem tipo
        if self.stats['events_without_type'] > 0:
            recommendations.append({
                "type": "warning",
                "message": f"Há {self.stats['events_without_type']} eventos sem tipo definido.",
                "recommendation": "Implemente tratamento específico para eventos sem tipo.",
                "details": "Verifique a estrutura desses eventos para identificar padrões."
            })
        
        # Analisar erros
        if self.stats['errors']:
            recommendations.append({
                "type": "error",
                "message": "Foram encontrados erros nos logs.",
                "recommendation": "Corrija os erros identificados para melhorar a estabilidade.",
                "details": dict(self.stats['errors'])
            })
        
        # Analisar avisos
        if self.stats['warnings']:
            recommendations.append({
                "type": "warning",
                "message": "Foram encontrados avisos nos logs.",
                "recommendation": "Verifique os avisos para identificar possíveis problemas.",
                "details": dict(self.stats['warnings'])
            })
        
        # Analisar tempos de processamento
        slow_events = []
        for event_type, times in self.stats['processing_times'].items():
            if times and sum(times) / len(times) > 1.0:  # Mais de 1 segundo
                slow_events.append({
                    "event_type": event_type,
                    "avg_time": sum(times) / len(times)
                })
        
        if slow_events:
            recommendations.append({
                "type": "performance",
                "message": "Alguns eventos estão demorando para serem processados.",
                "recommendation": "Otimize o processamento desses eventos.",
                "details": slow_events
            })
        
        # Recomendar configuração do Chatwoot
        active_events = []
        for event_type in self.event_mapping.keys():
            if event_type in self.stats['events_by_type'] and self.stats['events_by_type'][event_type] > 0:
                active_events.append({
                    "event_type": event_type,
                    "count": self.stats['events_by_type'][event_type],
                    "name": self.event_mapping[event_type]
                })
        
        if active_events:
            recommendations.append({
                "type": "configuration",
                "message": "Configure o Chatwoot para enviar apenas os eventos necessários.",
                "recommendation": "Revise a configuração do webhook no Chatwoot.",
                "details": active_events
            })
        
        return recommendations
    
    def start_monitoring(self):
        """
        Inicia o monitoramento de logs em tempo real.
        """
        # Iniciar thread de monitoramento
        monitor_thread = threading.Thread(target=self.monitor_logs)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        try:
            while True:
                # Atualizar estatísticas a cada 5 segundos
                time.sleep(5)
                self.generate_report()
        except KeyboardInterrupt:
            logger.info("Monitoramento interrompido pelo usuário.")
            self.running = False
            monitor_thread.join()
            self.generate_report()

def parse_arguments():
    """
    Analisa os argumentos da linha de comando.
    
    Returns:
        argparse.Namespace: Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Diagnóstico avançado de webhooks do Chatwoot")
    parser.add_argument(
        "--webhook-log", 
        default="logs/webhook.log",
        help="Arquivo de log do webhook"
    )
    parser.add_argument(
        "--output", 
        default="logs/diagnostics",
        help="Diretório para salvar os resultados"
    )
    parser.add_argument(
        "--mode",
        choices=["analyze", "monitor"],
        default="analyze",
        help="Modo de operação: 'analyze' para análise única, 'monitor' para monitoramento contínuo"
    )
    return parser.parse_args()

def main():
    """
    Função principal.
    """
    args = parse_arguments()
    
    # Criar instância de diagnóstico
    diagnostics = WebhookDiagnostics(args.webhook_log, args.output)
    
    if args.mode == "analyze":
        # Modo de análise única
        diagnostics.analyze_logs()
        diagnostics.generate_report()
    else:
        # Modo de monitoramento contínuo
        try:
            diagnostics.start_monitoring()
        except KeyboardInterrupt:
            logger.info("Diagnóstico interrompido pelo usuário.")
    
    logger.info("Diagnóstico concluído.")

if __name__ == "__main__":
    main()
