import asyncio

from vk_api.bot_longpoll import VkBotEventType

from app.bot.core import longpoll, send_start_message, geo_user, confirm_choose
from app.database.orm_query import orm_check_user_in_database, orm_add_user
from app.database.orm_query import orm_check_user_searched, orm_set_user_searched
from app.utils.menu_processing import MenuProcessing


menu = MenuProcessing()


async def main():
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            user_vk_id = event.obj.message['from_id']

            menu.set_user_vk_id(user_vk_id)
            await menu.set_user_info()

            if not await orm_check_user_in_database(user_vk_id):
                await orm_add_user(user_vk_id)

            if await orm_check_user_searched(user_vk_id):
                await menu.set_pages()
                menu.set_paginator()
                await menu.next_candidate()
            else:
                if event.obj.message.get('geo'):
                    city = event.obj.message.get('geo')['place']['city']

                    menu.update_city(city)
                    await menu.added_candidate_to_database()
                    await menu.set_pages()
                    menu.set_paginator()
                    await menu.next_candidate()

                    await orm_set_user_searched(user_vk_id, True)
                else:
                    await send_start_message(user_vk_id, 'Что делаем?')

        elif event.type == VkBotEventType.MESSAGE_EVENT:
            payload = event.object.payload.get('button')
            button_id = event.object.payload.get(event.object.user_id)

            match payload:
                case 'geo':
                    await geo_user(event.object.user_id, f"Ваше местоположение")
                case 'search':
                    await menu.added_candidate_to_database()
                    await menu.set_pages()
                    menu.set_paginator()
                    await menu.next_candidate()
                    await orm_set_user_searched(event.object.user_id, True)
                case 'next':
                    await menu.next_candidate()
                case 'previous':
                    await menu.previous_candidate()
                case 'like':
                    await menu.added_candidate_to_favorite()
                case 'dislike':
                    await confirm_choose(event.object.user_id, 'подтвердите действие')

                case 'reset':
                    await menu.drop_pages()
                    await orm_set_user_searched(event.object.user_id, False)
                    await send_start_message(event.object.user_id, 'Что делаем?')
                case 'continue':
                    await menu.set_pages()
                    menu.set_paginator()
                    await menu.next_candidate()
                    await orm_set_user_searched(event.object.user_id, True)
                case 'blacklist':
                    await menu.get_blacklist()
                case 'confirm':
                    await menu.added_candidate_to_blacklist()
                case 'discard':
                    await send_start_message(event.object.user_id, 'Что делаем?')
                case 'favorite':
                    await menu.get_favorite()


if __name__ == '__main__':
    try:
        # asyncio.run(main_db())
        asyncio.run(main())
    except Exception as e:
        print(e)


