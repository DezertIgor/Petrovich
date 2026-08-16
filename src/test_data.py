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
