"""Методы для работы с vk_api-api"""

import vk_api

from app.config import VK_TOKEN, GROUP_ID, USER_TOKEN
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from app.bot.any_method import params

from app.database.orm_query import (orm_check_user_in_database,
                                    orm_add_user,
                                    orm_add_all_candidate,
                                    orm_set_user_searched,
                                    orm_check_user_searched,
                                    orm_get_user_id, orm_get_all_candidate)
from app.utils.paginator import Paginator

# Инициализация сессий
group_session = vk_api.VkApi(token=VK_TOKEN)
user_session = vk_api.VkApi(token=USER_TOKEN)

bot = group_session.get_api()
longpoll = VkBotLongPoll(group_session, group_id=GROUP_ID)


async def welcome_message(user_id, message):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_callback_button('🧲 поиск', color=VkKeyboardColor.NEGATIVE, payload={"button": "search"})
    keyboard.add_callback_button('🌏 указать место', color=VkKeyboardColor.POSITIVE, payload={"button": "geo"})
    param = params(user_id, message, keyboard)
    try:
        bot.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


def get_photos(user_id: int):
    data = []
    param = {'owner_id': user_id,
             'album_id': 'profile',
             'extended': 1, }
    photos = user_session.method('photos.get', param)['items']
    if photos:
        # Сортировка списка по полю 'like'
        sorted_data = sorted(
            photos, key=lambda x: x['likes']['count'])[-3:]
        for photo in sorted_data:
            media_id, owner_id = photo['id'], photo['owner_id']
            data.append(f'photo{owner_id}_{media_id}')
    return data


async def send_choose_message(user_id: int, message: str, candidate_id: int, has_previous: bool, has_next: bool):
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_callback_button('💔', color=VkKeyboardColor.NEGATIVE, payload={
        "button": "dislike", "id": candidate_id})
    keyboard.add_callback_button('❤', color=VkKeyboardColor.POSITIVE, payload={
        "button": "like", "id": candidate_id})
    keyboard.add_line()
    if has_previous:
        keyboard.add_callback_button('предыдущий(ая)', color=VkKeyboardColor.PRIMARY,
                                     payload={"button": "previous", "id": candidate_id})

    if has_next:
        keyboard.add_callback_button('следующий(ая)', color=VkKeyboardColor.PRIMARY,
                                     payload={"button": "next", "id": candidate_id})

    param = params(user_id, message, keyboard, get_photos(candidate_id))
    try:
        bot.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


async def send_message(user_id, message):
    param = params(user_id, message)
    try:
        bot.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


async def get_user_geo(user_id, message):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_location_button()
    param = params(user_id, message, keyboard)
    try:
        bot.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


async def search_users(city: str, sex: int, bdate: int):
    try:
        param = {'sex': sex, 'birth_year': bdate, 'hometown': city, 'count': 50}
        response = user_session.method('users.search', param)
        data = [user['id'] for user in response['items']]
        return data
    except Exception as E:
        return f'Ошибка запроса: {E}'


async def get_user_data(user_id: int):
    try:
        param = {'user_ids': user_id, 'fields': 'sex,bdate,home_town'}
        response = group_session.method('users.get', param)

        city = response[0].get('home_town')
        sex = response[0].get('sex')
        bdate = response[0].get('bdate')

        # проверяем если ли др, если есть смотрим длину (может быть указан день или день/месяц
        if bdate:
            if len(bdate.split('.')) == 3:
                bdate = bdate.split('.')[-1]
            else:
                bdate = None
        else:
            bdate = None
        # меняем пол на противоположный
        match sex:
            case 1:
                sex = 2
            case 2:
                sex = 1
        if bdate and sex:
            return city, sex, bdate
        return {'message': 'заполните в профиле поле ' + 'возраст ' if not bdate else '' + 'пол' if not sex else ''}
    except Exception as E:
        return {'message': f'ошибка {E}'}


async def search_candidate(vk_id: int):
    param = {'user_ids': vk_id}
    response = group_session.method('users.get', param)

    first_name = response[0]['first_name']
    last_name = response[0]['last_name']
    candidate_id = response[0]['id']
    return first_name, last_name, candidate_id


async def main():
    global candidate_paginator
    for event in longpoll.listen():

        # Обработка сообщений
        if event.type == VkBotEventType.MESSAGE_NEW:
            user_id = event.obj.message['from_id']
            city, sex, bdate = await get_user_data(user_id)

            if not await orm_check_user_in_database(user_id):
                await orm_add_user(user_id)
                print('Пользователь добавлен в базу данных')

            searched = await orm_check_user_searched(user_id)

            if searched:
                uid = await orm_get_user_id(user_id)
                candidates = await orm_get_all_candidate(uid[0])
                candidate_paginator = Paginator(candidates)
                user = candidate_paginator.get_next()

                first_name, last_name, candidate_id = await search_candidate(user)

                await send_choose_message(
                    user_id,
                    f"{first_name} {last_name}\nhttps://vk.com/id{candidate_id}",
                    candidate_id, candidate_paginator.has_previous(), candidate_paginator.has_next()
                )
            else:
                if event.obj.message.get('geo'):
                    city = event.obj.message.get('geo')['place']['city']
                    candidate_list = await search_users(city, sex, bdate)
                    uid = await orm_get_user_id(user_id)
                    await orm_add_all_candidate(candidate_list, uid[0])

                    candidates = await orm_get_all_candidate(uid[0])
                    candidate_paginator = Paginator(candidates)
                    user = candidate_paginator.get_next()

                    first_name, last_name, candidate_id = await search_candidate(user)

                    await send_choose_message(
                        user_id,
                        f"{first_name} {last_name}\nhttps://vk.com/id{candidate_id}",
                        candidate_id, candidate_paginator.has_previous(), candidate_paginator.has_next()
                    )

                    await orm_set_user_searched(user_id)

                else:
                    await welcome_message(user_id, 'Что делаем?')

        # Обработка кнопок
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            payload = event.object.payload.get('button')

            button_id = event.object.payload.get(event.object.user_id)
            city, sex, bdate = await get_user_data(event.object.user_id)

            match payload:
                case 'geo':
                    await get_user_geo(event.object.user_id, f"Ваше местоположение")
                case 'search':
                    candidate_list = await search_users(city, sex, bdate)
                    uid = await orm_get_user_id(event.object.user_id)
                    await orm_add_all_candidate(candidate_list, uid[0])

                    candidates = await orm_get_all_candidate(uid[0])
                    candidate_paginator = Paginator(candidates)

                    user = candidate_paginator.get_next()

                    first_name, last_name, candidate_id = await search_candidate(user)
                    await send_choose_message(
                        event.object.user_id,
                        f"{first_name} {last_name}\nhttps://vk.com/id{candidate_id}",
                        candidate_id, candidate_paginator.has_previous(), candidate_paginator.has_next()
                    )
                    await orm_set_user_searched(event.object.user_id)
                case 'next':

                    user = candidate_paginator.get_next()
                    first_name, last_name, candidate_id = await search_candidate(user)

                    await send_choose_message(
                        event.object.user_id,
                        f"{first_name} {last_name}\nhttps://vk.com/id{candidate_id}",
                        candidate_id, candidate_paginator.has_previous(), candidate_paginator.has_next()
                    )
                case 'previous':
                    user = candidate_paginator.get_previous()
                    first_name, last_name, candidate_id = await search_candidate(user)

                    await send_choose_message(
                        event.object.user_id,
                        f"{first_name} {last_name}\nhttps://vk.com/id{candidate_id}",
                        candidate_id, candidate_paginator.has_previous(), candidate_paginator.has_next()
                    )

                case 'like':
                    await send_message(event.object.user_id, f"Вы нажали ❤ {button_id}")
                case 'dislike':
                    await send_message(event.object.user_id, f"Вы нажали 💔 {button_id}")
