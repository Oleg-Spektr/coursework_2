import pytest
import os
from unittest.mock import MagicMock, patch
from src.aeroplane import Aeroplane
from src.savers import JSONSaver
from src.utils import (
    filter_aeroplanes,
    get_aeroplanes_by_altitude,
    sort_aeroplanes,
    get_top_aeroplanes,
    print_aeroplanes,
    user_interaction
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


def test_aeroplane_comparison():
    """Тест магических методов сравнения самолетов строго ПО ВЫСОТЕ (Критерий №8)."""
    plane_low = Aeroplane("A", "Test", 300.0, 5000.0)  # Быстрый, но низко
    plane_high = Aeroplane("B", "Test", 100.0, 9000.0)  # Медленный, но высоко
    plane_equal_alt_faster = Aeroplane("C", "Test", 400.0, 5000.0)  # Высота как у A, но скорость выше

    # Теперь plane_high больше plane_low, так как высота 9000 > 5000
    assert plane_low < plane_high
    # При равной высоте (5000) plane_equal_alt_faster больше plane_low, так как скорость 400 > 300
    assert plane_low < plane_equal_alt_faster
    assert plane_high > plane_low
    assert plane_low == Aeroplane("A", "Test", 300.0, 5000.0)
    assert (plane_low == "not an aeroplane") is False


def test_cast_to_object_list():
    """Тест фабричного метода преобразования структуры OpenSky."""
    raw_response = {
        "states": [
            ["4b1812", "THY1812", "Turkey", 1720448120, 1720448120, 29.12, 40.98, 10200.5, False, 210.4, 120, None,
             None, 10200.5, "3144", False, 0]
        ]
    }
    obj_list = Aeroplane.cast_to_object_list(raw_response)
    assert len(obj_list) == 1
    assert obj_list[0].callsign == "THY1812"
    assert obj_list[0].origin_country == "Turkey"
    assert obj_list[0].velocity == 210.4
    assert obj_list[0].altitude == 10200.5

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
    """Тест добавления, дублирования и удаления из JSON (Критерий №6)."""
    plane_dict = {"callsign": "TEST777", "origin_country": "Spain", "velocity": 150.0, "altitude": 8000.0}
    assert temp_json_saver._read() == []

    # Добавление уникального
    temp_json_saver.add_aeroplane(plane_dict)
    assert len(temp_json_saver._read()) == 1

    # Попытка добавить дубликат (должна проигнорироваться)
    temp_json_saver.add_aeroplane(plane_dict)
    assert len(temp_json_saver._read()) == 1

    # Удаление
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
        Aeroplane("C3", "Canada", 200.0, 12000.0)
    ]


def test_filter_aeroplanes(sample_planes):
    """Тест фильтрации по странам."""
    res = filter_aeroplanes(sample_planes, "Spain")
    assert len(res) == 1
    assert res[0].callsign == "B2"

    res_multi = filter_aeroplanes(sample_planes, "Canada, Spain")
    assert len(res_multi) == 3
    assert len(filter_aeroplanes(sample_planes, "")) == 3


def test_get_aeroplanes_by_altitude(sample_planes):
    """Тест фильтрации по диапазону высот."""
    res = get_aeroplanes_by_altitude(sample_planes, "4000 - 9000")
    assert len(res) == 2
    assert len(get_aeroplanes_by_altitude(sample_planes, "сломанный диапазон")) == 3
    assert len(get_aeroplanes_by_altitude(sample_planes, "")) == 3


def test_sorting_and_top(sample_planes):
    """Тест сортировки по убыванию высоты (DESC) и выборки Топ-N (Критерий №8)."""
    sorted_list = sort_aeroplanes(sample_planes)
    # Самым первым должен быть C3, так как у него максимальная высота 12000.0
    assert sorted_list[0].altitude == 12000.0
    assert sorted_list[0].callsign == "C3"

    # Последним должен быть A1 с высотой 5000.0
    assert sorted_list[-1].altitude == 5000.0

    top_2 = get_top_aeroplanes(sorted_list, 2)
    assert len(top_2) == 2
    assert top_2[0].callsign == "C3"


def test_print_aeroplanes(sample_planes):
    """Тест функции вывода на экран."""
    print_aeroplanes(sample_planes)
    print_aeroplanes([])


# ==========================================================
# 4. ТЕСТЫ ИНТЕРФЕЙСА И ИНТЕГРАЦИИ (FlightRadarAdapter)
# ==========================================================

def test_user_interaction_mocked():
    """Эмуляция ввода пользователя для покрытия user_interaction."""
    inputs = ["Canada", "2", "Canada", "4000 - 15000"]

    # Ссылаемся на правильное имя класса FlightRadarAdapter
    with patch('builtins.input', side_effect=inputs), \
            patch('src.api.FlightRadarAdapter.get_aeroplanes') as mock_get, \
            patch('src.savers.JSONSaver.add_aeroplane') as _:
        user_interaction()
        assert mock_get.called


def test_api_adapter_mocked():
    """Тест для покрытия ветки успешного выполнения FlightRadarAdapter."""
    from src.api import FlightRadarAdapter

    with patch('src.api.get') as mock_get:
        mock_response_geo = MagicMock()
        mock_response_geo.json.return_value = [{"boundingbox": ["10", "20", "30", "40"]}]

        mock_response_sky = MagicMock()
        # Возвращаем структуру, имитирующую реальный или демонстрационный ответ
        mock_response_sky.json.return_value = {
            "states": [
                ["fr-105", "IBE3144", "Spain", 1720448104, 1720448104, -3.7, 40.4, 10200.0, False, 210.5, 0, None, None,
                 10200.0, "321", False, 0]
            ]
        }

        mock_get.side_effect = [mock_response_geo, mock_response_sky]

        adapter = FlightRadarAdapter()
        adapter.get_aeroplanes("Spain")

        # Проверяем, что данные успешно записались в атрибут адаптера
        assert "states" in adapter.aeroplanes
        assert adapter.aeroplanes["states"][0][1] == "IBE3144"
