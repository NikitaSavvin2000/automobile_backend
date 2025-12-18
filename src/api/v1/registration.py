# src/api/v1/registration.py
from fastapi import APIRouter, HTTPException, Body, status
from src.schemas import RegistrationRequest, RegistrationResponse, SendCodeRequest, SendCodeResponse, SendChangeCodeRequest
from src.services.create_org_and_superuser import create_user, send_verify_code, send_change_code, change_password
from src.core.logger import logger


router = APIRouter()


@router.post(
    "/user",
    status_code=status.HTTP_201_CREATED, 
    # response_model=RegistrationResponse,
    summary="Register organization and superuser",
    description="Создает нового юзера"
)

async def register_user(
    payload: RegistrationRequest = Body(
        ...,
        example={
            "email": "savvin.nikita.work@yandex.ru",
            "password": "test!",
            "verify_code": 100,
        },
    )
):
    """
    Эндпоинт для регистрации новой организации и её первого суперюзера.

    Description:
    - Создает запись в таблице organizations с указанной информацией.
    - Создает суперпользователя в таблице users, связанного с новой организацией.
    - Назначает новому пользователю роль superuser.
    - Возвращает информацию о созданной организации, пользователе и токены доступа.

    Raises:
    - **HTTPException 409**: Если организация или суперпользователь с такими данными уже существуют.
    - **HTTPException 422**: Если входные данные невалидны.
    - **HTTPException 500**: Если произошла ошибка при работе с базой данных.
    """

    try:
        result = await create_user(payload)
        return result
    except HTTPException:
        raise




@router.post(
    "/send_reg_code",
    status_code=status.HTTP_201_CREATED,
    response_model=SendCodeResponse,
    summary="Register organization and superuser",
    description="Создает нового юзера"
)

async def send_code_func(
        payload: SendCodeRequest = Body(
            ...,
            example={
                "name": "Никита Саввин",
                "email": "savvin.nikita.work@yandex.ru",
                "password": "test!",
            },
        )
):
    """
    Эндпоинт для регистрации новой организации и её первого суперюзера.

    Description:
    - Создает запись в таблице organizations с указанной информацией.
    - Создает суперпользователя в таблице users, связанного с новой организацией.
    - Назначает новому пользователю роль superuser.
    - Возвращает информацию о созданной организации, пользователе и токены доступа.

    Raises:
    - **HTTPException 409**: Если организация или суперпользователь с такими данными уже существуют.
    - **HTTPException 422**: Если входные данные невалидны.
    - **HTTPException 500**: Если произошла ошибка при работе с базой данных.
    """

    try:
        massage = await send_verify_code(payload)
        return massage
    except HTTPException:
        raise



@router.post(
    "/send_change_code",
    status_code=status.HTTP_201_CREATED,
    response_model=SendCodeResponse,
    summary="Register organization and superuser",
    description="Создает нового юзера"
)

async def send_change_code_func(
        payload: SendChangeCodeRequest = Body(
            ...,
            example={
                "email": "savvin.nikita.work@yandex.ru",
            },
        )
):
    """
    Эндпоинт для регистрации новой организации и её первого суперюзера.

    Description:
    - Создает запись в таблице organizations с указанной информацией.
    - Создает суперпользователя в таблице users, связанного с новой организацией.
    - Назначает новому пользователю роль superuser.
    - Возвращает информацию о созданной организации, пользователе и токены доступа.

    Raises:
    - **HTTPException 409**: Если организация или суперпользователь с такими данными уже существуют.
    - **HTTPException 422**: Если входные данные невалидны.
    - **HTTPException 500**: Если произошла ошибка при работе с базой данных.
    """

    try:
        massage = await send_change_code(payload)
        return massage
    except HTTPException:
        raise


@router.post(
    "/change_password",
    status_code=status.HTTP_201_CREATED,
    # response_model=RegistrationResponse,
    summary="Изменение пароля",
    description="Изменение пароля"
)

async def func_change_password(
        payload: RegistrationRequest = Body(
            ...,
            example={
                "email": "savvin.nikita.work@yandex.ru",
                "password": "test!",
                "verify_code": 100,
            },
        )
):
    """
    Эндпоинт для регистрации новой организации и её первого суперюзера.

    Description:
    - Создает запись в таблице organizations с указанной информацией.
    - Создает суперпользователя в таблице users, связанного с новой организацией.
    - Назначает новому пользователю роль superuser.
    - Возвращает информацию о созданной организации, пользователе и токены доступа.

    Raises:
    - **HTTPException 409**: Если организация или суперпользователь с такими данными уже существуют.
    - **HTTPException 422**: Если входные данные невалидны.
    - **HTTPException 500**: Если произошла ошибка при работе с базой данных.
    """

    try:
        result = await change_password(payload)
        return result
    except HTTPException:
        raise