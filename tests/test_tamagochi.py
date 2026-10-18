"""Тесты питомца"""

import pytest

from game.exceptions import TamagochiIsGone
from game.models import Food, Medicine
from game.tamagochi import AbstractTamagochi, SimpleTamagochi

APPLE = Food(name='Яблоко', satiety=10, price=15)
BURGER = Food(name='Бургер', satiety=20, price=40)


def make_medicine(heal_hp: int = 20, number_of_uses: int = 2) -> Medicine:
    return Medicine(
        name='Ибупрофен', price=30, heal_hp=heal_hp,
        number_of_uses=number_of_uses,
    )


def tick(pet: SimpleTamagochi, times: int) -> None:
    for _ in range(times):
        pet.update()


@pytest.fixture
def pet() -> SimpleTamagochi:
    """Здоровый питомец, который никогда не заболеет сам"""
    return SimpleTamagochi(sick_chance=0)


@pytest.fixture
def sick_pet() -> SimpleTamagochi:
    """Питомец, заболевший на первом тике (болезнь ещё не била по HP)"""
    pet = SimpleTamagochi(sick_chance=1)
    pet.update()
    return pet


def test_pet_follows_interface(pet):
    assert isinstance(pet, AbstractTamagochi)


def test_new_pet_is_healthy_and_full(pet):
    assert pet.name == 'Мурзик'
    assert pet.status == {'hunger': 0, 'fatigue': 0, 'hp': 100, 'energy': 100}
    assert pet.is_alive()
    assert not pet.is_sick()


@pytest.mark.parametrize('chance', [-0.1, 1.5])
def test_wrong_sick_chance_raises_value_error(chance):
    with pytest.raises(ValueError):
        SimpleTamagochi(sick_chance=chance)


def test_update_makes_pet_hungry_and_tired(pet):
    pet.update()
    assert pet.status == {'hunger': 3, 'fatigue': 2, 'hp': 100, 'energy': 98}


def test_feed_reduces_hunger_and_energy(pet):
    tick(pet, 10)
    pet.feed(APPLE)
    assert pet.status['hunger'] == 20
    assert pet.status['energy'] == 75


def test_feed_does_not_make_hunger_negative(pet):
    pet.feed(BURGER)
    assert pet.status['hunger'] == 0
    assert pet.status['energy'] == 95


def test_play_spends_energy_and_heals_healthy_pet(sick_pet):
    tick(sick_pet, 4)  # болезнь отняла 16 HP
    sick_pet.heal(make_medicine(heal_hp=0))
    sick_pet.play()
    status = sick_pet.status
    assert status['hp'] == 84 + 10
    assert status['energy'] == 90 - 20


def test_sick_pet_gets_no_hp_from_play(sick_pet):
    tick(sick_pet, 2)
    sick_pet.play()
    assert sick_pet.status['hp'] == 92


def test_rest_restores_energy_and_fatigue(pet):
    for _ in range(5):
        pet.play()
    pet.rest()
    assert pet.status['fatigue'] == 10
    assert pet.status['energy'] == 40


def test_sick_pet_rests_half_as_well(sick_pet):
    for _ in range(5):
        sick_pet.play()
    sick_pet.rest()
    assert sick_pet.status['fatigue'] == 52 - 20
    assert sick_pet.status['energy'] == 0 + 20


def test_sickness_hurts_hp_and_adds_fatigue(sick_pet):
    sick_pet.update()
    assert sick_pet.status['hp'] == 96
    assert sick_pet.status['fatigue'] == 2 + 6


def test_heal_cures_and_restores_hp(sick_pet):
    tick(sick_pet, 6)
    sick_pet.heal(make_medicine(heal_hp=20))
    assert not sick_pet.is_sick()
    assert sick_pet.status['hp'] == 76 + 20


def test_heal_does_not_raise_hp_above_max(pet):
    pet.heal(make_medicine(heal_hp=50))
    assert pet.status['hp'] == 100


def test_heal_with_empty_medicine_raises_value_error(pet):
    with pytest.raises(ValueError):
        pet.heal(make_medicine(number_of_uses=0))


def test_healthy_pet_never_gets_sick_with_zero_chance(pet):
    tick(pet, 30)
    assert not pet.is_sick()


def test_weak_pet_gets_sick_more_often(monkeypatch):
    monkeypatch.setattr('game.tamagochi.random.random', lambda: 0.5)
    pet = SimpleTamagochi(sick_chance=0.4)
    tick(pet, 23)  # голод 69: шанс обычный, 0.5 > 0.4
    assert not pet.is_sick()
    pet.update()  # голод 72: шанс 0.4 * 2.5 = 1.0
    assert pet.is_sick()


def test_starving_pet_loses_hp(pet):
    tick(pet, 33)
    assert pet.status['hp'] == 100
    pet.update()  # голод дошёл до 100
    assert pet.status['hp'] == 90


def test_exhausted_pet_without_energy_loses_hp(pet):
    for _ in range(10):
        pet.play()  # усталость 100, энергия 0
    pet.update()
    assert pet.status['hp'] == 100 - 5 - 5


def test_pet_dies_only_when_hp_below_zero(pet):
    tick(pet, 43)
    assert pet.status['hp'] == 0
    assert pet.is_alive()
    pet.update()
    assert pet.status['hp'] < 0
    assert not pet.is_alive()


@pytest.mark.parametrize(
    'action',
    [
        lambda pet: pet.feed(APPLE),
        lambda pet: pet.play(),
        lambda pet: pet.rest(),
        lambda pet: pet.heal(make_medicine()),
        lambda pet: pet.update(),
    ],
)
def test_dead_pet_cannot_do_anything(pet, action):
    tick(pet, 44)
    with pytest.raises(TamagochiIsGone):
        action(pet)
