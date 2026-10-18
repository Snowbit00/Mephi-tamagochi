"""Точка входа: консольный «Тамагочи-кликер»"""

import os

from game.clicker import SimpleRandomClicker
from game.exceptions import GameError, TamagochiIsGone
from game.game import AbstractGame, SimpleGame
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi

PET_NAME = 'Мурзик'
EXIT_COMMAND = '0'


def create_game() -> AbstractGame:
    """
    Создаёт питомца, кликер, магазин и собирает из них игру

    :return: готовая к запуску игра
    """
    all_food = [
        Food(name='Бургер', satiety=20, price=40),
        Food(name='Салат', satiety=10, price=20),
        Food(name='Яблоко', satiety=10, price=15)
    ]

    all_medicine = [
        Medicine(name='Ибупрофен', price=30, heal_hp=20, number_of_uses=2)
    ]

    tamagochi = SimpleTamagochi(name=PET_NAME)
    clicker = SimpleRandomClicker(10, 20)
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
    :raises TamagochiIsGone: если игра окончена
    """
    status = game.get_status()
    print(f"Сумка с едой: {game.food}")
    print(f"Сумка с лекарствами: {game.medicine}")
    print(
        f"\nСтатус: голод {status['hunger']}, "
        f"усталость {status['fatigue']}, здоровье {status['hp']}, "
        f"энергия {status['energy']}, монет {status['coins']}\n"
    )
    if game.tamagochi.is_sick():
        print("=======Тамагочи болеет======")
        print("=======Отдых действует менее эффективно=======")


def print_menu() -> None:
    """Печатает список действий"""
    print("1. Пойти на работу")
    print("2. Купить еду")
    print("3. Купить лекарство")
    print("4. Покормить")
    print("5. Вылечить")
    print("6. Играть")
    print("7. Отдых")
    print(f"{EXIT_COMMAND}. Выход")


def make_turn(game: AbstractGame, command: str) -> str:
    """
    Выполняет выбранное игроком действие

    :param game: текущая игра
    :param command: номер действия из меню
    :return: сообщение о результате для игрока
    :raises GameError: если действие не удалось (нет денег, еды и т. п.)
    """
    match command:
        case "1":
            income = game.work()
            game.tamagochi.update()
            return f'Вы заработали {income} монет'
        case "2":
            game.buy_food()
            return 'Вы купили еду'
        case "3":
            game.buy_medicine()
            return 'Вы купили лекарство'
        case "4":
            game.feed_tamagochi()
            return 'Вы покормили питомца'
        case "5":
            game.heal_tamagochi()
            return 'Вы дали питомцу лекарство'
        case "6":
            game.play_with_tamagochi()
            return 'Вы поиграли с питомцем'
        case "7":
            game.rest_tamagochi()
            return 'Питомец отдохнул'
        case _:
            return "Неверная команда"


def main() -> None:
    """Запускает игровой цикл: показать статус, спросить действие"""
    game = create_game()

    print(f"Добро пожаловать в Тамагочи-кликер! Ваш питомец — кот {PET_NAME}")
    output = ''

    while True:
        print(output)
        try:
            print_status(game)
            print_menu()
            command = input("Выберите действие: ")
            if command == EXIT_COMMAND:
                break
            output = make_turn(game, command)
        except TamagochiIsGone as error:
            print(error)
            break
        except GameError as error:
            output = str(error)

        clear_screen()


if __name__ == "__main__":
    main()
