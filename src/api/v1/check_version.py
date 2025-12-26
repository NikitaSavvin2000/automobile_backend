from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.utils.сheck_version import get_version, update_version, check_version

router = APIRouter()

class VersionUpdateRequest(BaseModel):
    version: str

class VersionCheckRequest(BaseModel):
    version: str


@router.get(
    "/current",
    summary="Текущая версия приложения"
)
async def get_current_version():
    return get_version()


@router.post(
    "/update",
    summary="Обновить версию приложения"
)
async def update_current_version(payload: VersionUpdateRequest):
    update_version(payload.version)
    return {"status": "ok"}


@router.post(
    "/check",
    summary="Проверка версии клиента"
)
async def check_client_version(payload: VersionCheckRequest):
    return check_version(payload.version)
