#!/usr/bin/env python3
"""
Script para executar o teste end-to-end e monitorar os resultados.

Este script executa o teste end-to-end e monitora os logs para verificar
se o mapeamento de clientes está funcionando corretamente, sem modificar
nenhum arquivo importante do sistema.

Uso:
    python run_e2e_test.py
"""

import os
import sys
import subprocess
import time
import argparse
import logging
from datetime import datetime
import threading

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importa o monitor de testes
from tests.integration.test_monitor import TestMonitor

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("E2ETestRunner")

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

class E2ETestRunner:
    """
    Executor de testes end-to-end com monitoramento.
    """
    
    def __init__(self, test_script_path=None, log_path=None):
        """
        Inicializa o executor de testes.
        
        Args:
            test_script_path: Caminho para o script de teste
            log_path: Caminho para o arquivo de log
        """
        # Define os caminhos
        self.test_script_path = test_script_path or os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../tests/integration/end_to_end_test.py')
        )
        self.log_path = log_path or os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../logs/chatwootai.log')
        )
        
        # Verifica se os arquivos existem
        if not os.path.exists(self.test_script_path):
            raise FileNotFoundError(f"Script de teste não encontrado: {self.test_script_path}")
        
        # Cria o diretório de logs se não existir
        log_dir = os.path.dirname(self.log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        logger.info(f"Script de teste: {self.test_script_path}")
        logger.info(f"Arquivo de log: {self.log_path}")
        
        # Inicializa o monitor de testes
        self.test_monitor = TestMonitor()
        
        # Processo do teste
        self.test_process = None
        
        # Flag para controle de execução
        self.running = True
    
    def start(self):
        """
        Inicia o teste e o monitoramento.
        """
        logger.info("Iniciando teste end-to-end com monitoramento...")
        print(f"{COLORS['bold']}{COLORS['green']}Teste End-to-End com Monitoramento iniciado{COLORS['reset']}")
        print(f"Script de teste: {COLORS['cyan']}{self.test_script_path}{COLORS['reset']}")
        print(f"Arquivo de log: {COLORS['cyan']}{self.log_path}{COLORS['reset']}")
        print(f"Pressione {COLORS['bold']}Ctrl+C{COLORS['reset']} para encerrar\n")
        
        try:
            # Inicia o monitor em uma thread separada
            monitor_thread = threading.Thread(target=self._run_monitor)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Executa o teste
            self._run_test()
            
            # Aguarda o término do monitor
            while self.running and monitor_thread.is_alive():
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n{COLORS['yellow']}Teste interrompido pelo usuário{COLORS['reset']}")
        finally:
            self.running = False
            self._cleanup()
    
    def _run_test(self):
        """
        Executa o script de teste.
        """
        try:
            print(f"{COLORS['blue']}Executando teste end-to-end...{COLORS['reset']}")
            
            # Executa o teste como um processo separado
            self.test_process = subprocess.Popen(
                [sys.executable, self.test_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Lê a saída do teste em tempo real
            for line in self.test_process.stdout:
                print(f"{COLORS['cyan']}[TESTE] {line.strip()}{COLORS['reset']}")
            
            # Aguarda o término do processo
            self.test_process.wait()
            
            # Verifica o código de saída
            if self.test_process.returncode == 0:
                print(f"{COLORS['green']}Teste concluído com sucesso!{COLORS['reset']}")
            else:
                print(f"{COLORS['red']}Teste falhou com código de saída {self.test_process.returncode}{COLORS['reset']}")
                
        except Exception as e:
            logger.error(f"Erro ao executar o teste: {e}")
            print(f"{COLORS['red']}Erro ao executar o teste: {e}{COLORS['reset']}")
    
    def _run_monitor(self):
        """
        Executa o monitor de testes.
        """
        try:
            print(f"{COLORS['magenta']}Iniciando monitor de testes...{COLORS['reset']}")
            
            # Inicia o monitor
            self.test_monitor.start()
            
        except Exception as e:
            logger.error(f"Erro ao executar o monitor: {e}")
            print(f"{COLORS['red']}Erro ao executar o monitor: {e}{COLORS['reset']}")
    
    def _cleanup(self):
        """
        Limpa recursos e finaliza processos.
        """
        # Finaliza o processo de teste se ainda estiver em execução
        if self.test_process and self.test_process.poll() is None:
            self.test_process.terminate()
            try:
                self.test_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.test_process.kill()
        
        # Finaliza o monitor
        if hasattr(self.test_monitor, 'stop'):
            self.test_monitor.stop()
        
        print(f"{COLORS['yellow']}Recursos liberados{COLORS['reset']}")

def main():
    """
    Função principal.
    """
    parser = argparse.ArgumentParser(description='Executor de testes end-to-end com monitoramento')
    parser.add_argument('--test-script', help='Caminho para o script de teste')
    parser.add_argument('--log-path', help='Caminho para o arquivo de log')
    args = parser.parse_args()
    
    try:
        runner = E2ETestRunner(args.test_script, args.log_path)
        runner.start()
    except Exception as e:
        logger.error(f"Erro ao iniciar o executor: {e}")
        print(f"{COLORS['red']}Erro ao iniciar o executor: {e}{COLORS['reset']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
