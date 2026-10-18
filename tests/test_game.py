"""Тесты игры"""

import pytest

from game.clicker import AbstractClicker
from game.exceptions import EmptyBag, NotEnoughMoney, TamagochiIsGone
from game.game import AbstractGame, SimpleGame
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi

BURGER = Food(name='Бургер', satiety=20, price=40)
SALAD = Food(name='Салат', satiety=10, price=20)
APPLE = Food(name='Яблоко', satiety=10, price=15)


class FixedClicker(AbstractClicker):
    """Кликер без случайности: всегда даёт одно и то же число монет"""

    def __init__(self, income: int = 15) -> None:
        self._income = income

    def click(self) -> None:
        pass

    @property
    def income_per_click(self) -> int:
        return self._income


def make_game(income: int = 15) -> SimpleGame:
    medicine = Medicine(
        name='Ибупрофен', price=30, heal_hp=20, number_of_uses=2
    )
    return SimpleGame(
        SimpleTamagochi(sick_chance=0),
        FixedClicker(income),
        all_food=[BURGER, SALAD, APPLE],
        all_medicine=[medicine],
    )


def earn(game: SimpleGame, times: int) -> None:
    for _ in range(times):
        game.work()


def test_game_follows_interface():
    assert isinstance(make_game(), AbstractGame)


@pytest.mark.parametrize('all_food, all_medicine', [
    ([], [Medicine('Ибупрофен', 30, 20, 2)]),
    ([APPLE], []),
])
def test_empty_shop_raises_value_error(all_food, all_medicine):
    with pytest.raises(ValueError):
        SimpleGame(
            SimpleTamagochi(), FixedClicker(), all_food, all_medicine
        )


def test_new_game_status():
    assert make_game().get_status() == {
        'hunger': 0, 'fatigue': 0, 'hp': 100, 'energy': 100, 'coins': 0,
    }


def test_work_adds_coins_without_tick():
    game = make_game(income=15)
    assert game.work() == 15
    assert game.work() == 15
    status = game.get_status()
    assert status['coins'] == 30
    assert status['hunger'] == 0


def test_buy_food_without_money_raises():
    game = make_game(income=10)
    game.work()
    with pytest.raises(NotEnoughMoney):
        game.buy_food()
    assert game.get_status()['coins'] == 10
    assert game.food == []


@pytest.mark.parametrize('coins, expected_food', [
    (15, APPLE),  # хватает только на яблоко
    (25, APPLE),  # салат и яблоко одинаково сытные, яблоко дешевле
    (45, BURGER),  # хватает на самое сытное
])
def test_buy_food_picks_most_filling_affordable(coins, expected_food):
    game = make_game(income=coins)
    game.work()
    game.buy_food()
    assert game.food == [expected_food]
    assert game.get_status()['coins'] == coins - expected_food.price


def test_buy_medicine_without_money_raises():
    game = make_game(income=20)
    game.work()
    with pytest.raises(NotEnoughMoney):
        game.buy_medicine()
    assert game.medicine == []


def test_bought_medicine_is_new_package():
    game = make_game(income=60)
    game.work()
    game.buy_medicine()
    game.buy_medicine()
    first, second = game.medicine
    assert first is not second
    assert first.uses == 0
    assert game.get_status()['coins'] == 0


def test_feed_with_empty_bag_raises():
    with pytest.raises(EmptyBag):
        make_game().feed_tamagochi()


def test_feed_uses_most_filling_food_and_ticks():
    game = make_game(income=55)
    game.work()
    game.buy_food()  # бургер за 40
    game.buy_food()  # яблоко за 15
    game.rest_tamagochi()
    game.rest_tamagochi()  # голод 6
    game.feed_tamagochi()
    assert game.food == [APPLE]
    assert game.get_status()['hunger'] == 0 + 3  # съел бургер, потом тик


def test_heal_with_empty_bag_raises():
    with pytest.raises(EmptyBag):
        make_game().heal_tamagochi()


def test_heal_spends_doses_and_throws_away_empty_medicine():
    game = make_game(income=30)
    game.work()
    game.buy_medicine()
    game.heal_tamagochi()
    assert game.medicine[0].uses == 1
    game.heal_tamagochi()
    assert game.medicine == []


def test_shop_medicine_is_not_spent():
    shop_medicine = Medicine('Ибупрофен', 30, 20, 1)
    game = SimpleGame(
        SimpleTamagochi(sick_chance=0), FixedClicker(30),
        [APPLE], [shop_medicine],
    )
    game.work()
    game.buy_medicine()
    game.heal_tamagochi()
    assert shop_medicine.uses == 0


def test_play_and_rest_make_a_tick():
    game = make_game()
    game.play_with_tamagochi()
    assert game.get_status()['hunger'] == 5 + 3
    game.rest_tamagochi()
    assert game.get_status()['hunger'] == 8 + 3


def test_bags_are_copies():
    game = make_game(income=15)
    game.work()
    game.buy_food()
    game.food.clear()
    game.medicine.append(Medicine('Ибупрофен', 30, 20, 2))
    assert game.food == [APPLE]
    assert game.medicine == []


def test_game_ends_when_pet_dies():
    game = make_game()
    with pytest.raises(TamagochiIsGone):
        for _ in range(100):  # без еды питомец погибнет от голода
            game.rest_tamagochi()
    assert not game.tamagochi.is_alive()
    with pytest.raises(TamagochiIsGone):
        game.get_status()
    with pytest.raises(TamagochiIsGone):
        game.work()
