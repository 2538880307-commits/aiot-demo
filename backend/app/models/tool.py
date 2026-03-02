from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Tool(Base):
    __tablename__ = 'tools'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    tool_type: Mapped[str] = mapped_column(String(64), index=True)
    tool_name: Mapped[str] = mapped_column(String(128), index=True)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    team: Mapped[str] = mapped_column(String(128))
    image_url: Mapped[str] = mapped_column(String(2048), default='')
