#!/usr/bin/env python3
"""
Script para iniciar el scheduler de notificaciones WhatsApp en background
Úselo para procesamiento de notificaciones en producción
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class WhatsAppSchedulerRunner:
    """Runner para el scheduler de notificaciones WhatsApp"""
    
    def __init__(self):
        self.scheduler = None
        self.running = False
    
    async def start(self):
        """Inicia el scheduler"""
        try:
            # Importar el scheduler service
            from app.services.scheduler_service import scheduler_service
            
            self.scheduler = scheduler_service
            self.running = True
            
            logger.info("🚀 Iniciando WhatsApp Notification Scheduler...")
            
            # Iniciar el scheduler
            await self.scheduler.start_scheduler()
            
            logger.info("✅ Scheduler iniciado correctamente")
            logger.info("📋 Estado del scheduler:")
            status = self.scheduler.get_scheduler_status()
            for key, value in status.items():
                logger.info(f"   {key}: {value}")
            
            # Mantener el proceso corriendo
            while self.running:
                await asyncio.sleep(60)  # Verificar cada minuto
                
                # Log de estado cada 10 minutos
                if asyncio.get_event_loop().time() % 600 < 60:
                    status = self.scheduler.get_scheduler_status()
                    logger.info(f"📊 Scheduler activo: {status['active_tasks']} tareas")
            
        except ImportError as e:
            logger.error(f"❌ Error importando módulos: {e}")
            logger.error("Asegúrese de que todas las dependencias estén instaladas")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Error iniciando scheduler: {e}")
            await self.stop()
            sys.exit(1)
    
    async def stop(self):
        """Detiene el scheduler"""
        if self.scheduler and self.running:
            logger.info("🛑 Deteniendo scheduler...")
            self.running = False
            await self.scheduler.stop_scheduler()
            logger.info("✅ Scheduler detenido correctamente")
    
    def handle_signal(self, signum, frame):
        """Maneja señales del sistema para parada limpia"""
        logger.info(f"📡 Señal recibida: {signum}")
        asyncio.create_task(self.stop())

async def main():
    """Función principal"""
    
    # Verificar configuración
    try:
        from app.core.config import settings
        
        if not settings.BACKGROUND_TASKS_ENABLED:
            logger.warning("⚠️ BACKGROUND_TASKS_ENABLED está deshabilitado")
            logger.info("Configure BACKGROUND_TASKS_ENABLED=true para habilitar")
            return
        
        if not settings.WHATSAPP_ACCESS_TOKEN:
            logger.warning("⚠️ WHATSAPP_ACCESS_TOKEN no configurado")
            logger.info("Configure las credenciales de WhatsApp Business API")
            return
        
        logger.info("✅ Configuración verificada")
        
    except Exception as e:
        logger.error(f"❌ Error verificando configuración: {e}")
        return
    
    # Crear y configurar runner
    runner = WhatsAppSchedulerRunner()
    
    # Configurar manejo de señales para parada limpia
    def signal_handler(signum, frame):
        logger.info(f"📡 Recibida señal {signum}, iniciando parada limpia...")
        runner.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await runner.start()
    except KeyboardInterrupt:
        logger.info("🔄 Interrupción de teclado recibida")
    finally:
        await runner.stop()

def run_scheduler():
    """Función de conveniencia para ejecutar el scheduler"""
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Mostrar información del sistema
    print("=" * 60)
    print("🚀 WHATSAPP NOTIFICATION SCHEDULER")
    print("=" * 60)
    print("Sistema de notificaciones automáticas para valorizaciones")
    print("Procesa y envía notificaciones WhatsApp en background")
    print()
    print("Para detener: Ctrl+C o enviar señal SIGTERM")
    print("=" * 60)
    print()
    
    # Ejecutar scheduler
    run_scheduler()