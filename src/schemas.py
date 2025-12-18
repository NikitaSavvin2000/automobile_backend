# src/schemas.py
from pydantic import BaseModel, EmailStr

from typing import Optional, List, Dict
from typing import Literal
from datetime import datetime

class PermissionsResponse(BaseModel):
    permissions: List[str]


class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    verify_code: int


class SendCodeRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class SendChangeCodeRequest(BaseModel):
    email: EmailStr

class SendCodeResponse(BaseModel):
    message: str
    user_id: int


class RegistrationResponse(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str
    message: str = "Организация и суперюзер успешно зарегистрированы"


class UserResponse(BaseModel):
    login: str
    first_name: str
    last_name: str
    email: str
    access_level: str  # например, 'admin'
    permissions: List[str]


class GetUsersByOrgResponse(BaseModel):
    users: List[UserResponse]


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"]
    expires_in: int
    refresh_expires_in: int

class AuthRequest(BaseModel):
    email: str | EmailStr
    password: str


class UserAuthResponse(BaseModel):
    id: int
    roles: list[str]
    permissions: list[str]



class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int
    user: UserAuthResponse


class RolesResponse(BaseModel):
    roles: list[str]


class RegisterUserRequest(BaseModel):
    """
    Схема для запроса на регистрацию нового пользователя в организации.
    """
    login: str
    password: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str 

class RegisterUserResponse(BaseModel):
    """
    Схема для ответа на запрос регистрации нового пользователя.
    """
    success: bool
    user_id: int
    message: str


class LogoutRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    detail: str


class UserStatusChangeResponse(BaseModel):
    """
    Схема для ответа на запрос по изменению статуса пользователя из организации.
    """
    success: bool
    user_id: int
    message: str


class UserStatusChangeRequest(BaseModel):
    """
    Схема для ответа по изменению статуса пользователя из организации.
    """
    login_to_change: str


class AccessTokenResponse(BaseModel):
    user_id: int
    org_id: int
    roles: List[str]
    permissions: List[str]

class CarCreateRequest(BaseModel):
    brand: str
    model: str
    year: int
    mileage: Optional[int]
    color: Optional[str]

class CarCreateResponse(BaseModel):
    message: str
    car_id: int


class CarResponse(BaseModel):
    id: int
    user_id_owner: int
    brand: str
    model: str
    year: int
    mileage: Optional[int]
    color: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    is_active: bool
    is_deleted: bool

class CarListResponse(BaseModel):
    cars: List[CarResponse]


class CarRecordImageResponse(BaseModel):
    id: int
    link_to_s3: str

class CarRecordCreateResponse(BaseModel):
    record_id: int
    message: str
    images: Optional[List[CarRecordImageResponse]] = []


class CarRecordImageResponse(BaseModel):
    id: int
    url: str

class CarRecordDetailResponse(BaseModel):
    car_record_id: int
    name: str
    description: str
    record_date: str | None
    mileage: int | None
    service_place: str | None
    cost: float | None
    images: list[CarRecordImageResponse]