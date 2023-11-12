from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# старт
def get_start_markup() -> ReplyKeyboardMarkup:
    start_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    start_markup.add(KeyboardButton("Старт регистрации"))
    return start_markup