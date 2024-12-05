"""Пагинатор для переключения между данными списка или кортежа"""

import math


class Paginator:
    """Простой пагинатор"""
    def __init__(self, array: list | tuple, page: int = 0, per_page: int = 1):
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)
        self.pages = math.ceil(self.len / self.per_page)

    def __get_slice(self):
        """
        Функция определяет индекс в списке/кортеже,
        данные из которого необходимо вернуть
        :return: Требуемый индекс списка/кортежа
        """
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def get_page(self):
        """
        :return: Возвращает данные из списка/кортежа
        """
        page_items = self.__get_slice()
        return page_items

    def has_next(self):
        """
        Проверяет есть ли у списка/кортежа индекс справа
        :return: Следующий индекс, если есть, в противном случае False
        """
        if self.page < self.pages:
            return self.page + 1
        return False

    def has_previous(self):
        """
        Проверяет есть ли у списка/кортежа индекс слева
        :return: Предшествующий индекс, если есть, в противном случае False
        """
        if self.page > 1:
            return self.page - 1
        return False

    def get_next(self):
        """
        Устанавливает текущий индекс для списка/кортежа правее
        :return: Возвращает данные из списка/кортежа
        """
        if self.page < self.pages:
            self.page += 1
            return self.get_page()
        raise IndexError(f'Следующая страница не существует. Используйте has_next() использованием функции.')

    def get_previous(self):
        """
        Устанавливает текущий индекс для списка/кортежа левее
        :return: Возвращает данные из списка/кортежа
        """
        if self.page > 1:
            self.page -= 1
            return self.__get_slice()
        raise IndexError(f'Следующая страница не существует. Используйте has_previous() использованием функции.')
