from vk_api.utils import get_random_id
def params(user_id: int, message: str, keyboard=None, attachments=None) -> dict:
    data = {
        'user_id': user_id,
        'message': message,
        'keyboard': keyboard.get_keyboard() if keyboard else None,
        'random_id': get_random_id(),
        'attachment': ','.join(attachments) if attachments else None
    }
    return data


# поиск пользователей в сообществе
# async def search_users_in_group(id: int):
#     try:
#         param = {
#             'group_id': GROUP_ID,
#             'user_ids': id,
#             'count': 1,
#             'fields': 'city,sex,bdate'}
#         response = vk_session.method('groups.getMembers', param)
#         return response['items']
#     except:
#         return 'Ошибка запроса'
