#!/usr/bin/env python3
"""
Script para capturar e analisar eventos do Chatwoot.

Este script:
1. Captura todos os eventos recebidos pelo webhook
2. Salva a estrutura completa dos eventos em um arquivo JSON
3. Gera estatísticas sobre os tipos de eventos
4. Ajuda a identificar padrões e problemas

Uso:
    python event_capture.py [--output DIRETÓRIO] [--days DIAS]
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import re
from collections import Counter, defaultdict

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("event_capture")

def parse_arguments():
    """
    Analisa os argumentos da linha de comando.
    
    Returns:
        argparse.Namespace: Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Captura e analisa eventos do Chatwoot")
    parser.add_argument(
        "--output", 
        default="logs/events",
        help="Diretório para salvar os eventos capturados"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=7,
        help="Número de dias para manter os eventos (0 = manter todos)"
    )
    parser.add_argument(
        "--webhook-log", 
        default="logs/webhook.log",
        help="Arquivo de log do webhook"
    )
    return parser.parse_args()

def ensure_directory(directory):
    """
    Garante que o diretório existe, criando-o se necessário.
    
    Args:
        directory (str): Caminho do diretório
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path

def extract_event_from_log(log_line):
    """
    Extrai informações de evento de uma linha de log.
    
    Args:
        log_line (str): Linha de log
        
    Returns:
        dict or None: Informações do evento ou None se não for um evento
    """
    # Padrões para identificar eventos nos logs
    webhook_pattern = r'Webhook recebido: (\{.*\})'
    processing_pattern = r'Processando webhook: (\{.*\})'
    
    # Tentar extrair o evento usando os padrões
    for pattern in [webhook_pattern, processing_pattern]:
        match = re.search(pattern, log_line)
        if match:
            try:
                event_data = json.loads(match.group(1))
                return event_data
            except json.JSONDecodeError:
                logger.warning(f"Falha ao decodificar JSON do evento: {match.group(1)[:100]}...")
    
    return None

def process_webhook_log(log_file, output_dir, max_age_days=7):
    """
    Processa o arquivo de log do webhook e extrai eventos.
    
    Args:
        log_file (str): Caminho do arquivo de log
        output_dir (Path): Diretório para salvar os eventos
        max_age_days (int): Número máximo de dias para manter os eventos
    
    Returns:
        tuple: (total_events, event_types, event_structures)
    """
    if not os.path.exists(log_file):
        logger.error(f"Arquivo de log não encontrado: {log_file}")
        return 0, Counter(), defaultdict(list)
    
    # Estatísticas
    total_events = 0
    event_types = Counter()
    event_structures = defaultdict(list)
    
    # Data de corte para eventos antigos
    cutoff_date = datetime.now() - timedelta(days=max_age_days) if max_age_days > 0 else None
    
    with open(log_file, 'r') as f:
        for line in f:
            event_data = extract_event_from_log(line)
            if event_data:
                # Extrair timestamp e tipo de evento
                timestamp = event_data.get('timestamp', datetime.now().isoformat())
                event_type = event_data.get('event', 'unknown')
                
                # Verificar se o evento é recente o suficiente
                event_date = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
                if cutoff_date and event_date < cutoff_date:
                    continue
                
                # Incrementar estatísticas
                total_events += 1
                event_types[event_type] += 1
                
                # Analisar estrutura do evento
                structure = analyze_event_structure(event_data)
                if structure not in event_structures[event_type]:
                    event_structures[event_type].append(structure)
                
                # Salvar evento em arquivo
                save_event(event_data, output_dir)
    
    return total_events, event_types, event_structures

def analyze_event_structure(event_data):
    """
    Analisa a estrutura de um evento.
    
    Args:
        event_data (dict): Dados do evento
        
    Returns:
        dict: Estrutura do evento (chaves e tipos de valores)
    """
    structure = {}
    
    def get_type_info(value):
        if value is None:
            return "null"
        elif isinstance(value, dict):
            return {k: get_type_info(v) for k, v in value.items()}
        elif isinstance(value, list):
            return f"array[{len(value)}]"
        else:
            return type(value).__name__
    
    for key, value in event_data.items():
        structure[key] = get_type_info(value)
    
    return structure

def save_event(event_data, output_dir):
    """
    Salva um evento em um arquivo JSON.
    
    Args:
        event_data (dict): Dados do evento
        output_dir (Path): Diretório para salvar o evento
    """
    # Gerar nome de arquivo baseado no tipo de evento e timestamp
    event_type = event_data.get('event', 'unknown')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    event_id = event_data.get('id', timestamp)
    
    # Criar diretório para o tipo de evento
    event_type_dir = output_dir / event_type
    event_type_dir.mkdir(exist_ok=True)
    
    # Salvar evento em arquivo JSON
    file_path = event_type_dir / f"{event_id}_{timestamp}.json"
    with open(file_path, 'w') as f:
        json.dump(event_data, f, indent=2)

def generate_report(total_events, event_types, event_structures, output_dir):
    """
    Gera um relatório de análise de eventos.
    
    Args:
        total_events (int): Total de eventos processados
        event_types (Counter): Contagem de tipos de eventos
        event_structures (dict): Estruturas de eventos por tipo
        output_dir (Path): Diretório para salvar o relatório
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_events": total_events,
        "event_types": dict(event_types),
        "event_structures": {k: v for k, v in event_structures.items()}
    }
    
    # Salvar relatório em arquivo JSON
    report_path = output_dir / "report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Exibir resumo no console
    logger.info(f"Total de eventos processados: {total_events}")
    logger.info("Tipos de eventos:")
    for event_type, count in event_types.most_common():
        logger.info(f"  - {event_type}: {count}")
    
    logger.info(f"Relatório salvo em: {report_path}")

def main():
    """
    Função principal.
    """
    args = parse_arguments()
    
    # Garantir que o diretório de saída existe
    output_dir = ensure_directory(args.output)
    
    logger.info(f"Iniciando captura de eventos do Chatwoot...")
    logger.info(f"Arquivo de log: {args.webhook_log}")
    logger.info(f"Diretório de saída: {output_dir}")
    
    # Processar arquivo de log
    total_events, event_types, event_structures = process_webhook_log(
        args.webhook_log, 
        output_dir, 
        args.days
    )
    
    # Gerar relatório
    generate_report(total_events, event_types, event_structures, output_dir)
    
    logger.info("Captura de eventos concluída.")

if __name__ == "__main__":
    main()
