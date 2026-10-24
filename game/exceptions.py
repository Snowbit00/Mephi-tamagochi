"""Модуль с исключениями"""


class GameError(Exception):
    """Базовая ошибка игры, от неё наследуются все остальные"""


class TamagochiIsGone(GameError):
    """Ошибка при смерти тамагочи"""


class NotEnoughMoney(GameError):
    """Ошибка когда не хватает монет для покупки"""


class EmptyBag(GameError):
    """Ошибка когда в сумке нет нужного предмета (еды или лекарства)"""


class MedicineIsEmpty(GameError):
    """Ошибка когда у лекарства не осталось применений"""


class ActionCancelled(GameError):
    """Ошибка когда игрок отменил выбор предмета"""
