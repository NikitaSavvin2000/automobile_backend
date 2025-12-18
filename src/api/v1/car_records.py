# src/api/v1/car_records.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, Form, Path
from typing import List
from src.services.car_records import create_car_record, delete_car_record, get_car_records, get_car_record_detail, update_car_record, delete_car_record_image
from src.core.token import jwt_token_validator
from src.schemas import CarRecordCreateResponse, CarRecordDetailResponse
from src.core.logger import logger

router = APIRouter()


@router.post(
    "/create",
    response_model=CarRecordCreateResponse,
    summary="Создать запись автомобиля",
    description="Создает запись для автомобиля и опционально загружает изображения"
)
async def create_user_car_record(
        car_id: int = Form(...),
        record_type: str = Form(...),
        name: str = Form(...),
        description: str = Form(...),
        record_date: str | None = Form(None),
        mileage: int | None = Form(None),
        service_place: str | None = Form(None),
        cost: float | None = Form(None),
        files: List[UploadFile] | None = None,
        user: dict = Depends(jwt_token_validator)
):
    """
    Эндпоинт для создания записи автомобиля с опциональной загрузкой изображений.

    Parameters:
    - **car_id**: ID автомобиля
    - **record_type, name, description**: обязательные поля записи
    - **record_date, mileage, service_place, cost**: опциональные поля
    - **files**: список изображений
    - **user**: данные текущего пользователя из токена

    Raises:
    - **HTTPException 400**: если обязательные поля не переданы
    - **HTTPException 500**: если произошла ошибка при работе с базой данных
    """
    user_id_owner = int(user["sub"])
    payload = {
        "record_type": record_type,
        "name": name,
        "description": description,
        "record_date": record_date,
        "mileage": mileage,
        "service_place": service_place,
        "cost": cost
    }
    try:
        result = await create_car_record(payload, user_id_owner, car_id, files)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании записи для автомобиля {car_id} пользователя {user_id_owner}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось создать запись для автомобиля")


@router.delete(
    "/delete/{record_id}",
    summary="Удалить запись автомобиля",
    description="Помечает запись автомобиля как удаленную (is_deleted=true)"
)
async def delete_user_car_record(
        record_id: int,
        user: dict = Depends(jwt_token_validator)
):
    user_id_owner = int(user["sub"])
    try:
        result = await delete_car_record(record_id=record_id, user_id_owner=user_id_owner)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Ошибка при удалении записи автомобиля {record_id} пользователя {user_id_owner}: {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Не удалось удалить запись автомобиля")


@router.get(
    "/list",
    summary="Получить записи автомобиля",
    description="Возвращает список активных и неудаленных записей автомобиля"
)
async def get_user_car_records(
        car_id: int,
        user: dict = Depends(jwt_token_validator)
):
    user_id_owner = int(user["sub"])
    try:
        result = await get_car_records(
            car_id=car_id,
            user_id_owner=user_id_owner
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Ошибка при получении записей автомобиля {car_id} пользователя {user_id_owner}: {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Не удалось получить записи автомобиля")



@router.get(
    "/info/{car}/{record_id}",
    response_model=CarRecordDetailResponse,
    summary="Получить запись автомобиля",
    description="Возвращает детальную информацию о записи автомобиля вместе с изображениями"
)
async def get_user_car_record(
        car_id: int,
        car_record_id: int,
        user: dict = Depends(jwt_token_validator)
):
    """
    Эндпоинт для получения детальной информации о записи автомобиля.

    Parameters:
    - **car_id**: ID автомобиля
    - **car_record_id**: ID записи автомобиля
    - **user**: данные текущего пользователя из токена

    Returns:
    - car_record_id
    - name
    - description
    - record_date
    - mileage
    - service_place
    - cost
    - images: список изображений (bytes)

    Raises:
    - **HTTPException 404**: если запись не найдена
    - **HTTPException 500**: если произошла ошибка при работе с базой данных
    """
    user_id_owner = int(user["sub"])
    try:
        record_detail = await get_car_record_detail(user_id_owner, car_id, car_record_id)
        return record_detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении записи автомобиля {car_record_id} пользователя {user_id_owner}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось получить запись автомобиля")



@router.put(
    "/update",
    response_model=dict,
    summary="Обновить запись автомобиля",
    description="Обновляет запись автомобиля и опционально добавляет новые изображения"
)
async def update_user_car_record(
        car_id: int = Form(...),
        car_record_id: int = Form(...),
        record_type: str = Form(...),
        name: str = Form(...),
        description: str = Form(...),
        record_date: str | None = Form(None),
        mileage: int | None = Form(None),
        service_place: str | None = Form(None),
        cost: float | None = Form(None),
        files: List[UploadFile] | None = None,
        user: dict = Depends(jwt_token_validator)
):
    """
    Эндпоинт для обновления записи автомобиля с опциональной загрузкой изображений.

    Parameters:
    - **car_id**: ID автомобиля
    - **car_record_id**: ID записи автомобиля
    - **record_type, name, description**: обязательные поля записи
    - **record_date, mileage, service_place, cost**: опциональные поля
    - **files**: список новых изображений
    - **user**: данные текущего пользователя из токена

    Raises:
    - **HTTPException 400**: если обязательные поля не переданы
    - **HTTPException 404**: если запись не найдена
    - **HTTPException 500**: если произошла ошибка при работе с базой данных
    """
    user_id_owner = int(user["sub"])
    payload = {
        "record_type": record_type,
        "name": name,
        "description": description,
        "record_date": record_date,
        "mileage": mileage,
        "service_place": service_place,
        "cost": cost
    }

    try:
        result = await update_car_record(payload, user_id_owner, car_id, car_record_id, files)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении записи автомобиля {car_record_id} пользователя {user_id_owner}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось обновить запись автомобиля")



@router.delete(
    "/delete_image/{car_record_id}/{image_id}",
    response_model=dict,
    summary="Удалить изображение записи автомобиля",
    description="Помечает изображение записи автомобиля как удалённое"
)
async def delete_user_car_record_image(
        car_record_id: int = Path(..., description="ID записи автомобиля"),
        image_id: int = Path(..., description="ID изображения"),
        user: dict = Depends(jwt_token_validator)
):
    """
    Эндпоинт для мягкого удаления изображения записи автомобиля.

    Parameters:
    - **car_record_id**: ID записи автомобиля
    - **image_id**: ID изображения
    - **user**: данные текущего пользователя из токена

    Raises:
    - **HTTPException 404**: если изображение не найдено или доступ запрещён
    - **HTTPException 500**: если произошла ошибка при работе с базой данных
    """
    user_id_owner = int(user["sub"])
    try:
        result = await delete_car_record_image(user_id_owner, car_record_id, image_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении изображения {image_id} записи {car_record_id} пользователя {user_id_owner}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось удалить изображение")