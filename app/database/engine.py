"""Модуль предназначен для конфигурации базы данных"""

from typing import Annotated

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, mapped_column

from app.config import DSN


engine = create_async_engine(DSN, echo=True)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

int_pk = Annotated[int, mapped_column(primary_key=True)]


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
