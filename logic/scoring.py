import random


UNIT_OPTIONS = {
    "ГГц": ["ТГц", "ГГц", "МГц", "кГц"],
    "МГц": ["ГГц", "МГц", "кГц", "Гц"],
    "кГц": ["МГц", "кГц", "Гц", "мГц"],
    "Гц": ["кГц", "Гц", "мГц", "мкГц"],
    "Вт": ["кВт", "Вт", "мВт", "дБВт"],
    "кВт": ["МВт", "кВт", "Вт", "мВт"],
    "мВт": ["Вт", "мВт", "мкВт", "дБм"],
    "дБВт": ["дБВт", "Вт", "кВт", "мВт"],
    "дБм": ["дБм", "дБВт", "Вт", "мВт"],
    "Мбит/с": ["Гбит/с", "Мбит/с", "кбит/с", "бит/с"],
    "кбит/с": ["Мбит/с", "кбит/с", "бит/с", "Гбит/с"],
    "бит/с": ["кбит/с", "бит/с", "Мбит/с", "Гбит/с"],
    "Мбит/сек": ["Гбит/сек", "Мбит/сек", "кбит/сек", "бит/сек"],
    "кбит/сек": ["Мбит/сек", "кбит/сек", "бит/сек", "Гбит/сек"],
    "км": ["км", "м", "см", "мм"],
    "м": ["км", "м", "см", "мм"],
    "см": ["м", "см", "мм", "мкм"],
    "с": ["мин", "с", "мс", "мкс"],
    "сек": ["мин", "сек", "мс", "мкс"],
    "мин": ["ч", "мин", "с", "мс"],
    "ч": ["сут", "ч", "мин", "с"],
    "лет": ["лет", "мес", "нед", "дн"],
    "град": ["град", "рад", "мин", "сек"],
    "К": ["К", "мК", "°С", "°F"],
    "дБ": ["дБ", "дБм", "дБВт", "раз"],
    "дБ/К": ["дБ/К", "К", "дБ", "раз"],
    "В": ["кВ", "В", "мВ", "мкВ"],
    "кг": ["т", "кг", "г", "мг"],
    "кВА": ["МВА", "кВА", "ВА", "мВА"],
    "%": ["%", "доли", "ppm", "‰"],
    "мкВ": ["мВ", "мкВ", "нВ", "В"],
    "дБ мкВ": ["дБ мкВ", "мкВ", "мВ", "В"],
    "дБ/мкВ": ["дБ/мкВ", "мкВ", "мВ", "В"],
    "мс": ["с", "мс", "мкс", "нс"],
    "ФВ": ["ФВ", "м", "км", "см"],
    "от Рном": ["от Рном", "от Рмакс", "от Рмин", "абс"],
    "мГц": ["Гц", "мГц", "кГц", "МГц"],
    "симв/с": ["симв/с", "Мсимв/с", "ксимв/с", "Гсимв/с"],
}


def get_unit_options(unit):
    if not unit:
        return []
    if unit in UNIT_OPTIONS:
        return UNIT_OPTIONS[unit]
    return [unit]


def check_answer(spec, user_answer, user_unit=None):
    if not user_answer:
        return False

    if spec.get("type") == "choice":
        user = user_answer.strip()
        correct = spec["answer"].strip()
        return user.lower() == correct.lower()

    correct_unit = spec.get("unit", "").strip()
    if correct_unit:
        if not user_unit:
            return False
        if user_unit.strip().lower() != correct_unit.lower():
            return False

    user = user_answer.strip().replace(",", ".").replace(" ", "")
    correct = spec["answer"].strip().replace(",", ".").replace(" ", "")

    spec_type = spec.get("type", "text")

    if spec_type == "number":
        try:
            u = float(user)
            c = float(correct)
        except ValueError:
            return False
        tol = float(spec.get("tolerance", 0))
        return abs(u - c) <= tol

    if spec_type == "range":
        try:
            u_parts = user.split("-")
            c_parts = correct.split("-")
            if len(u_parts) != 2 or len(c_parts) != 2:
                return False
            u1, u2 = float(u_parts[0]), float(u_parts[1])
            c1, c2 = float(c_parts[0]), float(c_parts[1])
            return abs(u1 - c1) <= 1 and abs(u2 - c2) <= 1
        except ValueError:
            return False

    return user.lower() == correct.lower()


def _calculate_count(total):
    calculated = round(0.7 * total)
    count = max(7, min(15, calculated))
    if count > total:
        count = total
    return count


def get_key_specs(station, count=None):
    all_specs = list(station["specs"])
    total = len(all_specs)
    if count is None:
        count = _calculate_count(total)
    if count >= total:
        result = list(all_specs)
        random.shuffle(result)
        return result
    return random.sample(all_specs, count)


def get_quiz_specs(station, total=None):
    all_specs = list(station["specs"])
    total_count = len(all_specs)

    if total is None:
        total = _calculate_count(total_count)

    key = [s for s in all_specs if s.get("weight", 0.5) == 1.0]
    result = []

    if len(key) >= total:
        result.extend(random.sample(key, total))
        random.shuffle(result)
        return result

    result.extend(key)
    remaining_pool = [s for s in all_specs if s not in result]
    remaining = total - len(result)
    if remaining > 0 and remaining_pool:
        result.extend(random.sample(remaining_pool, min(remaining, len(remaining_pool))))

    random.shuffle(result)
    return result
