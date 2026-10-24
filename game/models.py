"""Модуль с моделями"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Food:
    """Модель объекта еды"""
    name: str  # наименование
    satiety: int  # на сколько единиц утоляет голод
    price: int  # стоимость

    def __repr__(self) -> str:
        """
        Метод для красивого принтинга объекта

        :return: описание объекта для вывода на экран
        """
        return (
            f'{self.name} стоимость: {self.price}, '
            f'утоляет голод на {self.satiety} единиц'
        )


@dataclass
class Medicine:
    """Модель объекта лекарства"""
    name: str  # наименование
    price: int  # стоимость
    heal_hp: int  # сколько лечит HP
    number_of_uses: int  # максимальное количество применений
    uses: int = 0  # текущее количество применений

    def is_empty(self) -> bool:
        """
        Проверяет, осталось ли еще лекарство

        :return: True если применения закончились, иначе False
        """
        return self.uses >= self.number_of_uses

    def __repr__(self) -> str:
        """
        Метод для красивого принтинга объекта

        :return: описание объекта для вывода на экран
        """
        return (
            f'{self.name} стоимость: {self.price}, '
            f'лечит на {self.heal_hp} HP, '
            f'использований: {self.number_of_uses - self.uses}'
            f'/{self.number_of_uses}'
        )
