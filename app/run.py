import asyncio

from vk_api.bot_longpoll import VkBotEventType

from app.bot.core import longpoll, send_start_message, geo_user, confirm_choose, sendMessageEventAnswer
from app.database.orm_query import orm_check_user_in_database, orm_add_user
from app.database.orm_query import orm_check_user_searched, orm_set_user_searched
from app.database.orm_query import main as main_db
from app.utils.menu_processing import MenuProcessing
from app.config import FILENAME_MENU
import pickle
import os

# Восстановление menu из pikl файла
if os.path.exists(FILENAME_MENU):
    with open(FILENAME_MENU, 'rb') as f:
        menu = pickle.load(f)
else:
    menu = {}


async def main():
    await main_db()
    for event in longpoll.listen():
        user_vk_id = event.obj.message['from_id'] if event.object.message else event.object.user_id
        if event.type == VkBotEventType.MESSAGE_NEW:
            if not menu.get(user_vk_id):
                menu[user_vk_id] = MenuProcessing()
                menu[user_vk_id].set_user_vk_id(user_vk_id)
                await menu[user_vk_id].set_user_info()

            if not await orm_check_user_in_database(user_vk_id):
                await orm_add_user(user_vk_id)

            if await orm_check_user_searched(user_vk_id) and menu[user_vk_id].pages and event.object.message.get(
                    'text'):
                await menu[user_vk_id].now_candidate()
            else:
                if event.obj.message.get('geo'):
                    city = event.obj.message.get('geo')['place']['city']
                    menu[user_vk_id].update_city(city)
                    await menu[user_vk_id].added_candidate_to_database()
                    await menu[user_vk_id].set_pages()
                    menu[user_vk_id].set_paginator()
                    await menu[user_vk_id].next_candidate()
                    await orm_set_user_searched(user_vk_id, True)
                else:
                    await send_start_message(user_vk_id, 'Что делаем?')

        elif event.type == VkBotEventType.MESSAGE_EVENT:
            payload = event.object.payload.get('button')

            match payload:
                case 'geo':
                    await geo_user(user_vk_id, f"Ваше местоположение")
                case 'search':
                    await menu[user_vk_id].set_user_info()
                    await menu[user_vk_id].added_candidate_to_database()
                    await menu[user_vk_id].set_pages()
                    menu[user_vk_id].set_paginator()
                    await menu[user_vk_id].next_candidate()
                    await orm_set_user_searched(user_vk_id, True)
                case 'next':
                    await menu[user_vk_id].next_candidate()
                case 'previous':
                    await menu[user_vk_id].previous_candidate()
                case 'like':
                    text = await menu[user_vk_id].added_candidate_to_favorite()
                    await sendMessageEventAnswer(event.object.event_id, user_vk_id, event.obj.peer_id, text)
                case 'dislike':
                    await confirm_choose(user_vk_id, 'подтвердите действие')
                case 'reset':
                    text = await menu[user_vk_id].drop_pages()
                    await orm_set_user_searched(user_vk_id, False)
                    await sendMessageEventAnswer(event.object.event_id, user_vk_id, event.obj.peer_id, text)
                    await send_start_message(user_vk_id, 'Что делаем?')
                case 'continue':
                    await menu[user_vk_id].set_pages()
                    menu[user_vk_id].set_paginator()
                    await menu[user_vk_id].next_candidate()
                    await orm_set_user_searched(user_vk_id, True)
                case 'blacklist':
                    await menu[user_vk_id].get_blacklist()
                case 'confirm':
                    text = await menu[user_vk_id].added_candidate_to_blacklist()
                    await asyncio.sleep(1)
                    await sendMessageEventAnswer(event.object.event_id, user_vk_id, event.obj.peer_id, text)
                case 'discard':
                    await send_start_message(user_vk_id, 'Что делаем?')
                case 'favorite':
                    await menu[user_vk_id].get_favorite()
            if payload not in ['confirm', 'reset', 'like']:
                await sendMessageEventAnswer(event.object.event_id, user_vk_id, event.obj.peer_id)
            print(event.object)

        # Сохранение объекта в pikl файл
        with open(FILENAME_MENU, 'wb') as f:
            pickle.dump(menu, f)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
