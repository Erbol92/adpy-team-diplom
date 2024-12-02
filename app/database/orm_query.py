"""Функции запросов в базу данных"""

import asyncio

from sqlalchemy import select, update, and_, delete

from app.database.engine import Base, engine, session_factory
from app.database.models import User, Candidate, FavoriteCandidate, Blacklist


async def orm_drop_tables():
    """ Удаляет все таблицы из базы данных """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def orm_create_tables():
    """ Создаёт новые таблицы в базе данных """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def orm_check_user_in_database(vk_user_id):
    """
    Проверяет наличие пользователя в таблице ``user``
    :param vk_user_id: Идентификатор пользователя вконтакте
    :return:
    """
    query = select(User.vk_id).where(User.vk_id == vk_user_id)
    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(query)
            return result.scalar_one_or_none()


async def orm_get_user_id(vk_user_id):
    """
    Возвращает значение поля ``user.user_id``
    :param vk_user_id: Идентификатор пользователя вконтакте
    :return:
    """
    query = select(User.user_id).where(User.vk_id == vk_user_id)
    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(query)
            return result.scalars().all()[0]


async def orm_check_user_searched(vk_user_id):
    """
    Проверяет значение поля ``user.searched``
    :param vk_user_id: Идентификатор пользователя вконтакте
    :return:
    """
    query = select(User.already_searched).where(User.vk_id == vk_user_id)
    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(query)
            return result.scalars().all()[0]


async def orm_set_user_searched(vk_user_id: int, flag: bool):
    """
    Устанавливает значение поля ``user.searched`` в flag
    :param vk_user_id: Идентификатор пользователя вконтакте
    :return:
    """
    query = update(User).where(User.vk_id == vk_user_id).values(already_searched=flag)
    async with session_factory() as session:
        async with session.begin():
            await session.execute(query)


async def orm_add_user(vk_id: int):
    """
    Добавление новую сущность в таблицу ``user``
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
    Добавляет новые сущности в таблицу ``candidate``
    :param vk_id_list: Список идентификаторов пользователей вконтакте
    :param user_id: Идентификатор пользователя приложения
    :return:
    """
    query = select(Candidate.vk_id).where(Candidate.user_id == user_id)
    all_candidate = []
    async with session_factory() as session:
        async with session.begin():
            check_list = await session.execute(query)
            existing_ids = check_list.scalars().all()
            for ids in vk_id_list:
                if ids not in existing_ids:
                    all_candidate.append(Candidate(vk_id=ids, user_id=user_id))
            session.add_all(all_candidate)
            await session.commit()


async def orm_add_favorite_candidate(user_id: int, candidate_id: int):
    """
    Добавляет кандидата в избранное
    :param user_id: Идентификатор пользователя
    :param candidate_id: Идентификатор кандидата
    :return:
    """

    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(
                select(FavoriteCandidate).where(
                    FavoriteCandidate.user_id == user_id,
                    FavoriteCandidate.candidate_id == candidate_id
                )
            )
            favorite_candidate = result.scalars().first()
            # Если запись не найдена, добавляем нового кандидата
            if favorite_candidate is None:
                favorite_candidate = FavoriteCandidate(user_id=user_id, candidate_id=candidate_id)
                session.add(favorite_candidate)
                await session.commit()
                created = True
            else:
                created = False
            return created

async def orm_add_candidate_to_blacklist(user_id: int, candidate_id: int):
    """
    Добавляет кандидата в чёрный список
    :param user_id: Идентификатор пользователя
    :param candidate_id: Идентификатор кандидата
    :return:
    """

    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(
                select(Blacklist).where(
                    Blacklist.user_id == user_id,
                    Blacklist.candidate_id == candidate_id
                )
            )
            blacklist = result.scalars().first()
            if blacklist is None:
                blacklist = Blacklist(user_id=user_id, candidate_id=candidate_id)
                session.add(blacklist)
                await session.commit()
                created = True
            else:
                created = False
            return created


async def orm_get_all_candidate(user_id: int):
    """
    Возвращает список полей ``candidate.vk_id``
    :param user_id: Идентификатор пользователя
    :return:
    """
    query = select(Candidate.vk_id).where(and_(Candidate.user_id == user_id, Candidate.skip == False))
    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(query)
            return result.scalars().all()


async def drop_all_candidate(user_id: int):
    """
    Очищает список полей ``candidate``
    :param user_id: Идентификатор пользователя
    :return:
    """
    async with session_factory() as session:
        async with session.begin():
            # Получаем идентификаторы кандидатов, которые связаны с FavoriteCandidate или Blacklist
            subquery = select(Candidate.candidate_id).where(
                (Candidate.candidate_id.in_(select(FavoriteCandidate.candidate_id))) |
                (Candidate.candidate_id.in_(select(Blacklist.candidate_id)))
            )

            # Удаляем кандидатов, которые не находятся в подзапросе
            query = delete(Candidate).where(Candidate.candidate_id.notin_(subquery))
            result = await session.execute(query)
            await session.commit()  # Подтверждаем изменения

            return result.rowcount



async def orm_get_candidate(vk_id: int):
    """
    Возвращает поле ``candidate.candidate_id`` у одной сущности
    :param vk_id: Идентификатор пользователя вконтакте
    :return:
    """
    query = select(Candidate.candidate_id).where(Candidate.vk_id == vk_id)
    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(query)
            return result.scalars().all()[0]


async def orm_set_candidate_skip(vk_user_id):
    """
    Устанавливает значение поля ``candidate.skip`` в True
    :param vk_user_id: Идентификатор пользователя вконтакте
    :return:
    """
    query = update(Candidate).where(Candidate.vk_id == vk_user_id).values(skip=True)
    async with session_factory() as session:
        async with session.begin():
            await session.execute(query)


async def main():
    await orm_drop_tables()
    await orm_create_tables()


if __name__ == '__main__':
    try:
        print(asyncio.run(main()))
    except Exception as e:
        print(e)
