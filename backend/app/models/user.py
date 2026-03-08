from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    employee_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    department: Mapped[str] = mapped_column(String(128), index=True)
    position: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(32), default='employee', index=True)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)
