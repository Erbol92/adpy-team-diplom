
<p align="center">
    <img src="vkinder.png" width="150" alt="Логотип VKINDER">
</p>

# <p align="center">VKINDER</p>
<p>Бот для ВКонтакте, который помогает пользователям находить людей.<br>
Подбираются кандидаты противоположного пола, одного возраста на основе их геолокации, либо по городу указанному в вашем профиле.<br>
Бот предоставляет 3 фото из профиля с большим количеством лайков.<br>
Кандидатов можно добавлять в черные списки и избранные</p>

## Установка
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Erbol92/adpy-team-diplom
   cd adpy-team-diplom
   ```
2. Установите необходимые зависимости:
    ``` bash
    pip install -r requirements.txt
    ```
3. Создайте приложение ВК и сообщество:
   - получите access_token->USER_TOKEN;
   - VK_TOKEN токен группы. 
    
4. Cоздайте .env файл в корне проекта и пропишите настройки
```python
DB_USER = ''
DB_PASS = ''
DB_HOST = ''
DB_PORT = ''
DB_NAME = ''

VK_TOKEN = ''
USER_TOKEN = ''
GROUP_ID = ''
FILENAME_MENU = ''
```
## Использование
1. Запустите бота
```bash
    python app/run.py
```
2. Начните чат с ботом ВК
