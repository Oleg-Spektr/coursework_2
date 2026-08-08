def filter_aeroplanes(aeroplanes: list, filter_words: str) -> list:
    """Фильтрация самолетов по странам регистрации."""
    if not filter_words:
        return aeroplanes
    countries = [c.strip().lower() for c in filter_words.replace(',', ' ').split() if c.strip()]
    return [p for p in aeroplanes if p.origin_country.lower() in countries]


def get_aeroplanes_by_altitude(aeroplanes: list, altitude_range: str) -> list:
    """Фильтрация по диапазону высот (формат: 'Мин - Макс')."""
    if not altitude_range or '-' not in altitude_range:
        return aeroplanes
    try:
        min_alt, max_alt = map(float, altitude_range.split('-'))
        return [p for p in aeroplanes if min_alt <= p.altitude <= max_alt]
    except (ValueError, TypeError):
        return aeroplanes


# ДОРАБОТКА ПРЕПОДАВАТЕЛЯ: Явная сортировка по высоте через lambda
def sort_aeroplanes_by_altitude(aeroplanes: list) -> list:
    return sorted(aeroplanes, key=lambda p: p.altitude, reverse=True)


# ДОРАБОТКА ПРЕПОДАВАТЕЛЯ: Получение топ N по высоте
def get_top_aeroplanes(aeroplanes: list, top_n: int) -> list:
    return sort_aeroplanes_by_altitude(aeroplanes)[:top_n]


def print_aeroplanes(aeroplanes: list) -> None:
    """Вывод таблицы в консоль."""
    if not aeroplanes:
        print("Нет данных для отображения по заданным фильтрам.")
        return
    print("-" * 75)
    print(f"{'№':<3} | {'Позывной':<10} | {'Страна регистрации':<20} | {'Скорость':<12} | {'Высота':<10}")
    print("-" * 75)
    for i, p in enumerate(aeroplanes, 1):
        print(f"{i:<3} | {p.callsign:<10} | {p.origin_country:<20} | {p.velocity:<6.1f} м/с  | {p.altitude:<6.1f} м")
    print("-" * 75)


def user_interaction():
    """Главная функция интерфейса, которую вызывает main.py."""
    from src.api import FlightRadarAdapter
    from src.savers import JSONSaver

    api = FlightRadarAdapter()
    json_saver = JSONSaver()

    print("=== ЗАПУСК СИСТЕМЫ МОНИТОРИНГА АВИАЦИИ ===")
    country = input("Введите название страны на английском (например, Spain): ").strip()
    if not country:
        return

    print("Запрос информации о самолетах...")
    api.get_aeroplanes(country)

    if not api.aeroplanes:
        print("Не удалось получить информацию.")
        return

    from src.aeroplane import Aeroplane
    aeroplanes = Aeroplane.cast_to_object_list(api.aeroplanes)
    print(f"Успешно обработано самолетов: {len(aeroplanes)}")

    try:
        for p in aeroplanes:
            json_saver.add_aeroplane(p.to_dict())
    except Exception as e:
        print(f"Предупреждение при записи в файл: {e}")

    try:
        top_n = int(input("Введите количество самолетов для вывода в топ N: ").strip())
    except ValueError:
        top_n = 5

    filter_words = input("Введите названия стран для фильтрации по стране регистрации: ").strip()
    altitude_range = input("Введите диапазон высот полета (Пример: 5000 - 15000): ").strip()

    filtered_aeroplanes = filter_aeroplanes(aeroplanes, filter_words)
    ranged_aeroplanes = get_aeroplanes_by_altitude(filtered_aeroplanes, altitude_range)
    top_aeroplanes = get_top_aeroplanes(ranged_aeroplanes, top_n)

    print_aeroplanes(top_aeroplanes)
