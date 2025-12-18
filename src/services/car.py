from logging import getLogger
from fastapi import HTTPException, status
from sqlalchemy import insert
from datetime import datetime, timezone
from sqlalchemy import select, insert, update


from src.session import db_manager
from src.models.user_models import Car

logger = getLogger(__name__)

async def create_car(payload: dict, user_id_owner: int) -> dict:
    """
    Создаёт запись о машине в таблице cars.
    payload должен содержать ключи:
        brand, model, year, mileage (опционально), color (опционально)
    """
    brand = payload.get("brand")
    model = payload.get("model")
    year = payload.get("year")
    mileage = payload.get("mileage")
    color = payload.get("color")

    if not brand or not model or year is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Обязательные поля brand, model или year не переданы"
        )


    try:
        async with db_manager.get_db_session() as session:
            stmt = insert(Car).values(
                user_id_owner=user_id_owner,
                brand=brand[:20],
                model=model[:20],
                year=year,
                mileage=mileage,
                color=color,
                created_at=datetime.now(timezone.utc),
                is_active=True,
                is_deleted=False
            )
            result = await session.execute(stmt)
            await session.commit()
            car_id = result.inserted_primary_key[0]
            return {"message": "Car created", "car_id": car_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании машины: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать машину"
        )


async def update_car(car_id: int, user_id_owner: int, payload: dict) -> dict:
    """
    Обновляет запись о машине в таблице cars.
    Можно обновлять: brand, model, year, mileage, color
    car_id и user_id_owner используются для проверки прав владельца.
    """
    fields_to_update = {}
    if "brand" in payload and payload["brand"]:
        fields_to_update["brand"] = payload["brand"][:20]
    if "model" in payload and payload["model"]:
        fields_to_update["model"] = payload["model"][:20]
    if "year" in payload and payload["year"]:
        fields_to_update["year"] = payload["year"]
    if "mileage" in payload:
        fields_to_update["mileage"] = payload["mileage"]
    if "color" in payload:
        fields_to_update["color"] = payload["color"]

    if not fields_to_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет полей для обновления"
        )

    fields_to_update["updated_at"] = datetime.now(timezone.utc)

    try:
        async with db_manager.get_db_session() as session:
            stmt = (
                update(Car)
                .where(Car.id == car_id, Car.user_id_owner == user_id_owner, Car.is_deleted == False)
                .values(**fields_to_update)
            )
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Машина не найдена или нет прав на изменение"
                )
            await session.commit()
            return {"message": "Car updated", "car_id": car_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении машины: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить машину"
        )

async def delete_car(car_id: int, user_id_owner: int) -> dict:
    """
    Логическое удаление записи о машине.
    Устанавливает is_deleted = True и deleted_at = текущая дата.
    Проверяет права владельца.
    """
    try:
        async with db_manager.get_db_session() as session:
            stmt = (
                update(Car)
                .where(Car.id == car_id, Car.user_id_owner == user_id_owner, Car.is_deleted == False)
                .values(is_deleted=True, deleted_at=datetime.now(timezone.utc), is_active=False)
            )
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Машина не найдена или нет прав на удаление"
                )
            await session.commit()
            return {"message": "Car deleted", "car_id": car_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении машины: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить машину"
        )

async def get_user_cars(user_id_owner: int) -> list[dict]:
    """
    Возвращает список всех активных и не удалённых машин пользователя.
    """
    try:
        async with db_manager.get_db_session() as session:
            stmt = select(Car).where(
                Car.user_id_owner == user_id_owner,
                Car.is_active == True,
                Car.is_deleted == False
            )
            result = await session.execute(stmt)
            cars = result.scalars().all()
            return [
                {
                    "id": car.id,
                    "user_id_owner": car.user_id_owner,
                    "brand": car.brand,
                    "model": car.model,
                    "year": car.year,
                    "mileage": car.mileage,
                    "color": car.color,
                    "created_at": car.created_at,
                    "updated_at": car.updated_at,
                    "deleted_at": car.deleted_at,
                    "is_active": car.is_active,
                    "is_deleted": car.is_deleted
                }
                for car in cars
            ]
    except Exception as e:
        logger.error(f"Ошибка при получении списка машин: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить список машин"
        )
