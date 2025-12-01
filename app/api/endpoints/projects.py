import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_user_id
from app.core.db import get_session
from app.models.entities import Asset, AssetType, Project

router = APIRouter()


class AssetCreate(BaseModel):
    type: AssetType
    uri: str
    file_name: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assets: List[AssetCreate] = Field(default_factory=list)


class AssetResponse(BaseModel):
    id: uuid.UUID
    type: AssetType
    uri: str
    file_name: Optional[str]

    class Config:
        orm_mode = True


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    assets: List[AssetResponse]

    class Config:
        orm_mode = True


async def _register_assets(session: AsyncSession, project: Project, assets: List[AssetCreate]) -> None:
    for asset in assets:
        if not asset.uri:
            raise HTTPException(status_code=400, detail="Asset URI is required")
        session.add(
            Asset(
                project_id=project.id,
                type=asset.type,
                uri=asset.uri,
                file_name=asset.file_name,
            )
        )


@router.post("/", response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    user_id: Optional[str] = Depends(get_user_id),
):
    async with session.begin():
        project = Project(name=payload.name, description=payload.description)
        if user_id:
            try:
                project.user_id = uuid.UUID(user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user id")
        session.add(project)
        await session.flush()
        await _register_assets(session, project, payload.assets)

    await session.refresh(project, attribute_names=["assets"])
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    session: AsyncSession = Depends(get_session),
    user_id: Optional[str] = Depends(get_user_id),
):
    stmt = select(Project).options(selectinload(Project.assets))
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user id")
        stmt = stmt.where(Project.user_id == user_uuid)
    result = await session.execute(stmt)
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user_id: Optional[str] = Depends(get_user_id),
):
    stmt = (
        select(Project)
        .options(selectinload(Project.assets))
        .where(Project.id == project_id)
    )
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user id")
        stmt = stmt.where(Project.user_id == user_uuid)

    result = await session.execute(stmt)
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
