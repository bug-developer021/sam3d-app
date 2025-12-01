import asyncio
import os
import uuid
from datetime import datetime
from typing import List

from celery.utils.log import get_task_logger

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.entities import Asset, AssetType, ProcessingJob, ProcessingStatus
from app.services.pipeline_service import pipeline_service
from app.worker.celery_app import celery_app

logger = get_task_logger(__name__)


async def _process_job(job_id: uuid.UUID, image_paths: List[str]) -> None:
    async with AsyncSessionLocal() as session:
        job = await session.get(ProcessingJob, job_id)
        if not job:
            logger.warning("Job %s no longer exists", job_id)
            return

        job.status = ProcessingStatus.PROCESSING
        job.started_at = datetime.utcnow()
        await session.commit()

        try:
            if len(image_paths) == 1:
                pipeline_service.process_job(str(job_id), image_paths[0])
            else:
                pipeline_service.process_job_multiview(str(job_id), image_paths)

            output_mesh = os.path.join(settings.OUTPUT_DIR, f"{job_id}.obj")
            session.add(
                Asset(
                    project_id=job.project_id,
                    type=AssetType.OUTPUT_MESH,
                    uri=output_mesh,
                    file_name=os.path.basename(output_mesh),
                )
            )
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.error_message = None
            await session.commit()
        except Exception as exc:
            job.status = ProcessingStatus.FAILED
            job.error_message = str(exc)
            await session.commit()
            logger.exception("Job %s failed", job_id)


@celery_app.task(name="jobs.process")
def run_processing_job(job_id: str, image_paths: List[str]) -> None:
    """Celery task entrypoint to process reconstruction jobs."""
    logger.info("Starting processing job %s", job_id)
    asyncio.run(_process_job(uuid.UUID(job_id), image_paths))


def enqueue_processing_job(job_id: uuid.UUID, image_paths: List[str]) -> str:
    """Enqueue a processing job and return the task id."""
    result = run_processing_job.delay(str(job_id), image_paths)
    return result.id

