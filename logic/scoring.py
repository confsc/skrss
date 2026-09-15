def check_answer(spec, user_answer):
    """Проверяет ответ ученика. True — верно."""
    if not user_answer:
        return False

    user = user_answer.strip().replace(",", ".").replace(" ", "")
    correct = spec["answer"].strip().replace(",", ".").replace(" ", "")

    spec_type = spec.get("type", "text")

    if spec_type == "choice":
        return user.lower() == correct.lower()

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

    # text по умолчанию
    return user.lower() == correct.lower()


def get_key_specs(station, count=5):
    """Возвращает до `count` ключевых ТТХ (weight == 1.0)."""
    key = [s for s in station["specs"] if s.get("weight", 0.5) == 1.0]
    return key[:count]
