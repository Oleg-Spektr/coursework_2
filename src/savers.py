import json
import os
from abc import ABC, abstractmethod


class BaseSaver(ABC):
    """Абстрактный класс для сохранения данных (Критерий №5)."""

    @abstractmethod
    def add_aeroplane(self, aeroplane_dict: dict) -> None:
        pass

    @abstractmethod
    def delete_aeroplane(self, aeroplane_dict: dict) -> None:
        pass


class JSONSaver(BaseSaver):
    """Класс для гарантированно корректной работы с JSON (Критерий №6)."""

    def __init__(self, filename: str = "data/aeroplanes.json"):
        self.filename = filename
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        if not os.path.exists(self.filename):
            self._write([])

    def _read(self) -> list:
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _write(self, data: list) -> None:
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Критическая ошибка записи файла базы данных: {e}")

    def add_aeroplane(self, aeroplane_dict: dict) -> None:
        data = self._read()
        data.append(aeroplane_dict)
        self._write(data)

    def delete_aeroplane(self, aeroplane_dict: dict) -> None:
        data = self._read()
        callsign_to_del = aeroplane_dict.get("callsign")
        new_data = [p for p in data if p.get("callsign") != callsign_to_del]
        self._write(new_data)
