"""Модуль содержит настройки проекта"""

import os

from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

DSN = f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

VK_TOKEN = os.getenv('VK_TOKEN')
USER_TOKEN = os.getenv('USER_TOKEN')
GROUP_ID = os.getenv('GROUP_ID')
