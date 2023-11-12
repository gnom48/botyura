import random
from difflib import SequenceMatcher


# вернет "лучшее" совпадение из книги по контексту проблемы сотрудника
def get_advice_from_book() -> str:
    best_tip = None
    highest_similarity = 0.0

    for tip in "сюда подставим хранилище выдержек из книги":
        similarity = SequenceMatcher(None, tip, "сюда подставим проблему с которой столкунулся работник").ratio()
        if similarity > highest_similarity:
            highest_similarity = similarity
            best_tip = tip

    return best_tip