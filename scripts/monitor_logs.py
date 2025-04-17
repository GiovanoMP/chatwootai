#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para monitorar os logs do servidor unificado.

Este script monitora os logs do servidor unificado, exibindo
mensagens coloridas e formatadas para facilitar a análise.
"""

import os
import sys
import time
import argparse
import re
from datetime import datetime
from pathlib import Path
import threading
import queue

# Cores ANSI
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    @staticmethod
    def colorize(text, color):
        return f"{color}{text}{Colors.RESET}"

# Configurações
LOG_DIR = "logs"
SERVER_LOG = "server.log"
WEBHOOK_LOG = "webhook.log"
HUB_LOG = "hub.log"
ODOO_API_LOG = "odoo_api.log"

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Monitor logs for the unified server")
    parser.add_argument("--server-log", default=os.path.join(LOG_DIR, SERVER_LOG),
                        help=f"Path to server log file (default: {os.path.join(LOG_DIR, SERVER_LOG)})")
    parser.add_argument("--webhook-log", default=os.path.join(LOG_DIR, WEBHOOK_LOG),
                        help=f"Path to webhook log file (default: {os.path.join(LOG_DIR, WEBHOOK_LOG)})")
    parser.add_argument("--hub-log", default=os.path.join(LOG_DIR, HUB_LOG),
                        help=f"Path to hub log file (default: {os.path.join(LOG_DIR, HUB_LOG)})")
    parser.add_argument("--odoo-api-log", default=os.path.join(LOG_DIR, ODOO_API_LOG),
                        help=f"Path to Odoo API log file (default: {os.path.join(LOG_DIR, ODOO_API_LOG)})")
    parser.add_argument("--all", action="store_true",
                        help="Monitor all log files")
    parser.add_argument("--filter", type=str, default="",
                        help="Filter log messages containing this string")
    parser.add_argument("--level", type=str, default="",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", ""],
                        help="Filter log messages by level")
    return parser.parse_args()

def format_log_line(line, source):
    """Format a log line with colors and source indicator."""
    # Define colors for different sources
    source_colors = {
        "server": Colors.BLUE,
        "webhook": Colors.GREEN,
        "hub": Colors.MAGENTA,
        "odoo_api": Colors.CYAN
    }
    
    # Define colors for different log levels
    level_colors = {
        "DEBUG": Colors.WHITE,
        "INFO": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.RED + Colors.BOLD
    }
    
    # Parse log line
    timestamp_match = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - ([A-Z]+) - (.+)$", line)
    if timestamp_match:
        timestamp, logger, level, message = timestamp_match.groups()
        
        # Format timestamp
        timestamp = Colors.colorize(timestamp, Colors.BOLD)
        
        # Format logger
        logger = Colors.colorize(logger.strip(), Colors.CYAN)
        
        # Format level
        level_color = level_colors.get(level, Colors.WHITE)
        level = Colors.colorize(level, level_color)
        
        # Format source
        source_color = source_colors.get(source, Colors.WHITE)
        source_tag = Colors.colorize(f"[{source.upper()}]", source_color)
        
        # Format message
        # Highlight JSON objects
        message = re.sub(r'({[^}]*})', lambda m: Colors.colorize(m.group(1), Colors.YELLOW), message)
        
        # Highlight URLs
        message = re.sub(r'(https?://[^\s]+)', lambda m: Colors.colorize(m.group(1), Colors.UNDERLINE + Colors.BLUE), message)
        
        # Highlight IDs
        message = re.sub(r'(ID: [^\s,]+)', lambda m: Colors.colorize(m.group(1), Colors.BOLD + Colors.GREEN), message)
        
        # Return formatted line
        return f"{source_tag} {timestamp} - {logger} - {level} - {message}"
    else:
        # If line doesn't match expected format, just add source tag
        source_color = source_colors.get(source, Colors.WHITE)
        source_tag = Colors.colorize(f"[{source.upper()}]", source_color)
        return f"{source_tag} {line}"

def monitor_log_file(file_path, source, message_queue, filter_text="", level_filter=""):
    """Monitor a log file and send new lines to the message queue."""
    if not os.path.exists(file_path):
        print(f"⚠️  Log file not found: {file_path}")
        # Create empty file
        with open(file_path, 'w') as f:
            pass
        print(f"✅ Created empty log file: {file_path}")
    
    # Open file and seek to the end
    with open(file_path, 'r') as f:
        f.seek(0, os.SEEK_END)
        
        while True:
            line = f.readline()
            if line:
                line = line.rstrip()
                
                # Apply filters
                if filter_text and filter_text.lower() not in line.lower():
                    continue
                
                if level_filter:
                    level_match = re.search(r" - ([A-Z]+) - ", line)
                    if not level_match or level_match.group(1) != level_filter:
                        continue
                
                # Send to queue
                message_queue.put((source, line))
            else:
                time.sleep(0.1)

def main():
    """Main function."""
    args = parse_args()
    
    print("\n" + "="*70)
    print("🔍 MONITOR DE LOGS DO SERVIDOR UNIFICADO")
    print("="*70)
    
    # Create message queue
    message_queue = queue.Queue()
    
    # Start monitoring threads
    threads = []
    
    if args.all or args.server_log:
        server_thread = threading.Thread(
            target=monitor_log_file,
            args=(args.server_log, "server", message_queue, args.filter, args.level),
            daemon=True
        )
        server_thread.start()
        threads.append(server_thread)
        print(f"✅ Monitorando log do servidor: {args.server_log}")
    
    if args.all or args.webhook_log:
        webhook_thread = threading.Thread(
            target=monitor_log_file,
            args=(args.webhook_log, "webhook", message_queue, args.filter, args.level),
            daemon=True
        )
        webhook_thread.start()
        threads.append(webhook_thread)
        print(f"✅ Monitorando log do webhook: {args.webhook_log}")
    
    if args.all or args.hub_log:
        hub_thread = threading.Thread(
            target=monitor_log_file,
            args=(args.hub_log, "hub", message_queue, args.filter, args.level),
            daemon=True
        )
        hub_thread.start()
        threads.append(hub_thread)
        print(f"✅ Monitorando log do hub: {args.hub_log}")
    
    if args.all or args.odoo_api_log:
        odoo_api_thread = threading.Thread(
            target=monitor_log_file,
            args=(args.odoo_api_log, "odoo_api", message_queue, args.filter, args.level),
            daemon=True
        )
        odoo_api_thread.start()
        threads.append(odoo_api_thread)
        print(f"✅ Monitorando log da API Odoo: {args.odoo_api_log}")
    
    if not threads:
        print("❌ Nenhum arquivo de log selecionado para monitoramento")
        return
    
    # Print filters if any
    if args.filter:
        print(f"🔍 Filtrando mensagens contendo: {args.filter}")
    
    if args.level:
        print(f"🔍 Filtrando mensagens de nível: {args.level}")
    
    print("\n" + "="*70)
    print("📊 LOGS EM TEMPO REAL (Ctrl+C para sair)")
    print("="*70 + "\n")
    
    try:
        # Process messages from queue
        while True:
            source, line = message_queue.get()
            formatted_line = format_log_line(line, source)
            print(formatted_line)
    except KeyboardInterrupt:
        print("\n" + "="*70)
        print("👋 MONITOR DE LOGS ENCERRADO")
        print("="*70)

if __name__ == "__main__":
    main()
