from app.config import VK_TOKEN, GROUP_ID, USER_TOKEN
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# Инициализация сессии
vk_session = vk_api.VkApi(token=VK_TOKEN)
user_session = vk_api.VkApi(token=USER_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)


def user_generator(users):
    for user in users:
        yield user

# Функции для отправки сообщения

# стартовое сообщение


def send_start_message(user_id, message):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_callback_button('🧲 поиск', color=VkKeyboardColor.NEGATIVE, payload={
                                 "button": "search"})
    keyboard.add_callback_button('🌏 указать место', color=VkKeyboardColor.POSITIVE, payload={
                                 "button": "geo"})
    vk.messages.send(
        user_id=user_id,
        message=message,
        keyboard=keyboard.get_keyboard(),
        random_id=0
    )


# отправка сообщений с кнопкой навигации


def send_choose_message(user_id: int, message: str, candidate_id: int):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_callback_button('💔', color=VkKeyboardColor.NEGATIVE, payload={
                                 "button": "dislike", "id": candidate_id})
    keyboard.add_callback_button('❤', color=VkKeyboardColor.POSITIVE, payload={
                                 "button": "like", "id": candidate_id})
    keyboard.add_callback_button('следующий(ая)', color=VkKeyboardColor.PRIMARY,
                                 payload={"button": "next", "id": candidate_id})
    vk.messages.send(
        user_id=user_id,
        message=message,
        keyboard=keyboard.get_keyboard(),
        random_id=0
    )


# отправка текстового сообщения

def send_message(user_id, message):
    print(message)
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=0
    )

# отправка сообщения с кнопкой навигации


def geo_user(user_id, message):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_location_button()
    vk.messages.send(
        user_id=user_id,
        message=message,
        keyboard=keyboard.get_keyboard(),
        random_id=0
    )

# поиск пользователей в сообществе


def search_users_in_group(id: int):
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


def user_data(id: int):
    try:
        params = {'user_ids': id, 'fields': 'sex,bdate,home_town'}
        response = vk_session.method('users.get', params)
        response = response[0]
        bdate = response.get('bdate')
        sex = response.get('sex')
        city = response.get('home_town')
        if bdate:
            bdate = bdate.split('.')[-1]
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
    except:
        return {'message': 'ошибка'}


# поиск пользователей
def search_users(city: str, sex: int, bdate: int):
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
def search(id: int, home_town: str = None):
    result = user_data(id)
    if not isinstance(result, dict):
        bdate, sex, city = result
        # если home_town передан, заменяем город
        if home_town:
            city = home_town
        # если и то и то None
        if not city:
            text = 'неизвестно в каком городе искать'
            return text
        print(city)
        text = search_users(city, sex, bdate)
    else:
        text = result['message']
    return text


for event in longpoll.listen():
    # обрабатываем новые сообщения
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.obj.message['text']
        your_id = event.obj.message['from_id']
        print(event.obj.message)
        # если ответ геолокация
        if event.obj.message.get('geo'):
            city = event.obj.message.get('geo')['place']['city']
            users = user_generator(search(your_id, city))
            user = next(users)
            send_choose_message(your_id, f"{user['first_name']} {
                                user['last_name']}", user['id'])
        else:
            send_start_message(event.obj.message['from_id'], f"что делаем?")
    # обрабатываем новые события(кнопки)
    elif event.type == VkBotEventType.MESSAGE_EVENT:  # Обработка колбеков
        payload = event.object.payload.get('button')
        button_id = event.object.payload.get('id')
        print(payload)
        match payload:
            case 'dislike':
                send_message(event.object.user_id, f"Вы нажали 💔 {button_id}")
            case 'like':
                send_message(event.object.user_id, f"Вы нажали ❤ {button_id}")
            case 'next':
                send_message(event.object.user_id, "Вы нажали 'Следующий(ая)'")
            case 'search':
                text = search(your_id)
                print(text)
            case 'geo':
                geo_user(event.object.user_id, f"Ваше местоположение")
