"""Сквозные тесты консольной игры: ввод игрока подменяется сценарием"""

import random

import pytest

import main


@pytest.fixture
def screen_clears(monkeypatch) -> list[str]:
    """Вместо очистки консоли записывает команды очистки"""
    commands: list[str] = []
    monkeypatch.setattr(main.os, 'system', commands.append)
    return commands


def play_script(monkeypatch, commands: list[str]) -> None:
    """Запускает main(), отвечая на input() командами по очереди"""
    answers = iter(commands)
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    random.seed(0)
    main.main()


def test_simple_session_runs_without_errors(
    monkeypatch, capsys, screen_clears
):
    # работа ×2, купить еду (товар 3), покормить (1), купить лекарство
    # (товар 1; монет может не хватить), вылечить, играть, отдых, мусор, выход
    play_script(
        monkeypatch,
        ['1', '1', '2', '3', '4', '1', '3', '1', '5', '1', '6', '7', '9',
         '0'],
    )
    output = capsys.readouterr().out
    assert 'Добро пожаловать' in output
    assert 'Неверная команда' in output
    assert 'Traceback' not in output
    assert len(screen_clears) == 10


def test_game_errors_are_shown_to_player(
    monkeypatch, capsys, screen_clears
):
    play_script(monkeypatch, ['2', '1', '4', '5', '0'])
    output = capsys.readouterr().out
    assert 'Не хватает монет' in output
    assert 'Сумка с едой пуста' in output


def test_neglected_pet_ends_the_game(monkeypatch, capsys, screen_clears):
    play_script(monkeypatch, ['7'] * 200)
    output = capsys.readouterr().out
    assert 'Игра окончена' in output


def test_make_turn_buys_and_uses_medicine(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda prompt='': '1')
    random.seed(0)
    game = main.create_game()
    for _ in range(3):  # 3 работы дают не меньше 30 монет
        main.make_turn(game, '1')
    assert main.make_turn(game, '3') == 'Вы купили лекарство'
    assert main.make_turn(game, '5') == 'Вы дали питомцу лекарство'
    assert game.get_status()['coins'] >= 0


def test_clear_screen_uses_command_for_current_os(screen_clears):
    main.clear_screen()
    expected = 'cls' if main.os.name == 'nt' else 'clear'
    assert screen_clears == [expected]
