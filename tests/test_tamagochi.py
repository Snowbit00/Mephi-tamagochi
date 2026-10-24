"""Тесты питомца"""

import pytest

import game.tamagochi as rules
from game.exceptions import MedicineIsEmpty
from game.models import Food, Medicine
from game.tamagochi import AbstractTamagochi, SimpleTamagochi

APPLE = Food(name='Яблоко', satiety=10, price=15)
BURGER = Food(name='Бургер', satiety=20, price=40)

# С какого тика голод достигает максимума (деление с округлением вверх)
STARVING_FROM = -(-rules.MAX_STAT // rules.HUNGER_PER_TICK)


def make_medicine(heal_hp: int = 20, number_of_uses: int = 2) -> Medicine:
    return Medicine(
        name='Ибупрофен', price=30, heal_hp=heal_hp,
        number_of_uses=number_of_uses,
    )


def tick(pet: SimpleTamagochi, times: int) -> None:
    for _ in range(times):
        pet.update()


def tick_rested(pet: SimpleTamagochi, times: int) -> None:
    """Тики, перед каждым питомец отдыхает: растёт только голод"""
    for _ in range(times):
        pet.rest()
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
    assert pet.status == {
        'hunger': rules.HUNGER_PER_TICK,
        'fatigue': rules.FATIGUE_PER_TICK,
        'hp': 100,
        'energy': 100 - rules.ENERGY_PER_TICK,
    }


def test_feed_reduces_hunger_and_energy(pet):
    tick(pet, 10)
    before = pet.status
    pet.feed(APPLE)
    assert pet.status['hunger'] == before['hunger'] - APPLE.satiety
    assert pet.status['energy'] == before['energy'] - rules.FEED_ENERGY_COST


def test_feed_does_not_make_hunger_negative(pet):
    pet.feed(BURGER)
    assert pet.status['hunger'] == 0


def test_play_spends_energy_and_heals_healthy_pet(sick_pet):
    tick(sick_pet, 4)  # болезнь отняла здоровье
    sick_pet.heal(make_medicine(heal_hp=0))
    before = sick_pet.status
    sick_pet.play()
    assert sick_pet.status['hp'] == before['hp'] + rules.PLAY_HP_BONUS
    assert sick_pet.status['energy'] == (
        before['energy'] - rules.PLAY_ENERGY_COST
    )
    assert sick_pet.status['fatigue'] == before['fatigue'] + rules.PLAY_FATIGUE


def test_sick_pet_gets_no_hp_from_play(sick_pet):
    tick(sick_pet, 2)
    before = sick_pet.status['hp']
    sick_pet.play()
    assert sick_pet.status['hp'] == before


def test_rest_restores_energy_and_fatigue(pet):
    for _ in range(5):
        pet.play()  # усталость 50, энергия 0
    pet.rest()
    assert pet.status['fatigue'] == 50 - rules.REST_FATIGUE_RECOVERY
    assert pet.status['energy'] == rules.REST_ENERGY_RECOVERY


def test_sick_pet_rests_half_as_well(sick_pet):
    for _ in range(5):
        sick_pet.play()  # энергия кончилась
    before = sick_pet.status
    sick_pet.rest()
    assert sick_pet.status['fatigue'] == (
        before['fatigue'] - rules.REST_FATIGUE_RECOVERY // 2
    )
    assert sick_pet.status['energy'] == rules.REST_ENERGY_RECOVERY // 2


def test_sickness_hurts_hp_and_adds_fatigue(sick_pet):
    before = sick_pet.status
    sick_pet.update()
    assert sick_pet.status['hp'] == before['hp'] - rules.SICK_HP_LOSS
    assert sick_pet.status['fatigue'] == (
        before['fatigue'] + rules.FATIGUE_PER_TICK
        + rules.SICK_FATIGUE_PER_TICK
    )


def test_heal_cures_restores_hp_and_spends_dose(sick_pet):
    tick(sick_pet, 6)
    before = sick_pet.status['hp']
    medicine = make_medicine(heal_hp=20)
    sick_pet.heal(medicine)
    assert not sick_pet.is_sick()
    assert sick_pet.status['hp'] == before + 20
    assert medicine.uses == 1


def test_heal_does_not_raise_hp_above_max(pet):
    pet.heal(make_medicine(heal_hp=50))
    assert pet.status['hp'] == 100


def test_heal_with_empty_medicine_raises(pet):
    medicine = make_medicine(number_of_uses=1)
    pet.heal(medicine)
    with pytest.raises(MedicineIsEmpty):
        pet.heal(medicine)
    assert medicine.uses == 1


def test_healthy_pet_never_gets_sick_with_zero_chance(pet):
    tick(pet, 30)
    assert not pet.is_sick()


def test_weak_pet_gets_sick_more_often(monkeypatch):
    monkeypatch.setattr('game.tamagochi.random.random', lambda: 0.5)
    pet = SimpleTamagochi(sick_chance=0.4)
    fastest = max(rules.HUNGER_PER_TICK, rules.FATIGUE_PER_TICK)
    tick(pet, rules.WEAK_THRESHOLD // fastest)  # ещё не ослаб: 0.5 > 0.4
    assert not pet.is_sick()
    pet.update()  # ослаб: шанс 0.4 * 2.5 = 1.0
    assert pet.is_sick()


def test_starving_pet_loses_hp(pet):
    tick_rested(pet, STARVING_FROM - 1)
    assert pet.status['hp'] == 100
    tick_rested(pet, 1)  # голод дошёл до максимума
    assert pet.status['hp'] == 100 - rules.STARVING_HP_LOSS


def test_exhausted_pet_without_energy_loses_hp(pet):
    for _ in range(10):
        pet.play()  # усталость 100, энергия 0
    pet.update()
    assert pet.status['hp'] == (
        100 - rules.EXHAUSTED_HP_LOSS - rules.NO_ENERGY_HP_LOSS
    )


def test_pet_dies_only_when_hp_below_zero(pet):
    ticks_to_zero = STARVING_FROM - 1 + 100 // rules.STARVING_HP_LOSS
    tick_rested(pet, ticks_to_zero)
    assert pet.status['hp'] == 0
    assert pet.is_alive()
    tick_rested(pet, 1)
    assert pet.status['hp'] < 0
    assert not pet.is_alive()


def test_neglected_pet_dies_without_errors(pet):
    tick(pet, 300)
    assert not pet.is_alive()


@pytest.mark.parametrize(
    'action',
    [
        lambda pet: pet.feed(APPLE),
        lambda pet: pet.play(),
        lambda pet: pet.rest(),
        lambda pet: pet.heal(make_medicine(heal_hp=0)),
        lambda pet: pet.update(),
    ],
)
def test_dead_pet_stays_dead(pet, action):
    tick(pet, 300)
    action(pet)  # конец игры отслеживает игра, питомец не падает
    assert not pet.is_alive()
