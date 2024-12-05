"""Menu processing"""

from app.bot.core import send_choose_message, user_data, search_candidate, search_users, send_message, \
    search_candidate_bigquery, send_start_message
from app.database.orm_query import get_user_favorite_candidate, get_user_blacklist_candidate
from app.database.orm_query import orm_add_all_candidate, orm_get_user_id, orm_get_all_candidate, drop_all_candidate
from app.database.orm_query import orm_get_candidate, orm_add_favorite_candidate, orm_add_candidate_to_blacklist
from app.database.orm_query import orm_set_candidate_skip
from app.utils.paginator import Paginator


class MenuProcessing:
    """Класс для организации меню"""

    def __init__(self, user_vk_id: int = 0):
        self.user_vk_id = user_vk_id
        self.paginator = None
        self.current_candidate = 0
        self.pages = None
        self.city = None
        self.sex = None
        self.bdate = None

    def set_user_vk_id(self, vk_id: int):
        """
        Устанавливает значение для атрибута ``user_vk_id``
        :param vk_id: Идентификатор пользователя вконтакте
        :return:
        """
        self.user_vk_id = vk_id

    def set_paginator(self) -> None:
        """
        Устанавливает значение для атрибута ``paginator``
        :return:
        """
        self.paginator = Paginator(self.pages)

    def update_city(self, new_city: str):
        """
        Устанавливает новое значение для атрибута ``city``
        :param new_city:
        :return:
        """
        self.city = new_city

    def __set_current_candidate(self, candidate: int):
        """
        Устанавливает значение для атрибута ``current_candidate``
        :param candidate:
        :return:
        """
        self.current_candidate = candidate

    async def set_user_info(self):
        """
        Устанавливает значение для атрибутов ``city``, ``sex``, ``bdate``
        :return:
        """
        city, sex, bdate = await user_data(self.user_vk_id)
        self.city = city
        self.sex = sex
        self.bdate = bdate

    async def __get_database_user_id(self) -> int:
        """
        :return: Идентификатор пользователя в таблице ``user``
        """
        return await orm_get_user_id(self.user_vk_id)

    async def __search_new_candidate(self) -> list[int]:
        """
        :return: Список идентификаторов пользователей вконтакте
        """
        return await search_users(self.city, self.sex, self.bdate)

    async def added_candidate_to_database(self):
        """
        Добавляет кандидатов в таблицу ``candidate``
        :return:
        """
        candidate_list = await self.__search_new_candidate()
        user_id = await self.__get_database_user_id()
        await orm_add_all_candidate(candidate_list, user_id)

    async def set_pages(self):
        """
        Устанавливает значение для атрибута ``pages``
        :return:
        """
        user_id = await self.__get_database_user_id()
        self.pages = await orm_get_all_candidate(user_id)

    async def next_candidate(self):
        """
        Выводит пользователю сообщение со следующим кандидатом
        :return:
        """
        candidate = self.paginator.get_next()
        self.__set_current_candidate(candidate[0])
        first_name, last_name = await search_candidate(candidate)
        await send_choose_message(
            self.user_vk_id,
            f"{first_name} {last_name}\nhttps://vk.com/id{candidate[0]}",
            candidate, self.paginator.has_previous(), self.paginator.has_next()
        )

    async def now_candidate(self):
        candidate = self.paginator.get_page()
        self.__set_current_candidate(candidate[0])
        first_name, last_name = await search_candidate(candidate)
        await send_choose_message(
            self.user_vk_id,
            f"{first_name} {last_name}\nhttps://vk.com/id{candidate[0]}",
            candidate, self.paginator.has_previous(), self.paginator.has_next()
        )

    async def previous_candidate(self):
        """
        Выводит пользователю сообщение с предыдущим кандидатом
        :return:
        """
        candidate = self.paginator.get_previous()
        self.__set_current_candidate(candidate[0])
        first_name, last_name = await search_candidate(candidate[0])
        await send_choose_message(
            self.user_vk_id,
            f"{first_name} {last_name}\nhttps://vk.com/id{candidate[0]}",
            candidate, self.paginator.has_previous(), self.paginator.has_next()
        )

    async def added_candidate_to_favorite(self):
        """
        Добавляет текущего кандидата в таблицу ``favorite_candidate``
        :return:
        """
        user_id = await orm_get_user_id(self.user_vk_id)
        candidate_id = await orm_get_candidate(self.current_candidate)
        result = await orm_add_favorite_candidate(user_id, candidate_id)
        if result:
            await self.next_candidate()
            return "Пользователь добавлен в избранное"
            # await send_message(self.user_vk_id, "Пользователь добавлен в избранное")
        else:
            # await send_message(self.user_vk_id, "Пользователь уже добавлен")
            return "Пользователь уже добавлен"

    async def added_candidate_to_blacklist(self):
        """
        Добавляет текущего кандидата в таблицу ``blacklist``
        :return:
        """
        user_id = await orm_get_user_id(self.user_vk_id)
        candidate_id = await orm_get_candidate(self.current_candidate)

        await orm_set_candidate_skip(self.current_candidate)
        result = await orm_add_candidate_to_blacklist(user_id, candidate_id)
        if result:
            # await send_message(self.user_vk_id, "Пользователь теперь в чёрном списке")

            if self.current_candidate in self.pages:
                del self.pages[self.pages.index(self.current_candidate)]
                self.paginator.pages = len(self.pages)
                self.paginator.page = len(self.pages)

            if self.pages:
                await self.now_candidate()
            else:
                await send_start_message(self.user_vk_id, 'Что делаем?')
            return "Пользователь теперь в чёрном списке"
        else:
            # await send_message(self.user_vk_id, "Пользователь уже в чёрном списке")
            return "Пользователь уже в чёрном списке"

    async def drop_pages(self):
        """
        Сбрасывает значение для атрибута ``pages``
        :return:
        """
        user_id = await self.__get_database_user_id()
        self.pages = await drop_all_candidate(user_id)
        return "кандидаты очищены"

    async def get_blacklist(self):
        blacklist_ids = await get_user_blacklist_candidate(self.user_vk_id)
        blacklist_ids = [str(ids) for ids in blacklist_ids]
        blacklist = await search_candidate_bigquery(','.join(blacklist_ids))
        text = [f"{a['first_name']} {a['last_name']} https://vk.com/id{a['id']}" for a in blacklist]
        await send_message(self.user_vk_id, '\n\n'.join(text))

    async def get_favorite(self):
        favorite_ids = await get_user_favorite_candidate(self.user_vk_id)
        favorite_ids = [str(ids) for ids in favorite_ids]
        favorite = await search_candidate_bigquery(','.join(favorite_ids))
        text = [f"{a['first_name']} {a['last_name']} https://vk.com/id{a['id']}" for a in favorite]
        await send_message(self.user_vk_id, '\n\n'.join(text))
