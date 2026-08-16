import secrets
import string

CYRILLIC = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
LATIN = string.ascii_letters
DIGITS = string.digits
RANDOM_STRING_LENGTH = 12


def _random_string(use_cyrillic: bool) -> str:
    """Создать строку с обязательными группами символов и внутренним подчёркиванием."""
    required_alphabets = [LATIN, DIGITS]
    if use_cyrillic:
        required_alphabets.insert(0, CYRILLIC)

    required_characters = [secrets.choice(alphabet) for alphabet in required_alphabets]
    required_characters.append("_")

    alphabet = "".join(required_alphabets)
    characters = [secrets.choice(alphabet) for _ in range(RANDOM_STRING_LENGTH)]
    positions = secrets.SystemRandom().sample(range(1, RANDOM_STRING_LENGTH - 1), len(required_characters))

    for position, character in zip(positions, required_characters, strict=True):
        characters[position] = character

    return "".join(characters)


random_student_name = _random_string(use_cyrillic=True)
random_student_email = _random_string(use_cyrillic=False).lower()
random_updated_student_name = _random_string(use_cyrillic=True)
random_updated_student_email = _random_string(use_cyrillic=False).lower()
random_student_phone = "".join(secrets.choice(DIGITS) for _ in range(10))

# Редактируемые шаблоны тестовых данных студента.
student_name = f"Студент_{random_student_name}"
student_email = f"student_{random_student_email}@test.com"
student_phone_no = f"+7{random_student_phone}"
student_gender = "male"
student_status = 1

updated_student_name = f"Обновлённый_студент_{random_updated_student_name}"
updated_student_email = f"updated_student_{random_updated_student_email}@test.com"
updated_student_gender = "female"
updated_student_status = 1
