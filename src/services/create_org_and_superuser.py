# src/services/create_org_and_superuser.py

from logging import getLogger
from fastapi import HTTPException, status
from sqlalchemy import select, update, insert

from src.utils.jwt_utils import create_access_token, create_refresh_token
from src.models.user_models import RefreshToken
from src.session import db_manager
from src.models.user_models import Organization, User, Role, UserRoles
from src.schemas import RegistrationRequest, SendCodeRequest
from src.db_clients.config import RolesConfig
from src.core.security.password import  hash_password
from src.utils.code_sendler import send_email
import random
from datetime import datetime, timedelta, timezone
from services.auth_service import auth, logout
from src.core.security.email import encrypt_email, decrypt_email

logger = getLogger(__name__)
roles = RolesConfig()


async def check_login_exists(session, login: str):
    result = await session.execute(select(User).where(User.login == login))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Суперюзер с логином {login} уже существует"
        )

# async def check_email_exists(session, email: str):
#     result = await session.execute(
#         select(User).where(
#             User.email == email,
#             User.is_active == True,
#             User.is_deleted == False
#         )
#     )
#     if result.scalars().first():
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=f"Пользователь с email {email} уже существует"
#         )
#


async def check_email_exists(session, email: str):
    result = await session.execute(
        select(User).where(User.email == email, User.is_deleted == False)
    )
    user = result.scalars().first()

    if user:
        email_exist = True
        is_active = user.is_active
        return email_exist, is_active
    else:
        email_exist = False
        is_active = False
        return email_exist, is_active

async def check_org_exists(session, email: str):
    result = await session.execute(select(Organization).where(Organization.email == email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Организация с email {email} уже существует"
        )

async def check_user_email_exists(session, email: str):
    result = await session.execute(select(User).where(User.email == email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Суперюзер с email {email} уже существует"
        )

async def create_organization(session, name: str, email: str) -> Organization:
    org = Organization(name=name, email=email, owner_id=None)
    session.add(org)
    await session.flush()
    return org


async def create_user_record(session, name: str, email: str, code: int, expires_at, plain_password: str):
    hashed_pwd = hash_password(plain_password)

    user = User(
        name=name,
        email=email,
        is_active=False,
        verify_code=code,
        code_date_expired=expires_at,
        password=hashed_pwd,
        role_id=2,
    )

    session.add(user)
    await session.flush()
    await session.commit()
    return user.id

async def change_password_by_email(email: str, plain_password: str):
    current_date = datetime.now(timezone.utc)
    hashed_pwd = hash_password(plain_password)

    async with db_manager.get_db_session() as session:
        result = await session.execute(
            select(User.id)
            .where(
                User.email == email,
                User.is_active == True,
                User.is_deleted == False
            )
        )
        user_row = result.first()

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Активный пользователь с email {email} не найден"
            )

        user_id = user_row[0]

        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(password=hashed_pwd, updated_at=current_date)
        )
        await session.commit()

        return True, "Пароль успешно изменён"


async def update_user_verify_code(session, email: str, new_code: int, new_expires_at, is_active: bool = False):
    result = await session.execute(
        select(User).where(
            User.email == email,
            User.is_active == is_active,
            User.is_deleted == False
        )
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Пользователь с email {email} не найден или уже активен"
        )

    user.verify_code = new_code
    user.code_date_expired = new_expires_at

    session.add(user)
    await session.flush()
    await session.commit()

    return user.id



async def create_superuser(session, org_id: int, payload: RegistrationRequest) -> User:
    pass


async def assign_owner(session, org_id: int, superuser_id: int):
    await session.execute(
        update(Organization).where(Organization.id == org_id).values(owner_id=superuser_id)
    )

async def assign_superuser_role(session, superuser_id: int):
    role_result = await session.execute(
        select(Role).where(Role.name == roles.SUPERUSER)
    )
    role_obj = role_result.scalars().first()
    if not role_obj:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Роль SUPERUSER не найдена"
        )

    await session.execute(
        insert(UserRoles).values(user_id=superuser_id, role_id=role_obj.id)
    )


async def generate_code(digits: int, expire_minutes: int):
    code = str(random.randint(10 ** (digits - 1), 10 ** digits - 1)).zfill(digits)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    return code, expires_at


async def send_change_code(payload: SendCodeRequest) -> dict:
    expire_minutes = 15
    code, expires_at = await generate_code(digits=4, expire_minutes=expire_minutes)

    email = payload.email
    email_encrypt = encrypt_email(email=email)

    try:
        async with db_manager.get_db_session() as session:
            email_exist, is_active = await check_email_exists(session=session, email=email_encrypt)
            if email_exist and is_active:
                user_id =  await update_user_verify_code(
                    session=session, email=email_encrypt, new_code=code, new_expires_at=expires_at, is_active=True)
            elif email_exist and not is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Пользователь с почтой {email} не активен, пройдите регистрацию"
                )
            elif not email_exist and not is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Пользователь с почтой {email} не существует"
                )
            message = await send_email(recipient_emails=email, code=code, expire_minutes=expire_minutes)
            return {"message": message, "user_id": user_id}

    except HTTPException:
        raise

async def send_verify_code(payload: SendCodeRequest) -> dict:
    expire_minutes = 15
    code, expires_at = await generate_code(digits=4, expire_minutes=expire_minutes)

    email = payload.email
    email_encrypt = encrypt_email(email=email)

    try:
        async with db_manager.get_db_session() as session:
            email_exist, is_active = await check_email_exists(session=session, email=email_encrypt)
            if email_exist and is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Пользователь с почтой {email} уже существует"
                )
            elif email_exist and not is_active:
                user_id =  await update_user_verify_code(
                    session=session, email=email_encrypt, new_code=code, new_expires_at=expires_at)

            elif not email_exist and not is_active:
                user_id =  await create_user_record(
                    session=session, name=payload.name, email=email_encrypt,
                    code=code, expires_at=expires_at, plain_password=payload.password
                )
            message = await send_email(recipient_emails=email, code=code, expire_minutes=expire_minutes)
            return {"message": message, "user_id": user_id}

    except HTTPException:
        raise


async def func_verify_code(code: str, email: str):
    current_date = datetime.now(timezone.utc)
    async with db_manager.get_db_session() as session:
        result = await session.execute(
            select(User.verify_code, User.code_date_expired, User.is_active)
            .where(User.email == email, User.is_deleted == False)
        )
        user_row = result.first()

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с email {email} не найден"
            )


        verify_code, code_date_expired, is_active = user_row
        is_verified = str(verify_code) == str(code)
        if not is_active:
            was_active = False
            if not is_verified:
                return is_verified, was_active, "Неверный код"

            if code_date_expired is None:
                return False, was_active,  "Срок действия кода истек"

            # Приводим к UTC, если нет информации о таймзоне
            if code_date_expired.tzinfo is None:
                code_date_expired = code_date_expired.replace(tzinfo=timezone.utc)

            if current_date < code_date_expired:
                return True, was_active,  "Код подтвержден"
            else:
                return False, was_active,  "Срок действия кода истек"
        else:
            was_active = True
            return is_verified, was_active, "Пользовтель уже активен"



async def activate_user_by_email(email: str):
    current_date = datetime.now(timezone.utc)
    async with db_manager.get_db_session() as session:
        result = await session.execute(
            select(User.id, User.is_active)
            .where(User.email == email, User.is_deleted == False)
        )
        user_row = result.first()

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с email {email} не найден"
            )

        user_id, is_active = user_row
        if is_active:
            return True, "Пользователь уже активен"

        print("Привет, я тут")
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=True, updated_at=current_date)
        )
        await session.commit()
        return True, "Пользователь успешно активирован"


async def change_password(payload: RegistrationRequest) -> dict:
    verify_code = payload.verify_code
    email = payload.email
    email_encrypt = encrypt_email(email=email)
    password = payload.password

    is_verified, was_active, message = await func_verify_code(code=verify_code, email=email_encrypt)
    try:
        if is_verified and was_active:
            is_active, message = await change_password_by_email(email=email_encrypt, plain_password=password)
            return {"message": message}
        elif not is_verified and was_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Код не прошел проверку попробуйте снова"
            )
        elif is_verified and not was_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Пользователь с почтой {email} не еще прошел регистрацию"
            )
    except HTTPException:
        raise


async def create_user(payload: RegistrationRequest) -> dict:
    verify_code = payload.verify_code
    email = payload.email
    email_encrypt = encrypt_email(email=email)
    password = payload.password

    is_verified, was_active, message = await func_verify_code(code=verify_code, email=email_encrypt)
    try:
        if is_verified and not was_active:
            is_active, message = await activate_user_by_email(email=email_encrypt)
            if is_active:
                res = await auth(email=email_encrypt, password=password)
                return res
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Не известная ошибка попробуйте снова"
                )
        elif not is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        else:
            res = await auth(email=email_encrypt, password=password)
            return res
    except HTTPException:
        raise
