"""Тесты игры"""

import builtins

import pytest

import game.tamagochi as rules
from game.clicker import AbstractClicker
from game.exceptions import (
    ActionCancelled,
    EmptyBag,
    NotEnoughMoney,
    TamagochiIsGone,
)
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


@pytest.fixture(autouse=True)
def ask(monkeypatch, capsys):
    """Ответы игрока на вопросы игры; по умолчанию выбирается товар 1"""
    answers = ['1'] * 20

    def fake_input(prompt=''):
        return answers.pop(0) if answers else '0'

    monkeypatch.setattr(builtins, 'input', fake_input)
    return answers


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


def test_work_adds_coins_and_makes_a_tick():
    game = make_game(income=15)
    assert game.work() == 15
    status = game.get_status()
    assert status['coins'] == 15
    assert status['hunger'] == rules.HUNGER_PER_TICK


def test_buy_food_without_money_changes_nothing():
    game = make_game(income=10)
    game.work()
    before = game.get_status()
    with pytest.raises(NotEnoughMoney):  # выбран бургер за 40
        game.buy_food()
    assert game.get_status() == before
    assert game.food == []


@pytest.mark.parametrize('choice, expected_food', [
    ('1', BURGER), ('2', SALAD), ('3', APPLE),
])
def test_buy_food_gives_chosen_item(ask, choice, expected_food):
    ask[:] = [choice]
    game = make_game(income=100)
    game.work()
    game.buy_food()
    assert game.food == [expected_food]
    assert game.get_status()['coins'] == 100 - expected_food.price


@pytest.mark.parametrize('answer', ['0', 'abc', '9', ''])
def test_cancelled_choice_changes_nothing(ask, answer):
    game = make_game(income=100)
    game.work()
    before = game.get_status()
    ask[:] = [answer]
    with pytest.raises(ActionCancelled):
        game.buy_food()
    assert game.get_status() == before
    assert game.food == []


def test_shopping_makes_a_tick():
    game = make_game(income=100)
    game.work()
    game.buy_food()
    game.buy_medicine()
    assert game.get_status()['hunger'] == 3 * rules.HUNGER_PER_TICK


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


def test_feed_uses_chosen_food_and_makes_a_tick(ask):
    game = make_game(income=55)
    game.work()
    ask[:] = ['1', '3', '2']  # купить бургер, купить яблоко, съесть яблоко
    game.buy_food()
    game.buy_food()
    game.feed_tamagochi()
    assert game.food == [BURGER]
    assert game.get_status()['hunger'] == rules.HUNGER_PER_TICK


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
    hunger = rules.PLAY_HUNGER + rules.HUNGER_PER_TICK
    assert game.get_status()['hunger'] == hunger
    game.rest_tamagochi()
    assert game.get_status()['hunger'] == hunger + rules.HUNGER_PER_TICK


def test_bags_are_the_real_inventory(ask):
    ask[:] = ['3']  # яблоко
    game = make_game(income=15)
    game.work()
    game.buy_food()
    assert game.food == [APPLE]
    game.food.append(BURGER)  # сумку можно пополнить напрямую
    ask[:] = ['2', '1']  # съесть бургер, потом лечиться
    game.feed_tamagochi()
    assert game.food == [APPLE]
    game.medicine.append(Medicine('Ибупрофен', 30, 20, 2))
    game.heal_tamagochi()
    assert game.medicine[0].uses == 1


def test_work_alone_ends_the_game():
    game = make_game()
    with pytest.raises(TamagochiIsGone):
        for _ in range(300):  # без еды питомец погибнет от голода
            game.work()
    assert not game.tamagochi.is_alive()


def test_after_death_status_works_and_actions_are_blocked():
    game = make_game()
    with pytest.raises(TamagochiIsGone):
        for _ in range(300):
            game.rest_tamagochi()
    status = game.get_status()
    assert status['hp'] < 0
    for action in (game.work, game.buy_food, game.feed_tamagochi,
                   game.play_with_tamagochi, game.rest_tamagochi):
        with pytest.raises(TamagochiIsGone):
            action()
    assert game.get_status() == status
