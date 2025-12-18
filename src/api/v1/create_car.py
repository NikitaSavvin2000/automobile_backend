# src/api/v1/cars.py
from fastapi import APIRouter, HTTPException, Depends
from src.services.car import create_car, get_user_cars, update_car, delete_car
from src.core.token import jwt_token_validator
from src.schemas import CarCreateRequest, CarCreateResponse, CarListResponse
from src.core.logger import logger

router = APIRouter()


@router.post(
    "/cars",
    response_model=CarCreateResponse,
    summary="Создать автомобиль",
    description="Создает запись о машине для текущего пользователя."
)
async def create_user_car(
        payload: CarCreateRequest,
        user: dict = Depends(jwt_token_validator)
):
    """
    Эндпоинт для создания автомобиля пользователя.

    Description:
    - Принимает payload с обязательными полями brand, model, year и опциональными mileage, color
    - Создает запись в таблице cars для текущего пользователя (user_id_owner берется из токена)

    Parameters:
    - **payload**: JSON с данными автомобиля
    - **user**: Данные текущего пользователя из токена (Depends(jwt_token_validator))

    Raises:
    - **HTTPException 400**: Если обязательные поля не переданы
    - **HTTPException 500**: Если произошла ошибка при работе с базой данных
    """
    user_id_owner = int(user["sub"])
    try:
        result = await create_car(payload.dict(), user_id_owner)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании машины для пользователя {user_id_owner}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось создать машину")



@router.get(
    "/list",
    response_model=CarListResponse,
    summary="Список автомобилей пользователя",
    description="Возвращает список всех автомобилей текущего пользователя."
)
async def list_user_cars(user: dict = Depends(jwt_token_validator)):
    """
    Эндпоинт для получения всех машин пользователя.

    Description:
    - Возвращает список всех машин, включая удалённые
    - Для текущего пользователя (user_id_owner берется из токена)

    Parameters:
    - **user**: Данные текущего пользователя из токена

    Raises:
    - **HTTPException 500**: Если произошла ошибка при работе с базой данных
    """
    user_id_owner = int(user["sub"])
    try:
        cars = await get_user_cars(user_id_owner)
        return {"cars": cars}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении списка машин пользователя {user_id_owner}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось получить список машин")


@router.put(
    "/cars/{car_id}",
    response_model=CarCreateResponse,
    summary="Обновить автомобиль",
    description="Обновляет запись о машине текущего пользователя."
)
async def update_user_car(
        car_id: int,
        payload: CarCreateRequest,
        user: dict = Depends(jwt_token_validator)
):
    """
    Эндпоинт для обновления автомобиля пользователя.

    Description:
    - Обновляет указанные поля: brand, model, year, mileage, color
    - Проверяет права владельца по user_id_owner из токена

    Parameters:
    - **car_id**: ID автомобиля для обновления
    - **payload**: JSON с обновляемыми полями
    - **user**: Данные текущего пользователя из токена

    Raises:
    - **HTTPException 400**: Если нет полей для обновления
    - **HTTPException 404**: Если машина не найдена или пользователь не владелец
    - **HTTPException 500**: Если произошла ошибка при работе с базой данных
    """
    user_id_owner = int(user["sub"])
    try:
        result = await update_car(car_id, user_id_owner, payload.dict())
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении машины {car_id} пользователя {user_id_owner}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось обновить машину")


@router.delete(
    "/cars/{car_id}",
    response_model=CarCreateResponse,
    summary="Удалить автомобиль",
    description="Логическое удаление автомобиля текущего пользователя."
)
async def delete_user_car(
        car_id: int,
        user: dict = Depends(jwt_token_validator)
):
    """
    Эндпоинт для логического удаления автомобиля пользователя.

    Description:
    - Устанавливает is_deleted = True, deleted_at = текущая дата и is_active = False
    - Проверяет права владельца по user_id_owner из токена

    Parameters:
    - **car_id**: ID автомобиля для удаления
    - **user**: Данные текущего пользователя из токена

    Raises:
    - **HTTPException 404**: Если машина не найдена или пользователь не владелец
    - **HTTPException 500**: Если произошла ошибка при работе с базой данных
    """
    user_id_owner = int(user["sub"])
    try:
        result = await delete_car(car_id, user_id_owner)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении машины {car_id} пользователя {user_id_owner}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось удалить машину")
