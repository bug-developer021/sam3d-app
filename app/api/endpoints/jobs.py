import os
import shutil
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import open3d as o3d
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user, get_user_id
from app.core.config import settings
from app.core.db import AsyncSessionLocal, get_session
from app.core.rate_limit import rate_limit_upload_dependency
from app.models.entities import Asset, AssetType, ProcessingJob, ProcessingStatus, Project, User
from app.services.pipeline_service import pipeline_service

router = APIRouter()

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
MAX_FILES_PER_UPLOAD = 20
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def _validate_extension(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def _validate_content_type(content_type: Optional[str]) -> bool:
    if not content_type:
        return False
    base_type = content_type.split(";")[0].strip().lower()
    return base_type in ALLOWED_MIME_TYPES


async def _validate_file_size(file: UploadFile) -> int:
    content = await file.read()
    size = len(content)
    if size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File '{file.filename}' exceeds 50MB limit")
    if size == 0:
        raise HTTPException(status_code=400, detail=f"File '{file.filename}' is empty")
    await file.seek(0)
    return size


async def _validate_files(files: List[UploadFile]) -> List[UploadFile]:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(status_code=400, detail=f"Too many files. Max {MAX_FILES_PER_UPLOAD}")

    total_size = 0
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")
        if not _validate_extension(file.filename):
            raise HTTPException(status_code=400, detail=f"Unsupported extension for {file.filename}")
        if not _validate_content_type(file.content_type):
            raise HTTPException(status_code=400, detail=f"Unsupported content type for {file.filename}")
        total_size += await _validate_file_size(file)

    if total_size > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Total upload exceeds 200MB limit")
    return files


async def _ensure_user(session: AsyncSession, user_id: Optional[str]) -> Optional[uuid.UUID]:
    if not user_id:
        return None
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user id")

    existing = await session.get(User, user_uuid)
    if existing:
        return existing.id

    session.add(User(id=user_uuid))
    await session.flush()
    return user_uuid


async def _create_processing_job(
    session: AsyncSession,
    project: Project,
) -> ProcessingJob:
    job = ProcessingJob(project_id=project.id, task_id=uuid.uuid4().hex)
    session.add(job)
    await session.flush()
    return job


async def _save_input_assets(session: AsyncSession, project: Project, saved_paths: List[str]) -> None:
    for path in saved_paths:
        session.add(
            Asset(
                project_id=project.id,
                type=AssetType.INPUT_IMAGE,
                uri=path,
                file_name=os.path.basename(path),
            )
        )


async def process_job_task(job_id: uuid.UUID, image_paths: List[str]):
    async with AsyncSessionLocal() as session:
        job = await session.get(ProcessingJob, job_id)
        if not job:
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


upload_rate_limiter = rate_limit_upload_dependency()


@router.post(
    "/upload",
    dependencies=[Depends(upload_rate_limiter)],
)
async def upload_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
    user_id: Optional[str] = Depends(get_user_id),
):
    await _validate_files(files)

    job_dir = os.path.join(settings.UPLOAD_DIR, uuid.uuid4().hex)
    os.makedirs(job_dir, exist_ok=True)

    saved_paths: List[str] = []
    try:
        for file in files:
            file_path = os.path.join(job_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_paths.append(file_path)
    except Exception as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to save files: {exc}")

    try:
        async with session.begin():
            owner_id = await _ensure_user(session, user_id)
            project = Project(name=f"Job {os.path.basename(job_dir)}", user_id=owner_id)
            session.add(project)
            await session.flush()
            await _save_input_assets(session, project, saved_paths)
            job = await _create_processing_job(session, project)
    except Exception:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise

    background_tasks.add_task(process_job_task, job.id, saved_paths)

    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "project_id": str(project.id),
        "file_count": len(saved_paths),
    }


class ScalingRequest(BaseModel):
    target_dimension: float
    axis: str = "y"


@router.get("/status/{job_id}")
async def get_status(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    stmt = (
        select(ProcessingJob)
        .options(selectinload(ProcessingJob.project))
        .where(ProcessingJob.id == job_id)
    )
    result = await session.execute(stmt)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": str(job.id),
        "project_id": str(job.project_id),
        "status": job.status.value,
        "error": job.error_message,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
    }


@router.get("/jobs")
async def list_jobs(user_id: Optional[str] = Depends(get_user_id), session: AsyncSession = Depends(get_session)):
    stmt = select(ProcessingJob).options(selectinload(ProcessingJob.project))
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user id")
        stmt = stmt.join(Project).where(Project.user_id == user_uuid)
    result = await session.execute(stmt.order_by(ProcessingJob.created_at.desc()))
    jobs = result.scalars().all()
    return [
        {
            "job_id": str(job.id),
            "project_id": str(job.project_id),
            "status": job.status.value,
            "error": job.error_message,
        }
        for job in jobs
    ]


@router.get("/download/{job_id}")
async def download_model(job_id: uuid.UUID, format: str = "obj", session: AsyncSession = Depends(get_session)):
    stmt = (
        select(ProcessingJob)
        .options(selectinload(ProcessingJob.project).selectinload(Project.assets))
        .where(ProcessingJob.id == job_id)
    )
    result = await session.execute(stmt)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in {ProcessingStatus.COMPLETED, ProcessingStatus.PROCESSING}:
        raise HTTPException(status_code=400, detail=f"Job status is {job.status.value}")

    output_assets = [a for a in job.project.assets if a.type == AssetType.OUTPUT_MESH]
    if not output_assets:
        raise HTTPException(status_code=404, detail="Result file missing")

    source_path = output_assets[0].uri
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Result file missing")

    format = format.lower()
    allowed_formats = ["obj", "stl", "gltf", "glb", "ply"]
    if format not in allowed_formats:
        raise HTTPException(status_code=400, detail=f"Format {format} not supported. Allowed: {allowed_formats}")

    base_name = os.path.splitext(source_path)[0]
    target_path = f"{base_name}.{format}"

    if os.path.exists(target_path):
        return FileResponse(target_path, filename=os.path.basename(target_path))

    try:
        mesh = o3d.io.read_triangle_mesh(source_path)
        if not mesh.has_triangles():
            raise HTTPException(status_code=500, detail="Source model has no geometry")
        o3d.io.write_triangle_mesh(target_path, mesh)
        session.add(
            Asset(
                project_id=job.project_id,
                type=AssetType.OUTPUT_MESH,
                uri=target_path,
                file_name=os.path.basename(target_path),
            )
        )
        await session.commit()
        return FileResponse(target_path, filename=os.path.basename(target_path))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {exc}")


@router.post("/jobs/{job_id}/scale")
async def scale_model(
    job_id: uuid.UUID,
    request: ScalingRequest,
    session: AsyncSession = Depends(get_session),
    user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    stmt = (
        select(ProcessingJob)
        .options(selectinload(ProcessingJob.project).selectinload(Project.assets))
        .where(ProcessingJob.id == job_id)
    )
    result = await session.execute(stmt)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in {ProcessingStatus.COMPLETED, ProcessingStatus.PROCESSING}:
        raise HTTPException(status_code=400, detail="Job not completed")

    output_assets = [a for a in job.project.assets if a.type == AssetType.OUTPUT_MESH]
    if not output_assets:
        raise HTTPException(status_code=404, detail="Model file not found")

    result_path = output_assets[0].uri
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Model file not found")

    from scaling import MeshScaler

    scaler = MeshScaler()
    success = scaler.scale_mesh(result_path, request.target_dimension, request.axis)

    if success:
        return {"status": "success", "message": f"Model scaled to {request.target_dimension} along {request.axis}"}
    else:
        raise HTTPException(status_code=500, detail="Scaling failed")
