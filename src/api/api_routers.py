# src/api/api_routers.py
from fastapi import APIRouter

api_router = APIRouter()


# 1. Авторизация (логин/логаут)
from src.api.v1.authorization import router as auth_user_router
api_router.include_router(auth_user_router, prefix="/auth", tags=["Auth users"])

# 2. Обновление токенов (refresh)
from src.api.v1.auth_refresh import router as auth_refresh_router
api_router.include_router(auth_refresh_router, prefix="/auth", tags=["Refresh Token"])

# 3. Регистрация организации и суперпользователя
from src.api.v1.registration import router as register_organization_and_superuser
api_router.include_router(register_organization_and_superuser, prefix="/register", tags=["Register"])

# 3. Регистрация организации и суперпользователя
from src.api.v1.create_car import router as create_car
api_router.include_router(create_car, prefix="/cars", tags=["Car"])

# 3. Регистрация организации и суперпользователя
from src.api.v1.car_records import router as car_records
api_router.include_router(car_records, prefix="/cars_records", tags=["Car records"])


from src.api.v1.check_version import router as check_version
api_router.include_router(check_version, prefix="/version", tags=["Version"])

