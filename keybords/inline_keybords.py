from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from emoji import emojize
import datetime


# выбор пола
def get_gender_kb() -> InlineKeyboardMarkup:
    inline_kb_gender = InlineKeyboardMarkup(row_width=2)
    inline_kb_gender.add(InlineKeyboardButton(text='М', callback_data='М'), InlineKeyboardButton(text='Ж', callback_data='Ж'))
    return inline_kb_gender

    
# вид риелтора
def get_realtors_type_kb() -> InlineKeyboardMarkup:
    inline_kb_realtors_type = InlineKeyboardMarkup(row_width=1)
    inline_kb_realtors_type.add(InlineKeyboardButton(text='Риелтор жилой недвижимости', callback_data='residential'), InlineKeyboardButton(text='Риелтор комерческой недвижимости', callback_data='commercial'))
    return inline_kb_realtors_type


# главное меню выбора активностей
def get_inline_menu_markup() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(emojize(":bar_chart: Аналитика"), callback_data="analytics"),
        InlineKeyboardButton(emojize(":handshake: Встреча"), callback_data="meeting"),
        InlineKeyboardButton(emojize(":telephone_receiver: Обзвон"), callback_data="call"),
        InlineKeyboardButton(emojize(":house: Показ"), callback_data="show"),
        InlineKeyboardButton(emojize("🔍Поиск"), callback_data="search"),
        InlineKeyboardButton(emojize(":newspaper: Расклейка"), callback_data="flyer"),
        InlineKeyboardButton(emojize("📈Сделка"), callback_data="deal"),
        InlineKeyboardButton(emojize(":money_bag: Задаток"), callback_data="deposit"),
        InlineKeyboardButton(emojize("🥴Не могу работать"), callback_data="no_work"),
    ]

    inline_markup = InlineKeyboardMarkup(row_width=2)
    inline_markup.add(*buttons)

    return inline_markup


# ветка встреча
def get_inline_meeting_markup() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton("Квартира", callback_data="apartment"),
        InlineKeyboardButton("Земля", callback_data="lend"),
        InlineKeyboardButton("Дом", callback_data="house"),
        InlineKeyboardButton("Назад", callback_data="bsck"),
    ]

    inline_markup = InlineKeyboardMarkup(row_width=2)
    inline_markup.add(*buttons)

    return inline_markup

