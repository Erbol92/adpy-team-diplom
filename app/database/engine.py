"""Модуль предназначен для конфигурации базы данных"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import DSN
from app.database.models import Base


engine = create_async_engine(DSN, echo=False)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def drop_tables():
    """ Удаляет все таблицы из базы данных """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def create_tables():
    """ Создаёт новые таблицы в базе данных """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
