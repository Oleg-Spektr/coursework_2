# src/utils.py
from src.api import FlightRadarAdapter  # Жестко подтягиваем новый адаптер
from src.aeroplane import Aeroplane
from src.savers import JSONSaver


def filter_aeroplanes(aeroplanes: list, filter_words: str) -> list:
    """Улучшенная фильтрация по странам регистрации (устойчивая к пробелам)."""
    if not filter_words:
        return aeroplanes
    # Очищаем входящую строку от запятых, бьем по пробелам и переводим в нижний регистр
    target_countries = [c.strip().lower() for c in filter_words.replace(',', ' ').split() if c.strip()]

    filtered_list = []
    for p in aeroplanes:
        # Безопасно извлекаем страну, очищаем от пробелов (в ответах API часто бывает "Spain  ")
        p_country = str(p.origin_country).strip().lower()
        if p_country in target_countries:
            filtered_list.append(p)

    return filtered_list


def get_aeroplanes_by_altitude(aeroplanes: list, altitude_range: str) -> list:
    """Фильтрация по диапазону высот (формат: 'Мин - Макс')."""
    if not altitude_range or '-' not in altitude_range:
        return aeroplanes
    try:
        min_alt, max_alt = map(float, altitude_range.split('-'))
        return [p for p in aeroplanes if min_alt <= p.altitude <= max_alt]
    except (ValueError, TypeError):
        return aeroplanes


def sort_aeroplanes(aeroplanes: list) -> list:
    """Сортировка самолетов по убыванию характеристик DESC."""
    return sorted(aeroplanes, reverse=True)


def get_top_aeroplanes(aeroplanes: list, top_n: int) -> list:
    """Получение первых N элементов."""
    return aeroplanes[:top_n]


def print_aeroplanes(aeroplanes: list) -> None:
    """Вывод таблицы в консоль."""
    if not aeroplanes:
        print("Нет данных для отображения.")
        return
    print("-" * 75)
    print(f"{'№':<3} | {'Позывной':<10} | {'Страна регистрации':<20} | {'Скорость':<12} | {'Высота':<10}")
    print("-" * 75)
    for i, p in enumerate(aeroplanes, 1):
        print(f"{i:<3} | {p.callsign:<10} | {p.origin_country:<20} | {p.velocity:<6.1f} м/с  | {p.altitude:<6.1f} м")
    print("-" * 75)


def user_interaction():
    """Главная функция интерфейса, которую вызывает main.py."""
    # ИСПРАВЛЕНО: Создаем экземпляр правильного адаптера Flightradar24
    api = FlightRadarAdapter()
    json_saver = JSONSaver()

    print("=== ЗАПУСК СИСТЕМЫ МОНИТОРИНГА АВИАЦИИ (FLIGHTRADAR24) ===")
    country = input("Введите название страны на английском (например, Spain): ").strip()
    if not country:
        return

    print("Запрос информации о самолетах...")
    api.get_aeroplanes(country)

    if not api.aeroplanes:
        print("Не удалось получить информацию.")
        return

    # Преобразуем полученные данные в объекты класса
    aeroplanes = Aeroplane.cast_to_object_list(api.aeroplanes)
    print(f"Успешно обработано самолетов: {len(aeroplanes)}")

    # Сохраняем в JSON-файл базы данных
    for p in aeroplanes:
        json_saver.add_aeroplane(p.to_dict())

    try:
        top_n = int(input("Введите количество самолетов для вывода в топ N: ").strip())
    except ValueError:
        top_n = 5

    filter_words = input("Введите названия стран для фильтрации по стране регистрации: ").strip()
    altitude_range = input("Введите диапазон высот полета (Пример: 10000 - 15000): ").strip()

    # Цепочка обработки
    filtered_aeroplanes = filter_aeroplanes(aeroplanes, filter_words)
    ranged_aeroplanes = get_aeroplanes_by_altitude(filtered_aeroplanes, altitude_range)
    sorted_aeroplanes = sort_aeroplanes(ranged_aeroplanes)
    top_aeroplanes = get_top_aeroplanes(sorted_aeroplanes, top_n)

    print_aeroplanes(top_aeroplanes)
