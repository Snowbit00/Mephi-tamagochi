"""Тесты кликера"""

import pytest

from game.clicker import AbstractClicker, SimpleRandomClicker


def test_clicker_follows_interface():
    assert isinstance(SimpleRandomClicker(10, 20), AbstractClicker)


def test_income_is_zero_before_first_click():
    assert SimpleRandomClicker(10, 20).income_per_click == 0


def test_click_income_stays_in_range():
    clicker = SimpleRandomClicker(10, 20)
    for _ in range(200):
        clicker.click()
        assert 10 <= clicker.income_per_click <= 20


def test_click_with_equal_bounds_gives_exact_income():
    clicker = SimpleRandomClicker(7, 7)
    clicker.click()
    assert clicker.income_per_click == 7


@pytest.mark.parametrize('min_income, max_income', [(-1, 5), (20, 10)])
def test_wrong_bounds_raise_value_error(min_income, max_income):
    with pytest.raises(ValueError):
        SimpleRandomClicker(min_income, max_income)
