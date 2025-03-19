"""
Módulo para configuração avançada de logs de debug.

Este módulo implementa um sistema de logging avançado para facilitar
a depuração do sistema ChatwootAI, especialmente durante testes de
integração com o Chatwoot e WhatsApp.
"""

import os
import sys
import logging
import json
import inspect
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, Callable

# Definir níveis de log personalizados
TRACE = 5  # Nível mais detalhado que DEBUG
logging.addLevelName(TRACE, "TRACE")

# Configuração global de logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEBUG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
TRACE_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - [%(funcName)s] - %(message)s'

# Diretório para logs
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

class DebugLogger:
    """
    Classe para gerenciar logs de debug avançados.
    
    Permite configurar diferentes níveis de log, rotação de arquivos,
    formatação personalizada e outros recursos para facilitar a depuração.
    """
    
    def __init__(self, name: str, level: int = logging.INFO, 
                 log_to_file: bool = True, log_to_console: bool = True):
        """
        Inicializa o logger.
        
        Args:
            name: Nome do logger
            level: Nível de log (default: INFO)
            log_to_file: Se deve logar para arquivo
            log_to_console: Se deve logar para console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        
        # Limpar handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Definir formatadores para diferentes níveis
        self.default_formatter = logging.Formatter(LOG_FORMAT)
        self.debug_formatter = logging.Formatter(DEBUG_FORMAT)
        self.trace_formatter = logging.Formatter(TRACE_FORMAT)
        
        # Adicionar handler para console se solicitado
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(self._get_formatter_for_level(level))
            self.logger.addHandler(console_handler)
        
        # Adicionar handler para arquivo se solicitado
        if log_to_file:
            # Nome do arquivo de log baseado na data e no nome do logger
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file = os.path.join(LOG_DIR, f"{timestamp}_{name}.log")
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(self._get_formatter_for_level(level))
            self.logger.addHandler(file_handler)
    
    def _get_formatter_for_level(self, level: int) -> logging.Formatter:
        """
        Retorna o formatador apropriado para o nível de log.
        
        Args:
            level: Nível de log
            
        Returns:
            Formatador para o nível especificado
        """
        if level <= TRACE:
            return self.trace_formatter
        elif level <= logging.DEBUG:
            return self.debug_formatter
        else:
            return self.default_formatter
    
    def trace(self, msg: str, *args, **kwargs):
        """
        Loga uma mensagem no nível TRACE.
        
        Args:
            msg: Mensagem a ser logada
            *args: Argumentos para formatação da mensagem
            **kwargs: Argumentos nomeados para formatação da mensagem
        """
        self.logger.log(TRACE, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """Loga uma mensagem no nível DEBUG."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Loga uma mensagem no nível INFO."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Loga uma mensagem no nível WARNING."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Loga uma mensagem no nível ERROR."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Loga uma mensagem no nível CRITICAL."""
        self.logger.critical(msg, *args, **kwargs)
    
    def log_dict(self, level: int, prefix: str, data: Dict[str, Any]):
        """
        Loga um dicionário de forma formatada.
        
        Args:
            level: Nível de log
            prefix: Prefixo para a mensagem
            data: Dicionário a ser logado
        """
        try:
            formatted_data = json.dumps(data, indent=2, ensure_ascii=False)
            self.logger.log(level, f"{prefix}:\n{formatted_data}")
        except Exception as e:
            self.logger.error(f"Erro ao formatar dicionário: {e}")
            self.logger.log(level, f"{prefix}: {data}")
    
    def log_exception(self, e: Exception, context: Optional[str] = None):
        """
        Loga uma exceção com detalhes e contexto.
        
        Args:
            e: Exceção a ser logada
            context: Contexto adicional (opcional)
        """
        if context:
            self.logger.error(f"Exceção em {context}: {type(e).__name__}: {str(e)}")
        else:
            self.logger.error(f"Exceção: {type(e).__name__}: {str(e)}")
        
        # Adicionar informações do traceback
        import traceback
        tb = traceback.format_exc()
        self.logger.error(f"Traceback:\n{tb}")


def log_function_call(logger: Optional[DebugLogger] = None, level: int = logging.DEBUG):
    """
    Decorador para logar chamadas de função com argumentos e resultado.
    
    Args:
        logger: Logger a ser usado. Se None, usa o logger padrão do módulo
        level: Nível de log a ser usado
        
    Returns:
        Decorador para a função
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Usar o logger fornecido ou criar um novo
            log = logger or DebugLogger(func.__module__)
            
            # Obter informações da função
            func_name = func.__name__
            module_name = func.__module__
            
            # Logar chamada com argumentos
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            
            log.log(level, f"CHAMANDO {module_name}.{func_name}({signature})")
            
            # Medir tempo de execução
            start_time = time.time()
            
            try:
                # Executar a função
                result = func(*args, **kwargs)
                
                # Calcular tempo de execução
                end_time = time.time()
                exec_time = end_time - start_time
                
                # Logar resultado
                log.log(level, f"RETORNO de {func_name} (tempo: {exec_time:.6f}s): {repr(result)}")
                
                return result
            
            except Exception as e:
                # Logar exceção
                end_time = time.time()
                exec_time = end_time - start_time
                
                log.error(f"EXCEÇÃO em {func_name} (tempo: {exec_time:.6f}s): {type(e).__name__}: {str(e)}")
                
                # Re-lançar exceção
                raise
        
        return wrapper
    
    return decorator


def get_logger(name: str, level: int = logging.INFO) -> DebugLogger:
    """
    Obtém um logger com o nome especificado.
    
    Função de conveniência para criar ou obter um logger.
    
    Args:
        name: Nome do logger
        level: Nível de log (default: INFO)
        
    Returns:
        DebugLogger configurado
    """
    return DebugLogger(name, level)


# Logger global para módulos que não precisam de um logger específico
system_logger = get_logger("system", logging.INFO)


# Configurar log global (para outros módulos que usam logging diretamente)
def configure_global_logging(level: int = logging.INFO):
    """
    Configura o sistema de logging global.
    
    Args:
        level: Nível de log (default: INFO)
    """
    # Limpar configuração existente
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    
    # Configurar formatador
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Handler para arquivo
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(LOG_DIR, f"{timestamp}_global.log")
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Configurar root logger
    root.setLevel(level)
    root.addHandler(console_handler)
    root.addHandler(file_handler)
    
    return root
