from abc import ABC, abstractmethod

from requests import RequestException, get


class BaseAPIConnector(ABC):
    """Абстрактный класс для работы с API (Требование SOLID и критерия №1)."""

    @abstractmethod
    def get_aeroplanes(self, country: str) -> None:
        pass


class APIAdapter(BaseAPIConnector):
    """Адаптер для интеграции с внешними сервисами Nominatim и OpenSky."""

    def __init__(self) -> None:
        self.openstreetmap_url = "https://openstreetmap.org"
        self.opensky_url = "https://opensky-network.org?"
        self.aeroplanes = None

    def get_aeroplanes(self, country: str) -> None:
        headers_nominatim = {"User-Agent": "test-app/1.0"}
        params_nominatim = {"country": country, "format": "json", "limit": 1}

        try:
            response = get(
                url=self.openstreetmap_url,
                params=params_nominatim,
                headers=headers_nominatim,
            )
            response.raise_for_status()
            data = response.json()
        except (RequestException, ValueError) as e:
            print(f"Ошибка при запросе к географическому сервису: {e}")
            self.aeroplanes = {"states": []}
            return

        if not data or not isinstance(data, list):
            print(f"Страна '{country}' не найдена.")
            self.aeroplanes = {"states": []}
            return

        geo_coordinates = data[0].get("boundingbox")
        if not geo_coordinates or len(geo_coordinates) < 4:
            print("Не удалось извлечь координаты границ.")
            self.aeroplanes = {"states": []}
            return

        params = {
            "lamin": float(geo_coordinates[0]),
            "lamax": float(geo_coordinates[1]),
            "lomin": float(geo_coordinates[2]),
            "lomax": float(geo_coordinates[3]),
        }

        try:
            response = get(url=self.opensky_url, params=params)
            response.raise_for_status()
            self.aeroplanes = response.json()
        except (RequestException, ValueError) as e:
            print(f"Ошибка при получении данных о самолетах: {e}")
            self.aeroplanes = {"states": []}
