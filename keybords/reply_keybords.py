from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# старт
def get_start_markup() -> ReplyKeyboardMarkup:
    start_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    start_markup.add(KeyboardButton("Старт регистрации"))
    return start_markup


# виды сделок
def get_meeting_markup() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton("Квартира"),
        KeyboardButton("Земля"),
        KeyboardButton("Дом"),
        KeyboardButton("Назад"),
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)


# как прошла сделка
def get_meeting_result_markup() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton("Хорошо"),
        KeyboardButton("50/50"),
        KeyboardButton("Плохо"),
        KeyboardButton("Есть возражения"),
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)


# общее состояние риелтора
def get_meeting_rest_markup() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton("Устал"),
        KeyboardButton("Отпуск"),
        KeyboardButton("Назад"),
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)
