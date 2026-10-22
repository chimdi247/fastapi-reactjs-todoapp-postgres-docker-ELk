from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Always stored lower-cased (enforced by a CHECK constraint in the DB).
    email: Mapped[str] = mapped_column(String(255))

    password_hash: Mapped[str] = mapped_column(String(255))

    full_name: Mapped[Optional[str]] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(String(32), default="user", server_default="user")

    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    last_login_at: Mapped[Optional[datetime]]

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
