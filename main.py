"""Точка входа: консольный «Тамагочи-кликер»"""

import os

from game.clicker import SimpleRandomClicker
from game.exceptions import GameError, TamagochiIsGone
from game.game import AbstractGame, SimpleGame
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi

PET_NAME = 'Мурзик'
MIN_INCOME = 10  # монет за работу: от MIN_INCOME до MAX_INCOME
MAX_INCOME = 20
EXIT_COMMAND = '0'

# Команды меню: номер -> (название, метод игры, сообщение о результате).
# В сообщение на место {} подставляется то, что вернул метод.
ACTIONS = {
    '1': ('Пойти на работу', 'work', 'Вы заработали {} монет'),
    '2': ('Купить еду', 'buy_food', 'Вы купили еду'),
    '3': ('Купить лекарство', 'buy_medicine', 'Вы купили лекарство'),
    '4': ('Покормить', 'feed_tamagochi', 'Вы покормили питомца'),
    '5': ('Вылечить', 'heal_tamagochi', 'Вы дали питомцу лекарство'),
    '6': ('Играть', 'play_with_tamagochi', 'Вы поиграли с питомцем'),
    '7': ('Отдых', 'rest_tamagochi', 'Питомец отдохнул'),
}


def create_game() -> AbstractGame:
    """
    Создаёт питомца, кликер, магазин и собирает из них игру

    :return: готовая к запуску игра
    """
    all_food = [
        Food(name='Бургер', satiety=20, price=40),
        Food(name='Салат', satiety=10, price=20),
        Food(name='Яблоко', satiety=10, price=15),
    ]

    all_medicine = [
        Medicine(name='Ибупрофен', price=30, heal_hp=20, number_of_uses=2),
    ]

    tamagochi = SimpleTamagochi(name=PET_NAME)
    clicker = SimpleRandomClicker(MIN_INCOME, MAX_INCOME)
    return SimpleGame(
        tamagochi, clicker, all_food=all_food, all_medicine=all_medicine
    )


def clear_screen() -> None:
    """Очищает консоль в Windows (cls) и в Linux/macOS (clear)"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_status(game: AbstractGame) -> None:
    """
    Печатает сумки, показатели питомца и монеты

    :param game: текущая игра
    """
    status = game.get_status()
    print(f'Сумка с едой: {game.food}')
    print(f'Сумка с лекарствами: {game.medicine}')
    print(
        f'\nСтатус: голод {status["hunger"]}, '
        f'усталость {status["fatigue"]}, здоровье {status["hp"]}, '
        f'энергия {status["energy"]}, монет {status["coins"]}\n'
    )
    if game.tamagochi.is_sick():
        print('=======Тамагочи болеет======')
        print('=======Отдых действует менее эффективно=======')


def print_menu() -> None:
    """Печатает список действий"""
    for command, (title, _, _) in ACTIONS.items():
        print(f'{command}. {title}')
    print(f'{EXIT_COMMAND}. Выход')


def make_turn(game: AbstractGame, command: str) -> str:
    """
    Выполняет выбранное игроком действие

    :param game: текущая игра
    :param command: номер действия из меню
    :return: сообщение о результате для игрока
    :raises GameError: если действие не удалось (нет денег, еды и т. п.)
    """
    if command not in ACTIONS:
        return 'Неверная команда'
    _, method_name, message = ACTIONS[command]
    result = getattr(game, method_name)()
    return message.format(result)


def main() -> None:
    """Запускает игровой цикл: показать статус, спросить действие"""
    game = create_game()

    print(f'Добро пожаловать в Тамагочи-кликер! Ваш питомец — кот {PET_NAME}')
    output = ''

    while True:
        print(output)
        print_status(game)
        print_menu()
        command = input('Выберите действие: ')
        if command == EXIT_COMMAND:
            break
        try:
            output = make_turn(game, command)
        except TamagochiIsGone as error:
            print(error)
            break
        except GameError as error:
            output = str(error)

        clear_screen()


if __name__ == '__main__':
    main()
