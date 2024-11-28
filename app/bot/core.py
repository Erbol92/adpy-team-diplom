import vk_api
from config import VK_TOKEN, GROUP_ID, USER_TOKEN
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from .any_method import params
from .iterator import UserIterator

# from app.database.models import User, UserCandidate, Candidate
# from app.database.engine import session_factory

# Инициализация сессии
vk_session = vk_api.VkApi(token=VK_TOKEN)
user_session = vk_api.VkApi(token=USER_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

user_profile = {}
user_iterators = {}


# Функции для отправки сообщения

# стартовое сообщение
async def send_start_message(user_id, message):
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button('🧲 поиск', color=VkKeyboardColor.NEGATIVE, payload={
        "button": "search",
        "label": "🧲 поиск", })
    keyboard.add_callback_button('🌏 указать место', color=VkKeyboardColor.POSITIVE, payload={
        "button": "geo",
        "label": "🌏 указать место", })
    param = params(user_id, message, keyboard)
    try:
        vk.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


# получение фоток
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


# отправка сообщений с кнопкой навигации
async def send_choose_message(user_id: int, message: str, candidate_id: int):
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button('💔', color=VkKeyboardColor.NEGATIVE, payload={
        "button": "dislike", "id": candidate_id, "label": '💔'})
    keyboard.add_callback_button('❤', color=VkKeyboardColor.POSITIVE, payload={
        "button": "like", "id": candidate_id, "label": '❤'})
    keyboard.add_line()
    keyboard.add_callback_button('следующий(ая)', color=VkKeyboardColor.PRIMARY,
                                 payload={"button": "next", "id": candidate_id, "label": '👉'})
    param = params(user_id, message, keyboard, get_photos(candidate_id))
    try:
        vk.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


# отправка текстового сообщения

async def send_message(user_id, message):
    param = params(user_id, message)
    try:
        vk.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


# отправка сообщения с кнопкой навигации


async def geo_user(user_id, message):
    keyboard = VkKeyboard(inline=True)
    keyboard.add_location_button()
    param = params(user_id, message, keyboard)
    try:
        vk.messages.send(**param)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


# полученые данных пользователя (с кем чат)
async def user_data(user_id: int):
    try:
        param = {'user_ids': user_id, 'fields': 'sex,bdate,home_town'}
        response = vk_session.method('users.get', param)
        response = response[0]
        bdate = response.get('bdate')
        sex = response.get('sex')
        city = response.get('home_town')
        # проверяем если ли др, если есть смотрим длину (может быть указан день или день/месяц
        if bdate:
            if len(bdate.split('.')) == 3:
                bdate = bdate.split('.')[-1]
            else:
                bdate = None
        else:
            bdate = None
        user_profile[user_id] = {}
        user_profile[user_id]['sex'] = sex
        user_profile[user_id]['bdate'] = bdate
        user_profile[user_id]['city'] = city
        if bdate and sex:
            return bdate, sex, city
        return {'message': 'заполните в профиле поле ' + 'возраст ' if not bdate else '' + 'пол' if not sex else ''}
    except Exception as E:
        return {'message': f'ошибка {E}'}


# поиск пользователей
async def search_users(city: str, sex: int, bdate: int):
    try:
        # меняем пол на противоположный
        match sex:
            case 1:
                sex = 2
            case 2:
                sex = 1
        param = {'user_ids': id, 'sex': sex,
                 'birth_year': bdate, 'hometown': city, 'count': 5}
        response = user_session.method('users.search', param)
        data = [{'id': user['id'],
                 'first_name': user['first_name'],
                 'last_name': user['last_name']} for user in response['items']]
        return data
    except Exception as E:
        return f'Ошибка запроса: {E}'


# поиск в зависимости от того передан параметр город или нет
async def search(user_id: int, home_town: str = None):
    bdate = user_profile[user_id]['bdate']
    sex = user_profile[user_id]['sex']
    # если home_town передан, заменяем город
    city = home_town if home_town else user_profile[user_id].get('city')
    # если и то и то None
    if not city:
        text = 'неизвестно в каком городе искать'
        return text
    text = await search_users(city, sex, bdate)
    user_profile[user_id]['candidate'] = text
    # Создаем итератор для текущего пользователя
    user_iterators[user_id] = UserIterator(user_profile[user_id]['candidate'])
    return text


# проверяем есть ли у пользователя др и пол
async def check_and_send(your_id: int, event):
    sex = user_profile[your_id].get('sex')
    bdate = user_profile[your_id].get('bdate')
    if sex and bdate:
        # если ответ геолокация
        if event.obj.message.get('geo'):
            city = event.obj.message.get('geo')['place']['city']
            if not user_profile[your_id].get('candidate'):
                await search(your_id, city)
            try:
                if user_profile[your_id].get('candidate'):
                    user = next(user_iterators[your_id])
                    await send_choose_message(your_id,
                                              f"{user['first_name']} {user['last_name']}\nhttps://vk.com/id{user['id']}",
                                              user['id'])
                else:
                    await send_message(your_id, f'людей нет')
            except Exception as E:
                await send_message(your_id, f'люди закончились {E}')
        else:
            await send_start_message(your_id, f"что делаем?")


# редактирование сообщений
def edit_mess(label, event):
    mess = vk.messages.getByConversationMessageId(
        peer_id=event.obj.peer_id,
        conversation_message_ids=event.obj.conversation_message_id,
    )['items'][0]
    vk.messages.edit(
        peer_id=event.obj.peer_id,
        message=f"{mess['text']}  {label}",
        conversation_message_id=event.obj.conversation_message_id,
        keyboard=None)


def clean_global_param(event):
    if user_profile[event.object.user_id].get('candidate'):
        user_profile[event.object.user_id]['candidate'].clear()
    if user_iterators.get(event.object.user_id):
        del user_iterators[event.object.user_id]


async def main():
    for event in longpoll.listen():
        # обрабатываем новые сообщения
        if event.type == VkBotEventType.MESSAGE_NEW:
            your_id = event.obj.message['from_id']
            # если у пользователя есть запись в словаре, то чекаем др и пол и обрабатываем сообщения,
            # иначе пробуем прописать в словарь данные
            if user_profile.get(your_id):
                await check_and_send(your_id, event)
            else:
                check_user = await user_data(your_id)
                if isinstance(check_user, dict):
                    await send_message(your_id, check_user['message'])
                else:
                    await check_and_send(your_id, event)
        # обрабатываем новые события(кнопки)
        elif event.type == VkBotEventType.MESSAGE_EVENT:  # Обработка колбеков
            payload = event.object.payload.get('button')
            label = event.object.payload.get('label')
            button_id = event.object.payload.get(event.object.user_id)
            match payload:
                case 'dislike' | 'like':
                    try:
                        edit_mess(label, event)
                        user = next(user_iterators[event.object.user_id])
                        await send_choose_message(event.object.user_id,
                                                  f"{user['first_name']} {user['last_name']}\nhttps://vk.com/id{user['id']}",
                                                  user['id'])
                    except:
                        clean_global_param(event)
                        await send_message(event.object.user_id, 'люди закончились')
                case ('next' | 'search'):
                    # Получаем следующего пользователя для текущего пользователя
                    try:
                        edit_mess(label, event)
                        if user_iterators.get(event.object.user_id):
                            user = next(user_iterators[event.object.user_id])
                            await send_choose_message(event.object.user_id,
                                                      f"{user['first_name']} {user['last_name']}\nhttps://vk.com/id{user['id']}",
                                                      user['id'])
                        else:
                            await send_message(event.object.user_id, 'в вашем профиле нет города, выберите город')
                    except:
                        clean_global_param(event)
                        await send_message(event.object.user_id, ' люди закончились')
                case 'geo':
                    edit_mess(label, event)
                    clean_global_param(event)
                    await geo_user(event.object.user_id, f"Ваше местоположение")
