from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.services.pipeline_service import pipeline_service
from app.core.config import settings
from app.core.auth import get_current_user, get_user_id
from app.core.rate_limit import enforce_upload_rate_limit
from typing import Dict, List, Optional, Any
import shutil
import os
import uuid
import json
import open3d as o3d
import re

router = APIRouter()

# =============================================================================
# Upload Validation Constants
# =============================================================================
# Maximum file size: 50MB per file
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
MAX_FILE_SIZE_MB = MAX_FILE_SIZE_BYTES / (1024 * 1024)

# Maximum number of files per upload
MAX_FILES_PER_UPLOAD = 20

# Allowed MIME types for image uploads
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg", 
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
}

# Allowed file extensions (lowercase)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}

# Filename validation pattern (alphanumeric, dashes, underscores, dots)
SAFE_FILENAME_PATTERN = re.compile(r'^[\w\-. ]+$')

# Simple file-based job store
JOBS_FILE = os.path.join(settings.BASE_DIR, "storage", "jobs.json")

# Ensure jobs file exists
if not os.path.exists(os.path.dirname(JOBS_FILE)):
    os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)

def load_jobs() -> Dict:
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_job(job_id: str, status: str, result: str = None, error: str = None, user_id: str = None):
    jobs = load_jobs()
    existing = jobs.get(job_id, {})
    jobs[job_id] = {
        "status": status,
        "result": result,
        "error": error,
        "user_id": user_id or existing.get("user_id")  # Preserve user_id on updates
    }
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

def get_job(job_id: str):
    jobs = load_jobs()
    return jobs.get(job_id)

def get_jobs_for_user(user_id: Optional[str]) -> Dict:
    """Get jobs filtered by user. If user_id is None, returns all jobs (anonymous/admin mode)."""
    jobs = load_jobs()
    if user_id is None:
        return jobs
    return {k: v for k, v in jobs.items() if v.get("user_id") == user_id or v.get("user_id") is None}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and other attacks."""
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Replace potentially dangerous characters
    filename = filename.replace("..", "_")
    
    # If filename doesn't match safe pattern, generate a safe one
    name, ext = os.path.splitext(filename)
    if not SAFE_FILENAME_PATTERN.match(name):
        name = f"upload_{uuid.uuid4().hex[:8]}"
    
    return f"{name}{ext.lower()}"


def validate_file_extension(filename: str) -> bool:
    """Check if file has an allowed extension."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_content_type(content_type: Optional[str]) -> bool:
    """Check if content type is allowed."""
    if not content_type:
        return False
    # Handle content types with charset (e.g., "image/jpeg; charset=utf-8")
    base_type = content_type.split(";")[0].strip().lower()
    return base_type in ALLOWED_MIME_TYPES


async def validate_file_size(file: UploadFile) -> int:
    """
    Validate file size by reading the file.
    Returns the file size in bytes.
    Raises HTTPException if file is too large.
    """
    # Read file content to check size
    content = await file.read()
    size = len(content)
    
    if size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File '{file.filename}' is too large ({size / (1024*1024):.1f}MB). Maximum size is {MAX_FILE_SIZE_MB:.0f}MB."
        )
    
    if size == 0:
        raise HTTPException(
            status_code=400,
            detail=f"File '{file.filename}' is empty."
        )
    
    # Reset file position for later reading
    await file.seek(0)
    return size


async def validate_upload_files(files: List[UploadFile]) -> List[UploadFile]:
    """
    Validate all uploaded files.
    Returns the validated files list.
    Raises HTTPException on validation failure.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum {MAX_FILES_PER_UPLOAD} files per upload."
        )
    
    total_size = 0
    validated_files = []
    
    for file in files:
        # Check filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")
        
        # Validate extension
        if not validate_file_extension(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' has unsupported extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Validate content type
        if not validate_content_type(file.content_type):
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' has unsupported content type '{file.content_type}'. Allowed image types only."
            )
        
        # Validate file size
        file_size = await validate_file_size(file)
        total_size += file_size
        
        validated_files.append(file)
    
    # Check total upload size (max 200MB total)
    max_total_size = 200 * 1024 * 1024  # 200MB
    if total_size > max_total_size:
        raise HTTPException(
            status_code=413,
            detail=f"Total upload size ({total_size / (1024*1024):.1f}MB) exceeds maximum ({max_total_size / (1024*1024):.0f}MB)."
        )
    
    return validated_files


async def upload_rate_limit_dependency(
    request: Request,
    user_id: Optional[str] = Depends(get_user_id),
) -> Optional[str]:
    """
    Apply rate limiting per user (or client IP when anonymous) and return the user id.
    This keeps dependency evaluation to a single call.
    """
    await enforce_upload_rate_limit(request, user_id)
    return user_id


def process_job_task(job_id: str, image_paths: List[str], user_id: Optional[str] = None):
    """Background task to process uploaded images into 3D model."""
    save_job(job_id, "processing", user_id=user_id)
    try:
        if len(image_paths) == 1:
            pipeline_service.process_job(job_id, image_paths[0])
        else:
            pipeline_service.process_job_multiview(job_id, image_paths)
            
        # Check if output exists
        # Pipeline produces .obj if successful (via convert_to_mesh)
        output_mesh = os.path.join(settings.OUTPUT_DIR, f"{job_id}.obj")
        
        if os.path.exists(output_mesh):
            save_job(job_id, "completed", result=output_mesh, user_id=user_id)
        else:
            save_job(job_id, "completed_partial", error="Output mesh not found", user_id=user_id)
    except Exception as e:
        save_job(job_id, "failed", error=str(e), user_id=user_id)

@router.post("/upload")
async def upload_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = Depends(upload_rate_limit_dependency),
):
    """
    Upload one or more images to create a 3D model.
    
    Validation:
    - Allowed formats: JPEG, PNG, WebP, BMP, TIFF
    - Max file size: 50MB per file
    - Max files: 20 per upload
    - Max total size: 200MB per upload
    """
    # Validate all files before processing
    validated_files = await validate_upload_files(files)
    
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(settings.UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    saved_paths = []
    try:
        for file in validated_files:
            # Sanitize filename to prevent path traversal attacks
            safe_filename = sanitize_filename(file.filename)
            file_path = os.path.join(job_dir, safe_filename)
            
            # Ensure we don't overwrite files with same name
            counter = 1
            base_name, ext = os.path.splitext(safe_filename)
            while os.path.exists(file_path):
                file_path = os.path.join(job_dir, f"{base_name}_{counter}{ext}")
                counter += 1
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_paths.append(file_path)
    except Exception as e:
        # Clean up on failure
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to save files: {str(e)}")
    
    save_job(job_id, "queued", user_id=user_id)
    background_tasks.add_task(process_job_task, job_id, saved_paths, user_id)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "files": [os.path.basename(p) for p in saved_paths],
        "file_count": len(saved_paths)
    }

@router.get("/status/{job_id}")
async def get_status(job_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs")
async def list_jobs(user_id: Optional[str] = Depends(get_user_id)):
    return get_jobs_for_user(user_id)


@router.get("/download/{job_id}")
async def download_model(job_id: str, format: str = "obj", user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] not in ["completed", "completed_partial"]:
        raise HTTPException(status_code=400, detail=f"Job status is {job['status']}")
    
    # Base result (usually .obj or .ply)
    source_path = job["result"]
    if not source_path or not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Result file missing")
        
    # Normalize format
    format = format.lower()
    allowed_formats = ["obj", "stl", "gltf", "glb", "ply"]
    if format not in allowed_formats:
        raise HTTPException(status_code=400, detail=f"Format {format} not supported. Allowed: {allowed_formats}")

    # Determine target path
    # If source is /path/to/jobid.obj and format is stl -> /path/to/jobid.stl
    base_name = os.path.splitext(source_path)[0]
    target_path = f"{base_name}.{format}"
    
    # If target exists, return it
    if os.path.exists(target_path):
        return FileResponse(target_path, filename=os.path.basename(target_path))
        
    # Conversion logic
    try:
        # Read source
        if source_path.endswith(".ply"):
            mesh = o3d.io.read_triangle_mesh(source_path)
            if not mesh.has_triangles():
                # It might be a point cloud, try reading as PCD and reconstructing? 
                # For now assuming it's a mesh or we fail gracefully if user requests mesh format from pcd
                pass
        else:
            mesh = o3d.io.read_triangle_mesh(source_path)
            
        if not mesh.has_triangles() and not source_path.endswith(".ply"):
             raise HTTPException(status_code=500, detail="Source model has no geometry")

        # Write target
        o3d.io.write_triangle_mesh(target_path, mesh)
        
        return FileResponse(target_path, filename=os.path.basename(target_path))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


class ScalingRequest(BaseModel):
    target_dimension: float
    axis: str = "y"

@router.post("/jobs/{job_id}/scale")
async def scale_model(job_id: str, request: ScalingRequest, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] not in ["completed", "completed_partial"]:
        raise HTTPException(status_code=400, detail="Job not completed")
    
    result_path = job["result"]
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Model file not found")
        
    # Import here to avoid circular imports if any
    from scaling import MeshScaler
    scaler = MeshScaler()
    
    success = scaler.scale_mesh(result_path, request.target_dimension, request.axis)
    
    if success:
        return {"status": "success", "message": f"Model scaled to {request.target_dimension} along {request.axis}"}
    else:
        raise HTTPException(status_code=500, detail="Scaling failed")
