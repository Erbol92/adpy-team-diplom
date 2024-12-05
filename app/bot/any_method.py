"""Вспомогательные функции"""

from vk_api.utils import get_random_id


def params(user_id: int, message: str, keyboard=None, attachments=None) -> dict:
    """Формирует словарь параметров для сообщения"""
    data = {
        'user_id': user_id,
        'message': message,
        'keyboard': keyboard.get_keyboard() if keyboard else None,
        'random_id': get_random_id(),
        'attachment': ','.join(attachments) if attachments else None
    }
    return data


def map_sex(sex: int) -> str:
    """Заменяет пол id на строковое значение"""
    match sex:
        case 1:
            return 'man'
        case 2:
            return 'female'
