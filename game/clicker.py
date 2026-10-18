"""Модуль с интерфейсом и реализацией кликера"""

from abc import ABC, abstractmethod
from random import randint


class AbstractClicker(ABC):
    """Интерфейс для кликера"""

    @abstractmethod
    def __init__(self) -> None:
        """Абстрактный метод инициализации"""
        raise NotImplementedError

    @abstractmethod
    def click(self) -> None:
        """Абстрактный метод клика для накапливания монет"""
        raise NotImplementedError

    @property
    @abstractmethod
    def income_per_click(self) -> int:
        """Абстрактное свойство для доступа к количеству монет за клик"""
        raise NotImplementedError


class SimpleRandomClicker(AbstractClicker):
    """Кликер, который за каждый клик даёт случайное число монет"""

    def __init__(self, min_income: int, max_income: int) -> None:
        """
        Создаёт кликер с диапазоном дохода за один клик

        :param min_income: наименьшее число монет за клик
        :param max_income: наибольшее число монет за клик
        :raises ValueError: если границы отрицательные
            или минимум больше максимума
        """
        if not 0 <= min_income <= max_income:
            raise ValueError(
                'Доход за клик должен быть неотрицательным, '
                'а минимум не больше максимума'
            )
        self._min_income = min_income
        self._max_income = max_income
        self._income_per_click = 0

    def click(self) -> None:
        """Делает клик: выбирает случайный доход в заданном диапазоне"""
        self._income_per_click = randint(self._min_income, self._max_income)

    @property
    def income_per_click(self) -> int:
        """
        Сколько монет принёс последний клик

        :return: доход последнего клика, до первого клика 0
        """
        return self._income_per_click
