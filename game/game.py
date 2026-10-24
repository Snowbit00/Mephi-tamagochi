"""Модуль с интерфейсом и реализацией класса игры"""

from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any

from .clicker import AbstractClicker
from .exceptions import (
    ActionCancelled,
    EmptyBag,
    NotEnoughMoney,
    TamagochiIsGone,
)
from .models import Food, Medicine
from .tamagochi import AbstractTamagochi

# Сколько монет у игрока в начале игры
START_COINS = 0


class AbstractGame(ABC):
    """Интерфейс для логики игры"""

    @abstractmethod
    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine]
    ) -> None:
        """
        Абстрактный метод инициализации класса игры

        :param tamagochi: экземпляр тамагочи
        :param clicker: экземпляр кликера
        :param all_food: все доступные варианты еды
        :param all_medicine: все доступные варианты лекарств
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def tamagochi(self) -> AbstractTamagochi:
        """
        Абстрактное свойство для доступа к питомцу

        :return: экземпляр тамагочи
        """
        raise NotImplementedError

    @abstractmethod
    def work(self) -> int:
        """
        Абстрактный метод для логики действия "работа"

        :return: количество заработанных монет
        """
        raise NotImplementedError

    @abstractmethod
    def buy_food(self) -> None:
        """Абстрактный метод для покупки еды"""
        raise NotImplementedError

    @abstractmethod
    def buy_medicine(self) -> None:
        """Абстрактный метод для покупки лекарства"""
        raise NotImplementedError

    @abstractmethod
    def feed_tamagochi(self) -> None:
        """Абстрактный метод для кормления тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def heal_tamagochi(self) -> None:
        """Абстрактный метод для лечения тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def rest_tamagochi(self) -> None:
        """Абстрактный метод для отдыха тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def play_with_tamagochi(self) -> None:
        """Абстрактный метод для игры с тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        Абстрактный метод для получения статуса (всех характеристик) тамагочи

        :return: словарь со всеми характеристиками тамагочи
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def food(self) -> list[Food]:
        """
        Абстрактное свойство для доступа к сумке с едой

        :return: список с имеющимися (купленными) объектами еды
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def medicine(self) -> list[Medicine]:
        """
        Абстрактное свойство для доступа к сумке с лекарствами

        :return: список с имеющимися (купленными) объектами лекарств
        """
        raise NotImplementedError


class SimpleGame(AbstractGame):
    """
    Игра: кошелёк, сумки с едой и лекарствами и ход времени

    Передаёт действия игрока питомцу и следит, не закончилась ли игра.
    Каждое действие занимает один тик времени (час жизни питомца).
    Предмет для покупки, кормления и лечения игрок выбирает из списка
    по номеру, номер 0 отменяет действие (тик при этом не идёт).
    """

    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine]
    ) -> None:
        """
        Создаёт игру с пустым кошельком и пустыми сумками

        :param tamagochi: экземпляр тамагочи
        :param clicker: экземпляр кликера
        :param all_food: все доступные в магазине варианты еды
        :param all_medicine: все доступные в магазине варианты лекарств
        :raises ValueError: если в магазине нет еды или лекарств
        """
        if not all_food or not all_medicine:
            raise ValueError('В магазине должны быть и еда, и лекарства')
        self._tamagochi = tamagochi
        self._clicker = clicker
        self._all_food = list(all_food)
        self._all_medicine = list(all_medicine)
        self._coins = START_COINS
        self._food_bag: list[Food] = []
        self._medicine_bag: list[Medicine] = []

    @property
    def tamagochi(self) -> AbstractTamagochi:
        """
        Питомец, за которым следит игра

        :return: экземпляр тамагочи
        """
        return self._tamagochi

    def work(self) -> int:
        """
        Идёт на работу: кликер приносит монеты, проходит тик времени

        :return: количество заработанных монет
        :raises TamagochiIsGone: если игра окончена до или после работы
        """
        self._check_game_over()
        self._clicker.click()
        income = self._clicker.income_per_click
        self._coins += income
        self._next_turn()
        return income

    def buy_food(self) -> None:
        """
        Покупает еду из магазина: игрок выбирает её по номеру

        Поход в магазин занимает тик времени.

        :raises TamagochiIsGone: если игра окончена до или после покупки
        :raises ActionCancelled: если игрок отменил выбор
        :raises NotEnoughMoney: если монет не хватает на выбранную еду
        """
        self._check_game_over()
        food = self._choose('Какую еду купить?', self._all_food)
        self._pay(food.price)
        self._food_bag.append(food)
        self._next_turn()

    def buy_medicine(self) -> None:
        """
        Покупает лекарство из магазина: игрок выбирает его по номеру

        В сумку кладётся новая упаковка, поэтому образец из магазина
        не расходуется. Поход в магазин занимает тик времени.

        :raises TamagochiIsGone: если игра окончена до или после покупки
        :raises ActionCancelled: если игрок отменил выбор
        :raises NotEnoughMoney: если монет не хватает на лекарство
        """
        self._check_game_over()
        medicine = self._choose(
            'Какое лекарство купить?', self._all_medicine
        )
        self._pay(medicine.price)
        self._medicine_bag.append(replace(medicine, uses=0))
        self._next_turn()

    def feed_tamagochi(self) -> None:
        """
        Кормит питомца едой из сумки: игрок выбирает её по номеру

        Съеденная еда исчезает из сумки, проходит тик времени.

        :raises TamagochiIsGone: если игра окончена до или после кормления
        :raises EmptyBag: если в сумке нет еды
        :raises ActionCancelled: если игрок отменил выбор
        """
        self._check_game_over()
        if not self._food_bag:
            raise EmptyBag('Сумка с едой пуста, сначала купите еду')
        food = self._choose('Чем покормить питомца?', self._food_bag)
        self._food_bag.remove(food)
        self._tamagochi.feed(food)
        self._next_turn()

    def heal_tamagochi(self) -> None:
        """
        Лечит питомца лекарством из сумки: игрок выбирает его по номеру

        Питомец тратит одну дозу. Закончившееся лекарство
        выбрасывается из сумки. Проходит тик времени.

        :raises TamagochiIsGone: если игра окончена до или после лечения
        :raises EmptyBag: если в сумке нет лекарств
        :raises ActionCancelled: если игрок отменил выбор
        """
        self._check_game_over()
        if not self._medicine_bag:
            raise EmptyBag(
                'Сумка с лекарствами пуста, сначала купите лекарство'
            )
        medicine = self._choose(
            'Каким лекарством лечить?', self._medicine_bag
        )
        self._tamagochi.heal(medicine)
        if medicine.is_empty():
            self._remove_by_identity(self._medicine_bag, medicine)
        self._next_turn()

    def rest_tamagochi(self) -> None:
        """
        Укладывает питомца отдыхать, проходит тик времени

        :raises TamagochiIsGone: если игра окончена до или после отдыха
        """
        self._check_game_over()
        self._tamagochi.rest()
        self._next_turn()

    def play_with_tamagochi(self) -> None:
        """
        Играет с питомцем, проходит тик времени

        :raises TamagochiIsGone: если игра окончена до или после игры
        """
        self._check_game_over()
        self._tamagochi.play()
        self._next_turn()

    def get_status(self) -> dict[str, Any]:
        """
        Собирает статус игры: показатели питомца и монеты

        :return: словарь с показателями питомца и ключом coins
        """
        return {**self._tamagochi.status, 'coins': self._coins}

    @property
    def food(self) -> list[Food]:
        """
        Сумка с едой

        :return: список купленной еды (сама сумка, не копия)
        """
        return self._food_bag

    @property
    def medicine(self) -> list[Medicine]:
        """
        Сумка с лекарствами

        :return: список купленных лекарств (сама сумка, не копия)
        """
        return self._medicine_bag

    @staticmethod
    def _choose(title: str, items: list[Any]) -> Any:
        """
        Показывает пронумерованный список и спрашивает номер предмета

        :param title: вопрос игроку
        :param items: предметы на выбор
        :return: выбранный предмет
        :raises ActionCancelled: если введён 0, неверный номер
            или ввод закончился
        """
        print(title)
        for number, item in enumerate(items, start=1):
            print(f'{number}. {item}')
        try:
            answer = input('Введите номер (0 — отмена): ')
        except EOFError:
            raise ActionCancelled('Выбор отменён') from None
        if answer.strip().isdigit() and 1 <= int(answer) <= len(items):
            return items[int(answer) - 1]
        raise ActionCancelled('Выбор отменён')

    def _pay(self, price: int) -> None:
        """
        Списывает монеты за покупку

        :param price: стоимость покупки
        :raises NotEnoughMoney: если монет меньше, чем стоимость
        """
        if price > self._coins:
            raise NotEnoughMoney(
                f'Не хватает монет: нужно {price}, у вас {self._coins}'
            )
        self._coins -= price

    @staticmethod
    def _remove_by_identity(items: list[Any], target: Any) -> None:
        """
        Убирает из списка именно этот объект, а не равный ему

        :param items: список предметов
        :param target: предмет, который нужно убрать
        """
        for index, item in enumerate(items):
            if item is target:
                del items[index]
                return

    def _next_turn(self) -> None:
        """
        Проводит тик времени для питомца и проверяет конец игры

        :raises TamagochiIsGone: если питомец погиб за этот тик
        """
        self._tamagochi.update()
        self._check_game_over()

    def _check_game_over(self) -> None:
        """
        Завершает игру, если питомец погиб

        :raises TamagochiIsGone: если здоровье питомца упало ниже нуля
        """
        if not self._tamagochi.is_alive():
            raise TamagochiIsGone(
                'Здоровье питомца упало ниже нуля. Игра окончена!'
            )
