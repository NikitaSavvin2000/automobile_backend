# src/models/user_model.py
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db_clients.config import db_settings
from src.models.base_model import ORMBase
from src.models.organization_models import Organization  # noqa: E402
from decimal import Decimal

# Таблица связи многие-ко-многим для пользователей и ролей
UserRoles = Table(
    db_settings.tables.USER_ROLES,
    ORMBase.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

# Таблица связи многие-ко-многим для ролей и разрешений
RolePermissions = Table(
    db_settings.tables.ROLE_PERMISSIONS,
    ORMBase.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
)


class RefreshToken(ORMBase):
    __tablename__ = db_settings.tables.REFRESH_TOKENS

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    token: Mapped[str] = mapped_column(String)
    jti: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    # user: Mapped['User'] = relationship('User', back_populates='refresh_tokens')



class Permission(ORMBase):
    __tablename__ = db_settings.tables.PERMISSIONS

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    can_create: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_update: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_activate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    role: Mapped["Role"] = relationship("Role", back_populates="permissions", lazy="joined")



#
# class Permission(ORMBase):
#     __tablename__ = db_settings.tables.PERMISSIONS
#
#     code: Mapped[str] = mapped_column(String)
#     description: Mapped[str | None] = mapped_column(Text)
#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    # roles: Mapped[list['Role']] = relationship(
    #     'Role',
    #     secondary=RolePermissions,
    #     back_populates='permissions',
    # )



class Role(ORMBase):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    users: Mapped[list["User"]] = relationship("User", back_populates="role")
    permissions: Mapped[list["Permission"]] = relationship("Permission", back_populates="role")



class User(ORMBase):
    __tablename__ = db_settings.tables.USERS

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String)
    password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    last_activity: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"))
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")

    verify_code: Mapped[str | None] = mapped_column(String)

    code_date_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cars: Mapped[list["Car"]] = relationship("Car", back_populates="user_owner")
    car_records: Mapped[list["CarRecord"]] = relationship("CarRecord", back_populates="user_owner")
    images: Mapped[list["CarRecordImage"]] = relationship("CarRecordImage", back_populates="owner_user")



class Car(ORMBase):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id_owner: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user_owner: Mapped["User"] = relationship("User", back_populates="cars", lazy="joined")

    brand: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str] = mapped_column(String(20), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    mileage: Mapped[int | None] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    records: Mapped[list["CarRecord"]] = relationship("CarRecord", back_populates="car")
    images: Mapped[list["CarRecordImage"]] = relationship("CarRecordImage", back_populates="car")



class CarRecord(ORMBase):
    __tablename__ = "car_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id_owner: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user_owner: Mapped["User"] = relationship("User", back_populates="car_records", lazy="joined")
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), nullable=False)
    car: Mapped["Car"] = relationship("Car", back_populates="records", lazy="joined")

    record_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    record_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mileage: Mapped[int | None] = mapped_column(Integer)
    service_place: Mapped[str | None] = mapped_column(String(255))
    cost: Mapped[float | None] = mapped_column(Numeric)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    images: Mapped[list["CarRecordImage"]] = relationship("CarRecordImage", back_populates="car_record")


class CarRecordImage(ORMBase):
    __tablename__ = "car_records_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    car_record_id: Mapped[int] = mapped_column(ForeignKey("car_records.id"), nullable=False)
    car_record: Mapped["CarRecord"] = relationship("CarRecord", back_populates="images", lazy="joined")

    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), nullable=False)
    car: Mapped["Car"] = relationship("Car", back_populates="images", lazy="joined")

    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner_user: Mapped["User"] = relationship("User", back_populates="images", lazy="joined")

    link_to_s3: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class Tables:
    def __init__(self):
        self.User = User
        self.Role = Role
        self.Permission = Permission
        self.RefreshToken = RefreshToken
        self.UserRoles = UserRoles
        self.RolePermissions = RolePermissions
