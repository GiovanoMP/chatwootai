#!/usr/bin/env python3
"""
Script para monitorar logs do webhook e do hub.py

Este script:
1. Monitora os logs do servidor webhook
2. Monitora os logs do hub.py
3. Destaca mensagens importantes
4. Exibe o fluxo completo de processamento de mensagens

Uso:
    python monitor_webhook_logs.py [--webhook-log ARQUIVO] [--hub-log ARQUIVO]
"""

import os
import sys
import time
import argparse
import re
import threading
from datetime import datetime
from pathlib import Path
from colorama import Fore, Back, Style, init

# Inicializar colorama para formatação de cores no terminal
init(autoreset=True)

# Definir cores para diferentes tipos de logs
COLORS = {
    'webhook': Fore.CYAN,
    'hub': Fore.GREEN,
    'error': Fore.RED + Style.BRIGHT,
    'warning': Fore.YELLOW,
    'info': Fore.WHITE,
    'debug': Fore.BLUE,
    'message': Fore.MAGENTA + Style.BRIGHT,
    'chatwoot': Fore.YELLOW + Style.BRIGHT,
    'highlight': Back.YELLOW + Fore.BLACK,
    'success': Fore.GREEN + Style.BRIGHT,
}

# Padrões para identificar tipos de mensagens nos logs
PATTERNS = {
    'error': r'(?i)(error|exception|fail|traceback)',
    'warning': r'(?i)(warning|warn|attention)',
    'message_received': r'(?i)(message received|received message|new message)',
    'message_sent': r'(?i)(message sent|sending message|response sent)',
    'chatwoot': r'(?i)(chatwoot|webhook)',
    'hub': r'(?i)(hub|hubcrew|orchestrator)',
    'processing': r'(?i)(processing|processed|handling)',
}

def parse_arguments():
    """Analisa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description='Monitora logs do webhook e do hub.py')
    parser.add_argument('--webhook-log', type=str, default='webhook.log',
                        help='Caminho para o arquivo de log do webhook')
    parser.add_argument('--hub-log', type=str, default='hub.log',
                        help='Caminho para o arquivo de log do hub.py')
    parser.add_argument('--highlight', type=str, default='',
                        help='Termos para destacar nos logs (separados por vírgula)')
    parser.add_argument('--filter', type=str, default='',
                        help='Filtrar logs que contenham estes termos (separados por vírgula)')
    parser.add_argument('--level', type=str, default='info',
                        choices=['debug', 'info', 'warning', 'error'],
                        help='Nível mínimo de log para exibir')
    
    return parser.parse_args()

def get_log_level_priority(level):
    """Retorna a prioridade numérica de um nível de log."""
    priorities = {
        'debug': 0,
        'info': 1,
        'warning': 2,
        'error': 3
    }
    return priorities.get(level.lower(), 1)  # default para 'info'

def should_display_log(line, args):
    """Verifica se uma linha de log deve ser exibida com base nos filtros."""
    # Verificar nível de log
    level_match = re.search(r'(?i)(DEBUG|INFO|WARNING|ERROR)', line)
    if level_match:
        line_level = level_match.group(1).lower()
        if get_log_level_priority(line_level) < get_log_level_priority(args.level):
            return False
    
    # Aplicar filtros positivos (se especificados)
    if args.filter:
        filters = [f.strip() for f in args.filter.split(',')]
        if not any(f in line for f in filters if f):
            return False
    
    return True

def colorize_line(line, source, args):
    """Aplica cores a uma linha de log com base em seu conteúdo."""
    # Colorir com base na fonte (webhook ou hub)
    colored_line = COLORS[source] + line
    
    # Aplicar cores com base no conteúdo
    if re.search(PATTERNS['error'], line):
        colored_line = COLORS['error'] + line
    elif re.search(PATTERNS['warning'], line):
        colored_line = COLORS['warning'] + line
    elif re.search(PATTERNS['message_received'], line):
        colored_line = COLORS['message'] + line
    elif re.search(PATTERNS['message_sent'], line):
        colored_line = COLORS['success'] + line
    
    # Destacar termos específicos
    if args.highlight:
        highlights = [h.strip() for h in args.highlight.split(',')]
        for highlight in highlights:
            if highlight and highlight in line:
                # Substituir o termo destacado por sua versão colorida
                colored_line = colored_line.replace(
                    highlight, 
                    COLORS['highlight'] + highlight + Style.RESET_ALL + COLORS[source]
                )
    
    return colored_line

def monitor_log_file(file_path, source, args, callback=None):
    """Monitora um arquivo de log e exibe novas linhas."""
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            print(f"{COLORS['warning']}Arquivo de log não encontrado: {file_path}")
            print(f"{COLORS['info']}Aguardando criação do arquivo...")
            
            # Aguardar a criação do arquivo
            while not os.path.exists(file_path):
                time.sleep(1)
        
        # Abrir o arquivo e ir para o final
        with open(file_path, 'r') as file:
            file.seek(0, 2)  # Ir para o final do arquivo
            
            print(f"{COLORS[source]}Monitorando {source}: {file_path}")
            
            while True:
                line = file.readline()
                if line:
                    if should_display_log(line, args):
                        colored_line = colorize_line(line.rstrip(), source, args)
                        print(colored_line)
                        
                        # Chamar callback se fornecido
                        if callback:
                            callback(line, source)
                else:
                    time.sleep(0.1)  # Pequena pausa para não sobrecarregar a CPU
    except KeyboardInterrupt:
        print(f"\n{COLORS['info']}Monitoramento de {source} interrompido.")
    except Exception as e:
        print(f"{COLORS['error']}Erro ao monitorar {source}: {str(e)}")

def detect_message_flow(line, source):
    """Detecta e exibe o fluxo de processamento de mensagens."""
    # Detectar ID de mensagem ou conversa
    message_id_match = re.search(r'message[_\s]id[:\s]+(\d+)', line, re.IGNORECASE)
    conversation_id_match = re.search(r'conversation[_\s]id[:\s]+(\d+)', line, re.IGNORECASE)
    
    message_id = message_id_match.group(1) if message_id_match else None
    conversation_id = conversation_id_match.group(1) if conversation_id_match else None
    
    if message_id or conversation_id:
        id_type = "mensagem" if message_id else "conversa"
        id_value = message_id or conversation_id
        
        # Determinar a etapa do fluxo
        if source == 'webhook' and re.search(PATTERNS['message_received'], line):
            print(f"{COLORS['highlight']} FLUXO: {id_type.upper()} {id_value} recebida pelo webhook {Style.RESET_ALL}")
        elif source == 'hub' and re.search(PATTERNS['processing'], line):
            print(f"{COLORS['highlight']} FLUXO: {id_type.upper()} {id_value} sendo processada pelo HubCrew {Style.RESET_ALL}")
        elif source == 'hub' and re.search(PATTERNS['message_sent'], line):
            print(f"{COLORS['highlight']} FLUXO: {id_type.upper()} {id_value} resposta enviada ao Chatwoot {Style.RESET_ALL}")

def display_header():
    """Exibe o cabeçalho do monitor de logs."""
    print("\n" + "="*80)
    print(f"{Fore.CYAN + Style.BRIGHT}MONITOR DE LOGS DO WEBHOOK E HUB{Style.RESET_ALL}")
    print("="*80)
    print(f"{Fore.YELLOW}Pressione Ctrl+C para encerrar o monitoramento{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Logs do webhook: {Fore.CYAN}texto nesta cor{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Logs do hub: {Fore.GREEN}texto nesta cor{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Mensagens recebidas: {Fore.MAGENTA + Style.BRIGHT}texto nesta cor{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Respostas enviadas: {Fore.GREEN + Style.BRIGHT}texto nesta cor{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Erros: {Fore.RED + Style.BRIGHT}texto nesta cor{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Avisos: {Fore.YELLOW}texto nesta cor{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Termos destacados: {Back.YELLOW + Fore.BLACK}texto nesta cor{Style.RESET_ALL}")
    print("="*80 + "\n")

def main():
    """Função principal."""
    args = parse_arguments()
    
    # Exibir cabeçalho
    display_header()
    
    try:
        # Iniciar threads para monitorar os arquivos de log
        webhook_thread = threading.Thread(
            target=monitor_log_file,
            args=(args.webhook_log, 'webhook', args, detect_message_flow),
            daemon=True
        )
        
        hub_thread = threading.Thread(
            target=monitor_log_file,
            args=(args.hub_log, 'hub', args, detect_message_flow),
            daemon=True
        )
        
        webhook_thread.start()
        hub_thread.start()
        
        # Aguardar as threads terminarem (o que só acontecerá com Ctrl+C)
        webhook_thread.join()
        hub_thread.join()
    except KeyboardInterrupt:
        print(f"\n{COLORS['info']}Monitoramento interrompido pelo usuário.")
    except Exception as e:
        print(f"{COLORS['error']}Erro inesperado: {str(e)}")
    finally:
        print(f"\n{COLORS['info']}Monitor de logs encerrado.")

if __name__ == "__main__":
    main()
