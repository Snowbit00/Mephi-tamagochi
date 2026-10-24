"""Модуль с интерфейсом и реализацией класса игры"""

from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any

from .clicker import AbstractClicker
from .exceptions import EmptyBag, NotEnoughMoney, TamagochiIsGone
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
    Что купить и чем кормить, игра выбирает сама: покупается первый
    товар магазина, на который хватает монет, а кормят и лечат тем,
    что лежит в сумке первым.
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
        Покупает первую еду из магазина, на которую хватает монет

        Поход в магазин занимает тик времени.

        :raises TamagochiIsGone: если игра окончена до или после покупки
        :raises NotEnoughMoney: если монет не хватает ни на какую еду
        """
        self._check_game_over()
        food = self._first_affordable(self._all_food, 'еда')
        self._coins -= food.price
        self._food_bag.append(food)
        self._next_turn()

    def buy_medicine(self) -> None:
        """
        Покупает первое лекарство из магазина, на которое хватает монет

        В сумку кладётся новая упаковка, поэтому образец из магазина
        не расходуется. Поход в магазин занимает тик времени.

        :raises TamagochiIsGone: если игра окончена до или после покупки
        :raises NotEnoughMoney: если монет не хватает ни на какое
            лекарство
        """
        self._check_game_over()
        medicine = self._first_affordable(self._all_medicine, 'лекарство')
        self._coins -= medicine.price
        self._medicine_bag.append(replace(medicine, uses=0))
        self._next_turn()

    def feed_tamagochi(self) -> None:
        """
        Кормит питомца первой едой из сумки, проходит тик времени

        :raises TamagochiIsGone: если игра окончена до или после кормления
        :raises EmptyBag: если в сумке нет еды
        """
        self._check_game_over()
        if not self._food_bag:
            raise EmptyBag('Сумка с едой пуста, сначала купите еду')
        self._tamagochi.feed(self._food_bag.pop(0))
        self._next_turn()

    def heal_tamagochi(self) -> None:
        """
        Лечит питомца первым лекарством из сумки, проходит тик времени

        Питомец тратит одну дозу. Закончившееся лекарство
        выбрасывается из сумки.

        :raises TamagochiIsGone: если игра окончена до или после лечения
        :raises EmptyBag: если в сумке нет лекарств
        """
        self._check_game_over()
        if not self._medicine_bag:
            raise EmptyBag(
                'Сумка с лекарствами пуста, сначала купите лекарство'
            )
        medicine = self._medicine_bag[0]
        self._tamagochi.heal(medicine)
        if medicine.is_empty():
            self._medicine_bag.pop(0)
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

        :return: копия списка купленной еды
        """
        return list(self._food_bag)

    @property
    def medicine(self) -> list[Medicine]:
        """
        Сумка с лекарствами

        :return: копия списка купленных лекарств
        """
        return list(self._medicine_bag)

    def _first_affordable(
        self, goods: list[Food] | list[Medicine], title: str
    ) -> Food | Medicine:
        """
        Находит первый товар магазина, на который хватает монет

        :param goods: товары магазина (еда или лекарства)
        :param title: как назвать товар в сообщении об ошибке
        :return: товар, который можно купить
        :raises NotEnoughMoney: если монет не хватает ни на один товар
        """
        for item in goods:
            if item.price <= self._coins:
                return item
        cheapest = min(item.price for item in goods)
        raise NotEnoughMoney(
            f'Не хватает монет: {title} стоит от {cheapest}, '
            f'у вас {self._coins}'
        )

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
