"""вспомогательные функции"""

from vk_api.utils import get_random_id


# формирует словарь параметров для сообщения
def params(user_id: int, message: str, keyboard=None, attachments=None) -> dict:
    data = {
        'user_id': user_id,
        'message': message,
        'keyboard': keyboard.get_keyboard() if keyboard else None,
        'random_id': get_random_id(),
        'attachment': ','.join(attachments) if attachments else None
    }
    return data


# заменяет пол id на строковое значение
def map_sex(sex: int) -> str:
    match sex:
        case 1:
            return 'man'
        case 2:
            return 'female'
