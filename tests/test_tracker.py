import os
from unittest.mock import MagicMock, patch

import pytest

from src.aeroplane import Aeroplane
from src.savers import JSONSaver
from src.utils import (
    filter_aeroplanes,
    get_aeroplanes_by_altitude,
    get_top_aeroplanes,
    print_aeroplanes,
    sort_aeroplanes,
    user_interaction,
)

# ==========================================================
# 1. ТЕСТЫ ДЛЯ src/aeroplane.py (Модель данных и Валидация)
# ==========================================================


def test_aeroplane_creation_and_validation():
    """Тест создания объекта и базового приведения типов."""
    plane = Aeroplane("ACA123", "Canada", 220.0, 11000.0)
    assert plane.callsign == "ACA123"
    assert plane.origin_country == "Canada"
    assert plane.velocity == 220.0
    assert plane.altitude == 11000.0

    broken_plane = Aeroplane(None, None, None, None)
    assert broken_plane.callsign == "UNKNOWN"
    assert broken_plane.origin_country == "Unknown"
    assert broken_plane.velocity == 0.0
    assert broken_plane.altitude == 0.0


def test_aeroplane_dunder_comparisons():
    """Тест dunder-методов сравнения самолетов (Критерий №4)."""
    plane1 = Aeroplane("P1", "Test", 100.0, 5000.0)
    plane2 = Aeroplane("P2", "Test", 200.0, 5000.0)
    plane3 = Aeroplane("P3", "Test", 100.0, 6000.0)

    assert plane1 < plane2
    assert plane1 < plane3
    assert plane2 > plane1
    assert plane1 <= plane3
    assert plane1 == Aeroplane("P1", "Test", 100.0, 5000.0)
    assert (plane1 == "не самолет") is False


def test_cast_to_object_list():
    """Тест фабричного метода преобразования сырого JSON структуры OpenSky."""
    raw_response = {
        "states": [
            [
                "4b1812",
                "THY1812 ",
                "Turkey",
                1720448120,
                1720448120,
                29.12,
                40.98,
                10200.5,
                False,
                210.4,
                120,
                None,
                None,
                10200.5,
                "3144",
                False,
                0,
            ]
        ]
    }
    obj_list = Aeroplane.cast_to_object_list(raw_response)
    assert len(obj_list) == 1
    assert obj_list[0].callsign == "THY1812"
    assert obj_list[0].origin_country == "Turkey"
    assert obj_list[0].velocity == 210.4
    assert obj_list[0].altitude == 10200.5  # ИСПРАВЛЕНО ТУТ

    assert Aeroplane.cast_to_object_list(None) == []
    assert Aeroplane.cast_to_object_list({"states": None}) == []
    assert Aeroplane.cast_to_object_list({"states": [["сломанная строка"]]}) == []


# ==========================================================
# 2. ТЕСТЫ ДЛЯ src/savers.py (JSON Добавление и Удаление)
# ==========================================================


@pytest.fixture
def temp_json_saver():
    """Фикстура для создания временного тестового файла JSON."""
    test_file = "data/test_aeroplanes.json"
    saver = JSONSaver(test_file)
    yield saver
    if os.path.exists(test_file):
        os.remove(test_file)


def test_json_saver_operations(temp_json_saver):
    """Тест корректности добавления и удаления из JSON (Критерий №6)."""
    plane_dict = {
        "callsign": "TEST777",
        "origin_country": "Spain",
        "velocity": 150.0,
        "altitude": 8000.0,
    }
    assert temp_json_saver._read() == []

    temp_json_saver.add_aeroplane(plane_dict)
    current_data = temp_json_saver._read()
    assert len(current_data) == 1
    assert current_data[0]["callsign"] == "TEST777"

    temp_json_saver.delete_aeroplane(plane_dict)
    assert temp_json_saver._read() == []


# ==========================================================
# 3. ТЕСТЫ ДЛЯ src/utils.py (Фильтры, Сортировки и Срезы)
# ==========================================================


@pytest.fixture
def sample_planes():
    return [
        Aeroplane("A1", "Canada", 100.0, 5000.0),
        Aeroplane("B2", "Spain", 300.0, 8000.0),
        Aeroplane("C3", "Canada", 200.0, 12000.0),
    ]


def test_filter_aeroplanes(sample_planes):
    """Тест фильтрации по строке стран (Критерий №9)."""
    res = filter_aeroplanes(sample_planes, "Spain")
    assert len(res) == 1
    assert res[0].callsign == "B2"

    res_multi = filter_aeroplanes(sample_planes, "Canada, Spain")
    assert len(res_multi) == 3
    assert len(filter_aeroplanes(sample_planes, "")) == 3


def test_get_aeroplanes_by_altitude(sample_planes):
    """Тест фильтрации по диапазону высот (Критерий №9)."""
    res = get_aeroplanes_by_altitude(sample_planes, "4000 - 9000")
    assert len(res) == 2

    assert len(get_aeroplanes_by_altitude(sample_planes, "сломанный диапазон")) == 3
    assert len(get_aeroplanes_by_altitude(sample_planes, "")) == 3


def test_sorting_and_top(sample_planes):
    """Тест корректности сортировки DESC и выборки Топ-N (Критерий №8)."""
    sorted_list = sort_aeroplanes(sample_planes)
    assert sorted_list[0].velocity == 300.0
    assert sorted_list[2].velocity == 100.0

    top_2 = get_top_aeroplanes(sorted_list, 2)
    assert len(top_2) == 2
    assert top_2[0].callsign == "B2"


def test_print_aeroplanes(sample_planes):
    """Тест функции вывода на экран (покрытие ветки печати)."""
    print_aeroplanes(sample_planes)
    print_aeroplanes([])  # Тестируем ветку пустого списка


# ==========================================================
# 4. ТЕСТ ИНТЕРФЕЙСА (Покрывает utils.py до максимума)
# ==========================================================


def test_user_interaction_mocked():
    """Эмуляция ввода пользователя для покрытия логики в user_interaction."""
    inputs = ["Canada", "2", "Canada", "4000 - 15000"]

    with patch("builtins.input", side_effect=inputs), patch(
            "src.api.APIAdapter.get_aeroplanes"
    ) as mock_get, patch("src.savers.JSONSaver.add_aeroplane") as _:
        # Имитируем, что API вернул пустой, но корректный ответ для обхода сети
        user_interaction()
        assert mock_get.called


def test_api_adapter_mocked():
    """Тест для покрытия ветки успешного выполнения APIAdapter."""
    from src.api import APIAdapter

    with patch("src.api.get") as mock_get:
        # Имитируем ответы от двух серверов (Nominatim и OpenSky)
        mock_response_geo = MagicMock()
        mock_response_geo.json.return_value = {"boundingbox": ["10", "20", "30", "40"]}

        mock_response_sky = MagicMock()
        mock_response_sky.json.return_value = {"states": []}

        mock_get.side_effect = [mock_response_geo, mock_response_sky]

        adapter = APIAdapter()
        adapter.get_aeroplanes("Canada")

        assert adapter.aeroplanes == {"states": []}
