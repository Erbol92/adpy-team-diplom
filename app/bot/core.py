from .iterator import UserIterator
from config import VK_TOKEN, GROUP_ID, USER_TOKEN
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import asyncio

# Инициализация сессии
vk_session = vk_api.VkApi(token=VK_TOKEN)
user_session = vk_api.VkApi(token=USER_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

user_candidate = {}
user_iterators = {}


def user_generator(users):
    for user in users:
        yield user

# Функции для отправки сообщения

# стартовое сообщение


async def send_start_message(user_id, message):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_callback_button('🧲 поиск', color=VkKeyboardColor.NEGATIVE, payload={
                                 "button": "search"})
    keyboard.add_callback_button('🌏 указать место', color=VkKeyboardColor.POSITIVE, payload={
                                 "button": "geo"})

    params = {
        'user_id': user_id,
        'message': message,
        'keyboard': keyboard.get_keyboard(),
        'random_id': vk_api.utils.get_random_id()
    }
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: vk.messages.send(**params))


# отправка сообщений с кнопкой навигации

def get_photos(user_id: int):
    data = []

    def get_max_width(object):
        if object.get('orig_photo'):
            return object['orig_photo']['url']
        else:
            return object['sizes'][-1]['url']
    params = {'owner_id': user_id,
              'album_id': 'profile',
              'extended': 1, }
    photos = user_session.method('photos.get', params)['items']
    # print(photos)
    if photos:
        # Сортировка списка по полю 'like'
        sorted_data = sorted(
            photos, key=lambda x: x['likes']['count'])[-3:]
        for photo in sorted_data:
            media_id, owner_id = photo['id'], photo['owner_id']
            data.append(f'photo{owner_id}_{media_id}')
    print(data)
    return data


async def send_choose_message(user_id: int, message: str, candidate_id: int):
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_callback_button('💔', color=VkKeyboardColor.NEGATIVE, payload={
                                 "button": "dislike", "id": candidate_id})
    keyboard.add_callback_button('❤', color=VkKeyboardColor.POSITIVE, payload={
                                 "button": "like", "id": candidate_id})
    keyboard.add_callback_button('следующий(ая)', color=VkKeyboardColor.PRIMARY,
                                 payload={"button": "next", "id": candidate_id})
    params = {
        'user_id': user_id,
        'message': message,
        'attachment': ','.join(get_photos(candidate_id)),
        'keyboard': keyboard.get_keyboard(),
        'random_id': vk_api.utils.get_random_id()
    }
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: vk.messages.send(**params))


# отправка текстового сообщения

async def send_message(user_id, message):
    params = {
        'user_id': user_id,
        'message': message,
        'random_id': vk_api.utils.get_random_id()
    }
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: vk.messages.send(**params))

# отправка сообщения с кнопкой навигации


async def geo_user(user_id, message):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_location_button()
    params = {
        'user_id': user_id,
        'message': message,
        'keyboard': keyboard.get_keyboard(),
        'random_id': vk_api.utils.get_random_id()
    }
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: vk.messages.send(**params))

# поиск пользователей в сообществе


async def search_users_in_group(id: int):
    try:
        params = {
            'group_id': GROUP_ID,
            'user_ids': id,
            'count': 1,
            'fields': 'city,sex,bdate'}
        response = vk_session.method('groups.getMembers', params)
        return response['items']
    except:
        return 'Ошибка запроса'

# полученые данных пользователя (с кем чат)


async def user_data(id: int):
    # try:
    params = {'user_ids': id, 'fields': 'sex,bdate,home_town'}
    response = vk_session.method('users.get', params)
    response = response[0]
    bdate = response.get('bdate')
    sex = response.get('sex')
    city = response.get('home_town')
    if bdate:
        if len(bdate.split('.')) == 3:
            bdate = bdate.split('.')[-1]
        else:
            bdate = None
    else:
        bdate = None
    match sex:
        case 1:
            sex = 2
        case 2:
            sex = 1
    if bdate and sex:
        return bdate, sex, city
    return {'message': 'заполните в профиле поле '+'возраст ' if not bdate else ''+'пол' if not sex else ''}
    # except Exception as E:
    #     return {'message': f'ошибка {E}'}


# поиск пользователей
async def search_users(city: str, sex: int, bdate: int):
    # try:, 'city': city
    params = {'user_ids': id, 'sex': sex,
              'birth_year': bdate, 'hometown': city}
    response = user_session.method('users.search', params)
    data = [{'id': user['id'],
             'first_name': user['first_name'],
             'last_name': user['last_name']} for user in response['items']]
    return data
    # except:
    #     return 'Ошибка запроса'


# поиск в зависимости от того передан параметр город или нет
async def search(id: int, home_town: str = None):
    result = await user_data(id)
    if not isinstance(result, dict):
        bdate, sex, city = result
        # если home_town передан, заменяем город
        if home_town:
            city = home_town
        # если и то и то None
        if not city:
            text = 'неизвестно в каком городе искать'
            return text
        text = await search_users(city, sex, bdate)
        user_candidate['id'] = text
        # Создаем итератор для текущего пользователя
        user_iterators[id] = UserIterator(user_candidate['id'])
    else:
        text = result['message']
    print(text)
    return text

# получение фоток


async def main():
    for event in longpoll.listen():
        # обрабатываем новые сообщения

        if event.type == VkBotEventType.MESSAGE_NEW:
            your_id = event.obj.message['from_id']
            check_user = await user_data(your_id)
            if not isinstance(check_user, dict):
                bdate, sex, city = check_user
                if bdate and sex:
                    # если ответ геолокация
                    if event.obj.message.get('geo'):
                        city = event.obj.message.get(
                            'geo')['place']['city']
                        if not user_candidate.get(your_id):
                            await search(your_id, city)
                        user = next(user_iterators[your_id])
                        await send_choose_message(your_id, f"{user['first_name']} {user['last_name']}", user['id'])
                    else:
                        await send_start_message(your_id, f"что делаем?")
            else:
                await send_message(your_id, check_user['message'])

        # обрабатываем новые события(кнопки)
        elif event.type == VkBotEventType.MESSAGE_EVENT:  # Обработка колбеков
            payload = event.object.payload.get('button')
            button_id = event.object.payload.get(event.object.user_id)
            match payload:
                case 'dislike':
                    await send_message(event.object.user_id, f"Вы нажали 💔 {button_id}")
                case 'like':
                    await send_message(event.object.user_id, f"Вы нажали ❤ {button_id}")
                case 'next':
                    # Получаем следующего пользователя для текущего пользователя
                    user = next(user_iterators[event.object.user_id])
                    await send_choose_message(event.object.user_id, f"{user['first_name']} {user['last_name']}\n https://vk.com/id{user['id']}", user['id'])
                case 'search':
                    print(user_candidate.get(event.object.user_id))
                    if not user_candidate.get(event.object.user_id):
                        await search(event.object.user_id)
                    print(user_candidate.get(event.object.user_id))
                    user = next(user_iterators[event.object.user_id])
                    await send_choose_message(event.object.user_id, f"{user['first_name']} {user['last_name']}\n https://vk.com/id{user['id']}", user['id'])
                case 'geo':
                    await geo_user(event.object.user_id, f"Ваше местоположение")