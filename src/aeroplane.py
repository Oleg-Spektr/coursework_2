class Aeroplane:
    """Класс самолета с явным указанием типов и валидацией данных (Критерий №3)."""

    def __init__(
        self, callsign: str, origin_country: str, velocity: float, altitude: float
    ):
        # Строгое приведение типов для защиты структуры объекта
        self._callsign: str = str(callsign).strip() if callsign else "UNKNOWN"
        self._origin_country: str = (
            str(origin_country).strip() if origin_country else "Unknown"
        )
        self._velocity: float = float(velocity) if velocity is not None else 0.0
        self._altitude: float = float(altitude) if altitude is not None else 0.0

    @property
    def callsign(self) -> str:
        return self._callsign

    @property
    def origin_country(self) -> str:
        return self._origin_country

    @property
    def velocity(self) -> float:
        return self._velocity

    @property
    def altitude(self) -> float:
        return self._altitude

    @classmethod
    def cast_to_object_list(cls, opensky_json: dict) -> list:
        object_list = []
        if not opensky_json or not isinstance(opensky_json, dict):
            return object_list

        states = opensky_json.get("states")
        if not states or not isinstance(states, list):
            return object_list

        for plane_data in states:
            try:
                obj = cls(
                    callsign=plane_data[1],
                    origin_country=plane_data[2],
                    velocity=plane_data[9],
                    altitude=plane_data[7],
                )
                object_list.append(obj)
            except (IndexError, TypeError):
                continue  # Пропускаем поврежденные строки данных из API
        return object_list

    def to_dict(self) -> dict:
        return {
            "callsign": self.callsign,
            "origin_country": self.origin_country,
            "velocity": self.velocity,
            "altitude": self.altitude,
        }

    # Магические методы для корректного сравнения по скорости и высоте (Критерий №4)
    def __lt__(self, other):
        if not isinstance(other, Aeroplane):
            return NotImplemented
        if self._velocity == other._velocity:
            return self._altitude < other._altitude
        return self._velocity < other._velocity

    def __eq__(self, other):
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self._velocity == other._velocity and self._altitude == other._altitude

    def __le__(self, other):
        return self < other or self == other

    def __repr__(self):
        return f"Aeroplane({self.callsign}, V: {self.velocity}, H: {self.altitude})"
