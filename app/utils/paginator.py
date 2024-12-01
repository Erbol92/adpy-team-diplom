"""Пагинатор для переключения между пользователями"""
import math


class Paginator:
    """Простой пагинатор"""
    def __init__(self, array: list | tuple, page: int=0, per_page: int=1):
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)
        # math.ceil - округление в большую сторону до целого числа
        self.pages = math.ceil(self.len / self.per_page)

    def __get_slice(self):
        """Возвращает нужный индекс кандидата"""
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def get_page(self):
        """Возвращает текущий индекс кандидата"""
        page_items = self.__get_slice()
        return page_items

    def has_next(self):
        """Проверяет наличие следующего индекса из списка кандидатов"""
        if self.page < self.pages:
            return self.page + 1
        return False

    def has_previous(self):
        """Проверяет наличие предыдущего индекса из списка кандидатов"""
        if self.page > 1:
            return self.page - 1
        return False

    def get_next(self):
        """Возвращает следующего кандидата из списка"""
        if self.page < self.pages:
            self.page += 1
            return self.get_page()
        raise IndexError(f'Next page does not exist. Use has_next() to check before.')

    def get_previous(self):
        """Проверяет предыдущего кандидата из списка"""
        if self.page > 1:
            self.page -= 1
            return self.__get_slice()
        raise IndexError(f'Previous page does not exist. Use has_previous() to check before.')