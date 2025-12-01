from fastapi import APIRouter
from app.api.endpoints import jobs, projects

api_router = APIRouter()
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
