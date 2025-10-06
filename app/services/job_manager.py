"""
Gestor de tareas en segundo plano para scraping SEACE
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

from app.models.seace import ObraSEACE

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Estados posibles de un job"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    """Representa un job de scraping"""
    def __init__(self, job_id: str, cui: str, anio: int):
        self.job_id = job_id
        self.cui = cui
        self.anio = anio
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[ObraSEACE] = None
        self.error: Optional[str] = None
        self.error_details: Optional[str] = None


class JobManager:
    """
    Gestor simple de jobs en memoria

    NOTA: Para producción, esto debería usar Redis o una base de datos
    para compartir estado entre workers y persistir resultados
    """
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.max_jobs = 1000  # Límite de jobs almacenados en memoria

    def create_job(self, cui: str, anio: int) -> str:
        """Crea un nuevo job y retorna su ID"""
        job_id = str(uuid.uuid4())
        job = Job(job_id, cui, anio)

        # Limpiar jobs antiguos si superamos el límite
        if len(self.jobs) >= self.max_jobs:
            self._cleanup_old_jobs()

        self.jobs[job_id] = job
        logger.info(f"Job creado: {job_id} para CUI {cui}, año {anio}")
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Obtiene un job por su ID"""
        return self.jobs.get(job_id)

    def update_status(self, job_id: str, status: JobStatus):
        """Actualiza el estado de un job"""
        job = self.jobs.get(job_id)
        if job:
            job.status = status
            if status == JobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.now()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                job.completed_at = datetime.now()
            logger.info(f"Job {job_id} actualizado a estado: {status}")

    def set_result(self, job_id: str, result: ObraSEACE):
        """Guarda el resultado exitoso de un job"""
        job = self.jobs.get(job_id)
        if job:
            job.result = result
            self.update_status(job_id, JobStatus.COMPLETED)
            logger.info(f"Job {job_id} completado exitosamente")

    def set_error(self, job_id: str, error: str, details: Optional[str] = None):
        """Guarda el error de un job"""
        job = self.jobs.get(job_id)
        if job:
            job.error = error
            job.error_details = details
            self.update_status(job_id, JobStatus.FAILED)
            logger.error(f"Job {job_id} falló: {error}")

    def _cleanup_old_jobs(self):
        """Elimina los jobs más antiguos cuando superamos el límite"""
        # Ordenar por fecha de creación
        sorted_jobs = sorted(
            self.jobs.items(),
            key=lambda x: x[1].created_at
        )

        # Mantener solo los más recientes
        jobs_to_keep = sorted_jobs[-int(self.max_jobs * 0.8):]  # Mantener 80%
        self.jobs = dict(jobs_to_keep)
        logger.info(f"Limpieza de jobs: {len(sorted_jobs) - len(jobs_to_keep)} jobs eliminados")


# Instancia global del gestor de jobs
job_manager = JobManager()
