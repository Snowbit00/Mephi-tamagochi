"""Модуль с интерфейсом и реализациями класса тамагочи"""

import random
from abc import ABC, abstractmethod

from .exceptions import MedicineIsEmpty
from .models import Food, Medicine

# Границы показателей (голод, усталость, энергия, здоровье)
MIN_STAT = 0
MAX_STAT = 100

# Шанс заболеть за один тик
SICK_CHANCE = 0.1
# Если голод или усталость выше порога, питомец ослаблен
# и болеет чаще во столько раз
WEAK_THRESHOLD = 70
WEAK_SICK_CHANCE_FACTOR = 2.5

# Как меняются показатели за один тик
HUNGER_PER_TICK = 2
FATIGUE_PER_TICK = 2
SICK_FATIGUE_PER_TICK = 4  # болезнь утомляет сильнее
ENERGY_PER_TICK = 2

# Сколько здоровья теряется за тик
SICK_HP_LOSS = 4  # болеет
STARVING_HP_LOSS = 10  # голод на максимуме
EXHAUSTED_HP_LOSS = 5  # усталость на максимуме
NO_ENERGY_HP_LOSS = 5  # энергия кончилась

# Действия с питомцем
FEED_ENERGY_COST = 5
PLAY_ENERGY_COST = 20
PLAY_FATIGUE = 10
PLAY_HUNGER = 5
PLAY_HP_BONUS = 10
REST_FATIGUE_RECOVERY = 40
REST_ENERGY_RECOVERY = 40
SICK_REST_DIVIDER = 2  # больной отдыхает вдвое хуже


def clamp_stat(value: int) -> int:
    """
    Ограничивает показатель диапазоном от MIN_STAT до MAX_STAT

    :param value: значение показателя
    :return: значение в допустимых границах
    """
    return max(MIN_STAT, min(MAX_STAT, value))


class AbstractTamagochi(ABC):
    """Интерфейс логики тамагочи"""

    @abstractmethod
    def feed(self, food: Food) -> None:
        """
        Абстрактный метод для кормления тамагочи

        :param food: объект еды для кормления
        """
        raise NotImplementedError

    @abstractmethod
    def play(self) -> None:
        """Абстрактный метод для игры с тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def rest(self) -> None:
        """Абстрактный метод для отдыха тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def heal(self, medicine: Medicine) -> None:
        """
        Абстрактный метод для лечения тамагочи

        :param medicine: лекарство для лечения
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> dict[str, int]:
        """
        Абстрактное свойство для доступа ко всем состояниям тамагочи

        :return: словарь со всеми состояниями тамагочи
        """
        raise NotImplementedError

    @abstractmethod
    def is_alive(self) -> bool:
        """
        Абстрактный метод для проверки жив ли тамагочи

        :return: True если жив, иначе False
        """
        raise NotImplementedError

    @abstractmethod
    def is_sick(self) -> bool:
        """
        Абстрактный метод для проверки, не заболел ли тамагочи

        :return: True если тамагочи болеет, иначе False
        """
        raise NotImplementedError

    @abstractmethod
    def update(self) -> None:
        """
        Абстрактный метод для обновления состояний тамагочи.
        Должен использоваться после каждого взаимодействия с тамагочи
        """
        raise NotImplementedError


class SimpleTamagochi(AbstractTamagochi):
    """
    Питомец с голодом, усталостью, энергией и здоровьем.

    Все показатели от 0 до 100. Со временем (каждый тик update)
    питомец голодает, устаёт, тратит энергию и может заболеть.
    Здоровье сверху ограничено 100, а снизу нет: когда оно падает
    ниже нуля, питомец погибает.
    """

    def __init__(
        self,
        name: str = 'Мурзик',
        sick_chance: float = SICK_CHANCE
    ) -> None:
        """
        Создаёт сытого, бодрого и здорового питомца

        :param name: имя питомца
        :param sick_chance: вероятность заболеть за один тик, от 0 до 1
        :raises ValueError: если вероятность не в диапазоне от 0 до 1
        """
        if not 0 <= sick_chance <= 1:
            raise ValueError('Вероятность болезни должна быть от 0 до 1')
        self._name = name
        self._sick_chance = sick_chance
        self._hunger = MIN_STAT
        self._fatigue = MIN_STAT
        self._energy = MAX_STAT
        self._hp = MAX_STAT
        self._sick = False

    @property
    def name(self) -> str:
        """
        Имя питомца

        :return: имя
        """
        return self._name

    def feed(self, food: Food) -> None:
        """
        Кормит питомца

        Голод уменьшается на сытность еды, а на переваривание
        тратится немного энергии.

        :param food: объект еды для кормления
        """
        self._hunger = clamp_stat(self._hunger - food.satiety)
        self._energy = clamp_stat(self._energy - FEED_ENERGY_COST)

    def play(self) -> None:
        """
        Играет с питомцем

        Тратится энергия, растут усталость и голод.
        Здоровому питомцу игра поднимает здоровье.
        """
        self._energy = clamp_stat(self._energy - PLAY_ENERGY_COST)
        self._fatigue = clamp_stat(self._fatigue + PLAY_FATIGUE)
        self._hunger = clamp_stat(self._hunger + PLAY_HUNGER)
        if not self._sick:
            self._change_hp(PLAY_HP_BONUS)

    def rest(self) -> None:
        """
        Укладывает питомца отдыхать

        Усталость падает, энергия растёт. Больной питомец
        отдыхает вдвое хуже.
        """
        divider = SICK_REST_DIVIDER if self._sick else 1
        self._fatigue = clamp_stat(
            self._fatigue - REST_FATIGUE_RECOVERY // divider
        )
        self._energy = clamp_stat(
            self._energy + REST_ENERGY_RECOVERY // divider
        )

    def heal(self, medicine: Medicine) -> None:
        """
        Лечит питомца одной дозой лекарства

        Здоровье растёт на силу лекарства, болезнь проходит,
        а у лекарства тратится одно применение.

        :param medicine: лекарство для лечения
        :raises MedicineIsEmpty: если у лекарства не осталось применений
        """
        if medicine.is_empty():
            raise MedicineIsEmpty(f'Лекарство {medicine.name} закончилось')
        medicine.uses += 1
        self._change_hp(medicine.heal_hp)
        self._sick = False

    @property
    def status(self) -> dict[str, int]:
        """
        Все показатели питомца

        :return: словарь с ключами hunger, fatigue, hp и energy
        """
        return {
            'hunger': self._hunger,
            'fatigue': self._fatigue,
            'hp': self._hp,
            'energy': self._energy,
        }

    def is_alive(self) -> bool:
        """
        Проверяет, жив ли питомец

        :return: True если здоровье не ниже нуля, иначе False
        """
        return self._hp >= MIN_STAT

    def is_sick(self) -> bool:
        """
        Проверяет, болеет ли питомец

        :return: True если питомец болеет, иначе False
        """
        return self._sick

    def update(self) -> None:
        """
        Проводит один тик времени

        Растут голод и усталость, тратится энергия, теряется здоровье
        от болезни и запущенного состояния, а здоровый питомец может
        заболеть. Погибший питомец не воскресает: здоровье дальше
        только падает, а конец игры отслеживает игра.
        """
        fatigue_gain = FATIGUE_PER_TICK
        if self._sick:
            fatigue_gain += SICK_FATIGUE_PER_TICK
        self._hunger = clamp_stat(self._hunger + HUNGER_PER_TICK)
        self._fatigue = clamp_stat(self._fatigue + fatigue_gain)
        self._energy = clamp_stat(self._energy - ENERGY_PER_TICK)
        self._change_hp(-self._calculate_hp_loss())
        if not self._sick and random.random() < self._current_sick_chance():
            self._sick = True

    def _calculate_hp_loss(self) -> int:
        """
        Считает, сколько здоровья питомец теряет за тик

        :return: потеря здоровья, 0 если всё в порядке
        """
        hp_loss = 0
        if self._sick:
            hp_loss += SICK_HP_LOSS
        if self._hunger >= MAX_STAT:
            hp_loss += STARVING_HP_LOSS
        if self._fatigue >= MAX_STAT:
            hp_loss += EXHAUSTED_HP_LOSS
        if self._energy <= MIN_STAT:
            hp_loss += NO_ENERGY_HP_LOSS
        return hp_loss

    def _current_sick_chance(self) -> float:
        """
        Считает шанс заболеть с учётом ослабленности питомца

        :return: вероятность от 0 до 1
        """
        if self._hunger > WEAK_THRESHOLD or self._fatigue > WEAK_THRESHOLD:
            return min(1.0, self._sick_chance * WEAK_SICK_CHANCE_FACTOR)
        return self._sick_chance

    def _change_hp(self, delta: int) -> None:
        """
        Меняет здоровье, не давая ему подняться выше MAX_STAT

        :param delta: на сколько изменить здоровье (может быть < 0)
        """
        self._hp = min(MAX_STAT, self._hp + delta)
