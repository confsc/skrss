import random


def check_answer(spec, user_answer):
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

    return user.lower() == correct.lower()


def get_key_specs(station, count=5):
    all_specs = list(station["specs"])
    if len(all_specs) <= count:
        result = list(all_specs)
        random.shuffle(result)
        return result
    return random.sample(all_specs, count)


def get_quiz_specs(station, total=7, key_count=3):
    all_specs = list(station["specs"])
    key = [s for s in all_specs if s.get("weight", 0.5) == 1.0]

    result = []

    if len(key) >= key_count:
        result.extend(random.sample(key, key_count))
    else:
        result.extend(key)

    remaining_pool = [s for s in all_specs if s not in result]
    remaining = total - len(result)
    if remaining > 0 and remaining_pool:
        result.extend(random.sample(remaining_pool, min(remaining, len(remaining_pool))))

    random.shuffle(result)
    return result
