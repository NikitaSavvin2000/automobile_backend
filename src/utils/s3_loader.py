import os
import uuid
import boto3
from botocore.client import Config
from fastapi import UploadFile, HTTPException
from src.core.logger import logger

# logger = logger("s3_upload")

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

ALLOWED_EXTENSIONS = {".png", ".jpeg", ".jpg"}

async def upload_image_to_s3(file_name: str, content: bytes, folder: str = "images") -> str:
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат изображения")

    unique_name = f"{uuid.uuid4().hex}{ext}"
    s3_key = f"{folder}/{unique_name}"

    try:
        logger.info(f"Начало загрузки изображения в S3: {unique_name}")
        s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=content)
        logger.info(f"Изображение успешно загружено в S3: {s3_key}")
        return s3_key
    except Exception as e:
        logger.error(f"Ошибка при загрузке изображения в S3: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке изображения в S3")

async def load_image_from_s3(file_key: str) -> str:
    try:
        logger.info(f"Генерация presigned URL для S3: {file_key}")
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": file_key},
            ExpiresIn=3600
        )
        return url
    except Exception as e:
        logger.error(f"Ошибка при генерации presigned URL для S3: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении изображения из S3")
