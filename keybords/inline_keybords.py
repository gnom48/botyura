from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from emoji import emojize
import datetime
from aiogram.dispatcher.filters.state import State
from bot import state_machine


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


# почему плохо
def get_bed_result(from_state: State) -> InlineKeyboardButton:
    buttons = [
        InlineKeyboardButton("Объект плохой", callback_data="object"),
    ]
    if from_state == state_machine.WorkStates.deal_retult:
        buttons.append(InlineKeyboardButton("Продавец мудак", callback_data="saller"))
    elif from_state == state_machine.WorkStates.show_result:
        buttons.append(InlineKeyboardButton("Покупатель мудак", callback_data="client"))
    elif from_state == state_machine.WorkStates.deposit_result:
        buttons.append(InlineKeyboardButton("Клиент мудак", callback_data="depositer"))
    elif from_state == state_machine.WorkStates.meet_new_object_result:
        buttons.append(InlineKeyboardButton("Презентер мудак", callback_data="meeter"))
    buttons.append(InlineKeyboardButton("Продавец не явился", callback_data="nb"))
    buttons.append(InlineKeyboardButton("Другое", callback_data="other"))

    inline_markup = InlineKeyboardMarkup(row_width=3)
    inline_markup.add(*buttons)

    return inline_markup


# кнопка-ссылка на видео
def get_video_link(link: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    vb = InlineKeyboardButton(text='Смотреть материал 🎥', url=link)
    kb.add(vb)

    return kb