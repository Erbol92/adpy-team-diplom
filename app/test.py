import unittest
from app.utils.menu_processing import MenuProcessing
from unittest.mock import patch, AsyncMock
from app.bot.core import send_message


class TestMenuProcessing(unittest.TestCase):
    def setUp(self):
        """Этот метод выполняется перед каждым тестом."""
        self.user_vk_id = 12345
        self.menu = MenuProcessing(self.user_vk_id)


    def test_initialization(self):
        """Тестируем инициализацию класса."""
        self.assertEqual(self.menu.user_vk_id, self.user_vk_id)
        self.assertIsNone(self.menu.paginator)
        self.assertEqual(self.menu.current_candidate, 0)
        self.assertIsNone(self.menu.pages)
        self.assertIsNone(self.menu.city)
        self.assertIsNone(self.menu.sex)
        self.assertIsNone(self.menu.bdate)


    def test_set_user_vk_id(self):
        """Тестируем метод set_user_vk_id."""
        new_vk_id = 67890
        self.menu.set_user_vk_id(new_vk_id)
        self.assertEqual(self.menu.user_vk_id, new_vk_id)


    def test_update_city(self):
        """Тестируем метод update_city."""
        new_city = "Москва"
        self.menu.update_city(new_city)
        self.assertEqual(self.menu.city, new_city)

class TestCore(unittest.TestCase):
    @patch('app.bot.core.vk.messages.send')  # Замените на правильный путь к vk.messages.send
    def test_send_message_success(self, mock_send):
        """Тестируем успешную отправку сообщения."""
        user_id = 12345
        message = "Hello"
        result = send_message(user_id, message)
        mock_send.assert_called_once()

    @patch('app.bot.core.vk.messages.send', side_effect=Exception("Ошибка отправки"))
    def test_send_message_failure(self, mock_send):
        user_id = 12345
        message = "Hello"

        # Проверяем, что при вызове send_message возникает исключение
        with self.assertRaises(Exception):
            send_message(user_id, message)
if __name__ == '__main__':
    unittest.main()