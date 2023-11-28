from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# старт
def get_start_markup() -> ReplyKeyboardMarkup:
    start_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    start_markup.add(KeyboardButton("Старт регистрации"))
    return start_markup


# виды сделок частное
def get_meeting_private_markup() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton("Квартира"),
        KeyboardButton("Земля"),
        KeyboardButton("Дом"),
        KeyboardButton("Назад"),
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)


# виды сделок коммерческое
def get_meeting_commercial_markup() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton("Офис"),
        KeyboardButton("Магазин"),
        KeyboardButton("Другое"),
        KeyboardButton("Назад"),
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)


# как прошла сделка
def get_meeting_result_markup() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton("Хорошо"),
        KeyboardButton("Плохо"),
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)


# все понятно?
def get_is_all_materials_ok_markup() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton("Спасибо, все понятно"),
        KeyboardButton("Нужна еще информация"),
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)


# общее состояние риелтора - не буду работать
def get_rest_markup() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton("Устал"),
        KeyboardButton("Больничный"),
        KeyboardButton("Отпуск"),
        KeyboardButton("Назад"),
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)


# провал сделки TODO: адаптировать под показ
def get_bad_deal_result() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton("Плохой объект"),
        KeyboardButton("Продавец неграмотный"),
        KeyboardButton("Моя ошибка"),
        KeyboardButton("Назад"),
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)
