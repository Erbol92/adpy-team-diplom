"""Методы для работы с vk_api"""

import json

import vk_api

from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from app.config import VK_TOKEN, GROUP_ID, USER_TOKEN
from app.database.orm_query import (orm_get_all_candidate,
                                    orm_get_user_id,
                                    get_user_favorite_candidate,
                                    get_user_blacklist_candidate)
from .any_method import params


vk_session = vk_api.VkApi(token=VK_TOKEN)
user_session = vk_api.VkApi(token=USER_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)


async def send_message_event_answer(event_id: str, user_id: int, peer_id: int, text: str = None):
    """
    Отправляет событие с действием, которое произойдет при нажатии на callback-кнопку
    :param event_id: Случайная строка, которая возвращается в событии message_event
    :param user_id: Идентификатор пользователя
    :param peer_id: Идентификатор диалога со стороны сообщества
    :param text: Сообщение, которое будет показано пользователю
    :return:
    """
    param = {'event_id': event_id,
             'user_id': user_id,
             'peer_id': peer_id,
             }
    if text is not None:
        event_data = {'event_data': json.dumps({"type": "show_snackbar", "text": text})}
        param.update(event_data)
    try:
        vk.messages.sendMessageEventAnswer(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


async def confirm_choose(user_id: int, message: str):
    """
    Подтверждение удаления
    :param user_id: Идентификатор пользователя
    :param message: Сообщение для пользователя
    :return:
    """
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button('подтвердить', color=VkKeyboardColor.POSITIVE, payload={
        "button": "confirm",
        "label": "confirm", })
    keyboard.add_callback_button('отмена', color=VkKeyboardColor.NEGATIVE, payload={
        "button": "discard",
        "label": "discard", })
    param = params(user_id, message, keyboard)
    try:
        vk.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


async def send_start_message(user_id: int, message: str):
    """
    Стартовое сообщение
    :param user_id: Идентификатор пользователя
    :param message: Сообщение для пользователя
    :return:
    """
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button('🧲 поиск', color=VkKeyboardColor.NEGATIVE, payload={
        "button": "search",
        "label": "🧲 поиск", })
    keyboard.add_callback_button('🌏 указать место', color=VkKeyboardColor.POSITIVE, payload={
        "button": "geo",
        "label": "🌏 указать место", })
    uid = await orm_get_user_id(user_id)
    all_user_candidates = await orm_get_all_candidate(uid)
    if all_user_candidates:
        keyboard.add_line()
        keyboard.add_callback_button('продолжить', color=VkKeyboardColor.PRIMARY, payload={
            "button": "continue",
            "label": "continue", })

    user_favorite_candidate = await get_user_favorite_candidate(user_id)
    user_blacklist_candidate = await get_user_blacklist_candidate(user_id)
    count = 2 if user_favorite_candidate and user_blacklist_candidate else None
    if count == 2:
        keyboard.add_line()
    if user_favorite_candidate:
        keyboard.add_callback_button('избранные', color=VkKeyboardColor.PRIMARY, payload={
            "button": "favorite",
            "label": "favorite", })
    if user_blacklist_candidate:
        keyboard.add_callback_button('черный список', color=VkKeyboardColor.PRIMARY, payload={
            "button": "blacklist",
            "label": "blacklist", })

    param = params(user_id, message, keyboard)
    try:
        vk.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


def get_photos(user_id: int):
    """
    Получение фото
    :param user_id: Идентификатор пользователя
    :return: Фотографии пользователя
    """
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
    """
    Отправка сообщения с кнопками для переключения между кандидатами
    :param user_id: Идентификатор пользователя
    :param message: Сообщение
    :param candidate_id: Идентификатор кандидата
    :param has_previous: Проверка на предыдущего в списке кандидатов
    :param has_next: Проверка на следующего в списке кандидатов
    :return:
    """
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button(
        '💔',
        color=VkKeyboardColor.NEGATIVE,
        payload={"button": "dislike", "id": candidate_id, "label": '💔'})
    keyboard.add_callback_button(
        '❤',
        color=VkKeyboardColor.POSITIVE,
        payload={"button": "like", "id": candidate_id, "label": '❤'})

    if has_previous or has_next:
        keyboard.add_line()
        if has_previous:
            keyboard.add_callback_button(
                'предыдущий(ая)',
                color=VkKeyboardColor.PRIMARY,
                payload={"button": "previous", "id": candidate_id, "label": '👈'})
        if has_next:
            keyboard.add_callback_button(
                'следующий(ая)',
                color=VkKeyboardColor.PRIMARY,
                payload={"button": "next", "id": candidate_id, "label": '👉'})

    keyboard.add_line()
    keyboard.add_callback_button(
        'сброс',
        color=VkKeyboardColor.PRIMARY,
        payload={"button": "reset", "label": 'reset'})
    param = params(user_id, message, keyboard, get_photos(candidate_id))
    try:
        vk.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


async def send_message(user_id: int, message: str):
    """
    Отправка текстового сообщения
    :param user_id: Идентификатор пользователя
    :param message: Сообщение
    :return:
    """
    param = params(user_id, message)
    try:
        vk.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


async def geo_user(user_id: int, message: str):
    """
    Отправка сообщения с кнопкой навигации
    :param user_id: Идентификатор пользователя
    :param message: Сообщение
    :return:
    """
    keyboard = VkKeyboard(inline=True)
    keyboard.add_location_button()
    param = params(user_id, message, keyboard)
    try:
        vk.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


async def user_data(user_id: int):
    """
    Получение данных пользователя (с кем чат)
    :param user_id: Идентификатор пользователя
    :return:
    """
    try:
        param = {'user_ids': user_id, 'fields': 'sex,bdate,home_town'}
        response = vk_session.method('users.get', param)

        city = response[0].get('home_town')
        sex = response[0].get('sex')
        bdate = response[0].get('bdate')

        # проверяем если ли дата рождения, если есть смотрим длину (может быть указан день или день/месяц
        if bdate:
            if len(bdate.split('.')) == 3:
                bdate = bdate.split('.')[-1]
            else:
                bdate = None
        else:
            bdate = None

        if bdate and sex:
            return city, sex, bdate
        return {'message': 'заполните в профиле поле ' + 'возраст ' if not bdate else '' + 'пол' if not sex else ''}
    except Exception as E:
        return {'message': f'ошибка {E}'}


async def search_candidate(vk_id: int):
    """
    Осуществляет поиск имени и фамилии пользователя
    :param vk_id: Идентификатор пользователя вконтакте
    :return:
    """
    param = {'user_ids': vk_id}
    response = vk_session.method('users.get', param)

    first_name = response[0]['first_name']
    last_name = response[0]['last_name']
    return first_name, last_name


# массовый запрос как search_candidate
async def search_candidate_bigquery(vk_id: str):
    """
    Осуществляет поиск множества данных о пользователе
    :param vk_id: Идентификатор пользователя вконтакте
    :return:
    """
    param = {'user_ids': vk_id}
    response = vk_session.method('users.get', param)
    return response


# поиск пользователей
async def search_users(city: str, sex: int, bdate: int):
    """
    Поиск подходящих кандидатов по фильтрам
    :param city: Город для поиска
    :param sex: Пол для поиска
    :param bdate: Дата рождения для поиска
    :return:
    """
    try:
        # меняем пол на противоположный
        match sex:
            case 1:
                sex = 2
            case 2:
                sex = 1

        param = {'sex': sex, 'birth_year': bdate, 'hometown': city, 'count': 50}
        response = user_session.method('users.search', param)
        data = [user['id'] for user in response['items']]
        return data
    except Exception as E:
        return f'Ошибка запроса: {E}'
