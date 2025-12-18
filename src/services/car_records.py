from logging import getLogger
from fastapi import HTTPException, status
from src.utils.s3_loader import upload_image_to_s3, load_image_from_s3
from src.models.user_models import Car, CarRecord, CarRecordImage
from io import BytesIO
from typing import List, Tuple

from typing import List
from fastapi import UploadFile, HTTPException
from sqlalchemy import insert, select, update
from datetime import datetime, timezone
from src.session import db_manager
from src.models.user_models import CarRecordImage
import os
import asyncio
from datetime import datetime
from fastapi import HTTPException, status

logger = getLogger(__name__)


async def parse_date_any_format(date_str: str) -> datetime | None:
    if not date_str:
        return None

    date_formats = [
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%d.%m.%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",       # американский формат
        "%m-%d-%Y",       # американский формат с тире
        "%Y-%m-%dT%H:%M:%S",
        "%Y.%m.%dT%H:%M:%S",
        "%d.%m.%YT%H:%M:%S",
        "%d-%m-%YT%H:%M:%S",
        "%m/%d/%YT%H:%M:%S",
        "%m-%d-%YT%H:%M:%S",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось распознать дату: {date_str}. Ожидаемые форматы: YYYY-MM-DD, DD.MM.YYYY, YYYY.MM.DD, MM/DD/YYYY, с/без времени"
        )


async def create_car_record(payload: dict, user_id_owner: int, car_id: int, files: list[UploadFile] | None = None) -> dict:
    record_type = payload.get("record_type")
    name = payload.get("name")
    description = payload.get("description")
    mileage = payload.get("mileage")
    service_place = payload.get("service_place")
    cost = payload.get("cost")

    if not record_type or not name or not description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Обязательные поля record_type, name или description не переданы"
        )

    record_date_str = payload.get("record_date")
    record_date_obj = None
    if record_date_str:
        record_date_obj = await parse_date_any_format(date_str=record_date_str)

    try:
        async with db_manager.get_db_session() as session:
            car_exists = await session.execute(
                select(Car.id).where(
                    Car.id == car_id,
                    Car.user_id_owner == user_id_owner,
                    Car.is_deleted == False
                )
            )
            if not car_exists.scalar():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"У пользователя нет машины с id={car_id}"
                )

            stmt = insert(CarRecord).values(
                user_id_owner=user_id_owner,
                car_id=car_id,
                record_type=record_type[:100],
                name=name[:255],
                description=description,
                record_date=record_date_obj,
                mileage=mileage,
                service_place=service_place,
                cost=cost,
                created_at=datetime.now(timezone.utc),
                is_active=True,
                is_deleted=False
            )

            result = await session.execute(stmt)
            await session.commit()
            record_id = result.inserted_primary_key[0]

            if files:
                files_content = [(file.filename, await file.read()) for file in files]
                asyncio.create_task(
                    upload_car_record_images(
                        car_record_id=record_id,
                        car_id=car_id,
                        owner_user_id=user_id_owner,
                        files_content=files_content
                    )
                )


            return {"message": "Car record created", "record_id": record_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании записи для машины: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать запись для машины"
        )


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

async def upload_car_record_images(
        car_record_id: int,
        car_id: int,
        owner_user_id: int,
        files_content: List[Tuple[str, bytes]],  # [(filename, content), ...]
        folder: str = "car_records"
) -> List[str]:
    uploaded_keys = []

    try:
        async with db_manager.get_db_session() as session:
            for file_name, content in files_content:
                s3_key = await upload_image_to_s3(file_name, content, folder)

                stmt = insert(CarRecordImage).values(
                    car_record_id=car_record_id,
                    car_id=car_id,
                    owner_user_id=owner_user_id,
                    link_to_s3=s3_key,
                    created_at=datetime.now(timezone.utc),
                    is_active=True,
                    is_deleted=False
                )
                await session.execute(stmt)
                uploaded_keys.append(s3_key)

            await session.commit()
            return uploaded_keys

    except Exception as e:
        logger.error(f"Ошибка при загрузке изображений для car_record_id={car_record_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось загрузить изображения")


async def delete_car_record(record_id: int, user_id_owner: int) -> dict:
    try:
        async with db_manager.get_db_session() as session:
            exists = await session.execute(
                select(CarRecord.id).where(
                    CarRecord.id == record_id,
                    CarRecord.user_id_owner == user_id_owner,
                    CarRecord.is_deleted == False
                )
            )
            if not exists.scalar():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"У пользователя нет записи автомобиля с id={record_id}"
                )

            stmt = (
                update(CarRecord)
                .where(
                    CarRecord.id == record_id,
                    CarRecord.user_id_owner == user_id_owner
                )
                .values(
                    is_deleted=True,
                    is_active=False,
                    deleted_at=datetime.now(timezone.utc)
                )
            )

            await session.execute(stmt)
            await session.commit()
            return {"message": "Car record deleted", "record_id": record_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении записи автомобиля: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить запись автомобиля"
        )

async def get_car_records(
        user_id_owner: int,
        car_id: int
) -> list[dict]:
    try:
        async with db_manager.get_db_session() as session:
            car_exists = await session.execute(
                select(Car.id).where(
                    Car.id == car_id,
                    Car.user_id_owner == user_id_owner,
                    Car.is_deleted == False
                )
            )
            if not car_exists.scalar():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"У пользователя нет машины с id={car_id}"
                )

            result = await session.execute(
                select(
                    CarRecord.id,
                    CarRecord.user_id_owner,
                    CarRecord.car_id,
                    CarRecord.record_type,
                    CarRecord.name,
                    CarRecord.record_date,
                    CarRecord.mileage,
                    CarRecord.service_place,
                    CarRecord.cost
                ).where(
                    CarRecord.car_id == car_id,
                    CarRecord.user_id_owner == user_id_owner,
                    CarRecord.is_deleted == False,
                    CarRecord.is_active == True
                ).order_by(CarRecord.created_at.desc())
            )

            rows = result.all()

            return [
                {
                    "record_id": r.id,
                    "user_id_owner": r.user_id_owner,
                    "car_id": r.car_id,
                    "record_type": r.record_type,
                    "name": r.name,
                    "record_date": r.record_date,
                    "mileage": r.mileage,
                    "service_place": r.service_place,
                    "cost": r.cost
                }
                for r in rows
            ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Ошибка при получении записей автомобиля car_id={car_id} пользователя {user_id_owner}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить записи автомобиля"
        )
async def get_car_record_detail(user_id_owner: int, car_id: int, car_record_id: int) -> dict:
    try:
        async with db_manager.get_db_session() as session:
            record_result = await session.execute(
                select(CarRecord).where(
                    CarRecord.id == car_record_id,
                    CarRecord.car_id == car_id,
                    CarRecord.user_id_owner == user_id_owner,
                    CarRecord.is_deleted == False
                )
            )
            record = record_result.scalar_one_or_none()
            if not record:
                raise HTTPException(status_code=404, detail=f"Запись с id={car_record_id} не найдена")

            images_result = await session.execute(
                select(CarRecordImage.id, CarRecordImage.link_to_s3).where(
                    CarRecordImage.car_record_id == car_record_id,
                    CarRecordImage.is_deleted == False
                )
            )
            file_keys = images_result.all()

        images = [
            {"id": img_id, "url": await load_image_from_s3(link)}
            for img_id, link in file_keys
        ]

        return {
            "car_record_id": record.id,
            "name": record.name,
            "description": record.description,
            "record_date": record.record_date.isoformat() if record.record_date else None,
            "mileage": record.mileage,
            "service_place": record.service_place,
            "cost": record.cost,
            "images": images
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении записи машины: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось получить запись машины")


async def update_car_record(
        payload: dict,
        user_id_owner: int,
        car_id: int,
        car_record_id: int,
        files: list[UploadFile] | None = None
) -> dict:
    record_type = payload.get("record_type")
    name = payload.get("name")
    description = payload.get("description")
    mileage = payload.get("mileage")
    service_place = payload.get("service_place")
    cost = payload.get("cost")

    if not record_type or not name or not description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Обязательные поля record_type, name или description не переданы"
        )

    record_date_str = payload.get("record_date")
    record_date_obj = None
    if record_date_str:
        record_date_obj = await parse_date_any_format(date_str=record_date_str)

    try:
        async with db_manager.get_db_session() as session:
            car_record_result = await session.execute(
                select(CarRecord).where(
                    CarRecord.id == car_record_id,
                    CarRecord.car_id == car_id,
                    CarRecord.user_id_owner == user_id_owner,
                    CarRecord.is_deleted == False
                )
            )
            car_record = car_record_result.scalar_one_or_none()
            if not car_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Запись с id={car_record_id} не найдена"
                )

            update_stmt = (
                update(CarRecord)
                .where(CarRecord.id == car_record_id)
                .values(
                    record_type=record_type[:100],
                    name=name[:255],
                    description=description,
                    record_date=record_date_obj,
                    mileage=mileage,
                    service_place=service_place,
                    cost=cost,
                    updated_at=datetime.now(timezone.utc)
                )
            )

            await session.execute(update_stmt)
            await session.commit()

            if files:
                files_content = [(file.filename, await file.read()) for file in files]
                asyncio.create_task(
                    upload_car_record_images(
                        car_record_id=car_record_id,
                        car_id=car_id,
                        owner_user_id=user_id_owner,
                        files_content=files_content
                    )
                )

            return {"message": "Car record updated", "record_id": car_record_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении записи для машины: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить запись для машины"
        )


async def delete_car_record_image(
        user_id: int,
        car_record_id: int,
        image_id: int
) -> dict:
    try:
        async with db_manager.get_db_session() as session:
            result = await session.execute(
                select(CarRecordImage).where(
                    CarRecordImage.id == image_id,
                    CarRecordImage.car_record_id == car_record_id,
                    CarRecordImage.owner_user_id == user_id,
                    CarRecordImage.is_deleted == False
                )
            )
            image = result.scalar_one_or_none()
            if not image:
                raise HTTPException(status_code=404, detail="Изображение не найдено или доступ запрещён")

            await session.execute(
                update(CarRecordImage)
                .where(CarRecordImage.id == image_id)
                .values(is_deleted=True, deleted_at=datetime.utcnow())
            )
            await session.commit()

        return {"status": "success", "message": "Изображение удалено"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении изображения {image_id} записи {car_record_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось удалить изображение")
