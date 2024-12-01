"""Функции запросов в базу дан"""

from sqlalchemy import select, update

from app.database.engine import Base, engine, session_factory
from app.database.models import User, Candidate, FavoriteCandidate


async def orm_drop_tables():
    """ Удаляет все таблицы из базы данных """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def orm_create_tables():
    """ Создаёт новые таблицы в базе данных """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def orm_check_user_in_database(vk_user_id):
    query = select(User.vk_id).where(User.vk_id == vk_user_id)
    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(query)
            return result.scalar_one_or_none()


async def orm_get_user_id(vk_user_id):
    query = select(User.user_id).where(User.vk_id == vk_user_id)
    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(query)
            return result.scalars().all()


async def orm_check_user_searched(vk_user_id):
    query = select(User.already_searched).where(User.vk_id == vk_user_id)
    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(query)
            return result.scalars().all()[0]


async def orm_set_user_searched(vk_user_id):
    query = update(User).where(User.vk_id == vk_user_id).values(already_searched=True)
    async with session_factory() as session:
        async with session.begin():
            await session.execute(query)


async def orm_add_user(vk_id: int):
    """
    Добавление нового пользователя
    :param vk_id: Идентификатор пользователя вконтакте
    :return:
    """
    user = User(
        vk_id=vk_id
    )
    async with session_factory() as session:
        async with session.begin():
            session.add(user)
            await session.commit()


async def orm_add_all_candidate(vk_id_list: list[int], user_id: int):
    """
    Добавление нескольких новых кандидатов
    :param vk_id_list: Идентификатор кандидата
    :param user_id: Идентификатор пользователя
    :return:
    """
    all_candidate = []
    for ids in vk_id_list:
        all_candidate.append(Candidate(vk_id=ids, user_id=user_id))

    async with session_factory() as session:
        async with session.begin():
            session.add_all(all_candidate)
            await session.commit()


async def orm_add_favorite_candidate(user_id: int, candidate_id: int):
    """
    Связь между пользователем и кандидатом
    :param user_id: Идентификатор пользователя
    :param candidate_id: Идентификатор кандидата
    :return:
    """
    favorite_candidate = FavoriteCandidate(user_id=user_id, candidate_id=candidate_id)

    async with session_factory() as session:
        async with session.begin():
            session.add(favorite_candidate)
            await session.commit()


async def orm_get_all_candidate(user_id: int):
    query = select(Candidate.vk_id).where(Candidate.user_id == user_id)
    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(query)
            return result.scalars().all()
