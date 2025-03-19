"""
Serviço de Sincronização Periódica.
Este serviço executa sincronizações completas em intervalos regulares para garantir
a consistência entre o PostgreSQL e o Qdrant.
"""
import os
import logging
import asyncio
import time
from datetime import datetime
from typing import Optional

from src.services.data_sync_service import DataSyncService

class PeriodicSyncService:
    """
    Serviço para sincronização periódica entre PostgreSQL e Qdrant.
    
    Este serviço executa sincronizações completas em intervalos regulares para
    garantir a consistência dos dados, mesmo se algumas notificações forem perdidas.
    """
    
    def __init__(
        self, 
        data_sync_service: DataSyncService,
        sync_interval: int = 3600  # Padrão: 1 hora
    ):
        """
        Inicializa o serviço de sincronização periódica.
        
        Args:
            data_sync_service: Instância do DataSyncService para sincronização.
            sync_interval: Intervalo entre sincronizações em segundos.
        """
        self.data_sync_service = data_sync_service
        self.sync_interval = sync_interval
        self.running = False
        self.last_sync_time = None
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Serviço de Sincronização Periódica inicializado com intervalo de {sync_interval} segundos")
        
    async def start(self):
        """
        Inicia o serviço de sincronização periódica.
        
        Este método executa sincronizações completas em intervalos regulares
        até que o serviço seja parado.
        """
        self.running = True
        
        try:
            # Executar uma sincronização inicial
            await self._perform_sync()
            
            # Iniciar loop de sincronização periódica
            while self.running:
                # Calcular tempo até a próxima sincronização
                if self.last_sync_time:
                    elapsed = time.time() - self.last_sync_time.timestamp()
                    wait_time = max(0, self.sync_interval - elapsed)
                else:
                    wait_time = self.sync_interval
                
                self.logger.info(f"Próxima sincronização em {wait_time:.1f} segundos")
                
                # Aguardar até o próximo intervalo
                await asyncio.sleep(wait_time)
                
                # Verificar se o serviço ainda está rodando
                if not self.running:
                    break
                    
                # Executar sincronização
                await self._perform_sync()
                
        except Exception as e:
            self.logger.error(f"Erro no serviço de sincronização periódica: {e}")
            self.running = False
            
    async def _perform_sync(self):
        """
        Executa uma sincronização completa.
        
        Este método sincroniza todos os produtos e regras de negócio entre
        o PostgreSQL e o Qdrant.
        """
        try:
            self.logger.info("Iniciando sincronização periódica")
            
            # Sincronizar produtos
            products_success = await asyncio.to_thread(
                self.data_sync_service.full_sync_products
            )
            
            # Sincronizar regras de negócio
            rules_success = await asyncio.to_thread(
                self.data_sync_service.full_sync_business_rules
            )
            
            # Registrar resultado
            self.last_sync_time = datetime.now()
            if products_success and rules_success:
                self.logger.info(f"Sincronização periódica concluída com sucesso em {self.last_sync_time}")
            else:
                self.logger.warning(
                    f"Sincronização periódica concluída com avisos em {self.last_sync_time}. "
                    f"Produtos: {'OK' if products_success else 'FALHA'}, "
                    f"Regras: {'OK' if rules_success else 'FALHA'}"
                )
                
        except Exception as e:
            self.logger.error(f"Erro durante sincronização periódica: {e}")
            
    def stop(self):
        """
        Para o serviço de sincronização periódica.
        """
        self.running = False
        self.logger.info("Serviço de sincronização periódica parado")
        
    @property
    def status(self):
        """
        Retorna o status atual do serviço.
        
        Returns:
            Dicionário com informações de status do serviço.
        """
        return {
            "running": self.running,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "sync_interval": self.sync_interval,
            "next_sync_in": self.sync_interval - (time.time() - self.last_sync_time.timestamp()) if self.last_sync_time else self.sync_interval
        }
