from abc import ABC, abstractmethod
from requests import get, RequestException


class BaseAPIConnector(ABC):
    """Абстрактный класс для работы с API (SOLID)."""

    @abstractmethod
    def get_aeroplanes(self, country: str) -> None:
        pass


class FlightRadarAdapter(BaseAPIConnector):
    """Класс-адаптер для интеграции с авиа-API (OpenSky с защитным fallback-режимом)."""

    def __init__(self) -> None:
        # Собираем правильный адрес из частей, чтобы избежать системных автозамен текста в IDE
        parts = ["https://", "nominatim.", "openstreetmap.org", "/search"]
        self.openstreetmap_url = "".join(parts)
        # Возвращаем оригинальный OpenSky URL, запрошенный в рамках курсовой
        self.opensky_url = 'https://opensky-network.org?'
        self.aeroplanes = None

    def get_aeroplanes(self, country: str) -> None:
        headers_nominatim = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        params_nominatim = {
            'country': country,
            'format': 'json',
            'limit': 1
        }

        try:
            response = get(url=self.openstreetmap_url, params=params_nominatim, headers=headers_nominatim)
            response.raise_for_status()
            data = response.json()
        except (RequestException, ValueError) as e:
            print(f"Ошибка географического сервиса: {e}")
            self._set_mock_data()
            return

        if not data or not isinstance(data, list):
            print(f"Страна '{country}' не найдена в базе данных.")
            self._set_mock_data()
            return

        # Извлекаем координаты boundingbox: [ymin, ymax, xmin, xmax]
        geo_coordinates = data[0].get('boundingbox')
        if not geo_coordinates or len(geo_coordinates) < 4:
            print("Не удалось извлечь координаты границ.")
            self._set_mock_data()
            return

        # Параметры для фильтрации самолетов по их географическим координатам
        params = {
            'lamin': float(geo_coordinates[0]),
            'lamax': float(geo_coordinates[1]),
            'lomin': float(geo_coordinates[2]),
            'lomax': float(geo_coordinates[3]),
        }

        # Делаем реальный сетевой запрос к авиа-API без принудительных исключений
        try:
            print(f"Отправка реального сетевого запроса к OpenSky API для зоны {country}...")
            response = get(url=self.opensky_url, params=params, timeout=7)

            # Если сервер вернул ошибку (например, 403 Forbidden из-за лимитов на размер зоны страны)
            response.raise_for_status()

            # Если запрос прошёл успешно, сохраняем реальные живые данные
            self.aeroplanes = response.json()
            print("Данные успешно получены из сети в реальном времени!")

        except (RequestException, ValueError) as e:
            # Уходим в демо-режим ТОЛЬКО в случае реальной ошибки сети или блокировки 403
            print(f"\n[OpenSky API] Сервер ограничил доступ или вернул ошибку: {e}")
            print("[Fallback Режим] Автоматическая подгрузка отказоустойчивых демонстрационных данных...")
            self._set_mock_data()

    def _set_mock_data(self) -> None:
        """Имитация ответа API для бесперебойной демонстрации шагов 2, 3 и 4."""
        self.aeroplanes = {
            "states": [
                ["fr-101", "SU2112  ", "Russian Federation", 1720448000, 1720448000, 30.5, 50.7, 250.0, False, 250.0, 0,
                 None, None, 11200.0, "777", False, 0],
                ["fr-102", "LH9981  ", "Germany", 1720448101, 1720448101, 10.2, 53.1, 215.3, False, 215.3, 0, None,
                 None, 10500.0, "320", False, 0],
                ["fr-103", "AFR022  ", "France", 1720448102, 1720448102, 2.5, 49.0, 198.0, False, 198.0, 0, None, None,
                 9800.0, "330", False, 0],
                ["fr-104", "UAE011  ", "United Arab Emirates", 1720448103, 1720448103, 54.1, 24.0, 270.8, False, 270.8,
                 0, None, None, 12100.0, "380", False, 0],
                ["fr-105", "IBE3144 ", "Spain", 1720448104, 1720448104, -3.7, 40.4, 10200.0, False, 210.5, 0, None,
                 None, 10200.0, "321", False, 0]
            ]
        }
