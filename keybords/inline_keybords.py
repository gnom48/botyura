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
        InlineKeyboardButton(emojize("📚База знаний"), callback_data="d_base"),
        InlineKeyboardButton(emojize("🥴Не могу работать"), callback_data="no_work")
    ]

    inline_markup = InlineKeyboardMarkup()
    
    for i in range(0, 8, 2): # добавляем первые 4 строки по 2 кнопке в каждой строке
        inline_markup.add(buttons[i], buttons[i+1])

    for i in range(8, 10): # добавляем последние 2 строки по 1 кнопке в каждой строке
        inline_markup.add(buttons[i])

    return inline_markup


# почему плохо
def get_bed_result(from_state: State) -> InlineKeyboardButton:
    buttons = []
    if from_state == state_machine.WorkStates.deal_retult: # сделка
        buttons.append(InlineKeyboardButton(text="Сделку перенесли", callback_data="Сделку перенесли"))
        buttons.append(InlineKeyboardButton(text="Клиент передумал", callback_data="Клиент передумал"))

    elif from_state == state_machine.WorkStates.show_result: # показ
        buttons.append(InlineKeyboardButton("Покупатель привередливый", callback_data="Покупатель привередливый"))
        buttons.append(InlineKeyboardButton("Встреча не состоялась", callback_data="Встреча не состоялась"))
        buttons.append(InlineKeyboardButton("Объект не понравился", callback_data="Объект не понравился"))

    elif from_state == state_machine.WorkStates.deposit_result: # задаток
        buttons.append(InlineKeyboardButton("Задаток перенесен", callback_data="Задаток перенесен"))
        buttons.append(InlineKeyboardButton("Задаток сорвался", callback_data="Задаток сорвался"))

    elif from_state == state_machine.WorkStates.meet_new_object_result: # встреча
        buttons.append(InlineKeyboardButton("Продавец привередливый", callback_data="Продавец привередливый"))
        buttons.append(InlineKeyboardButton("Объект плохой", callback_data="Объект не понравился"))

    elif from_state == state_machine.WorkStates.analytics_result or from_state == state_machine.WorkStates.search_result: # аналитика и поиск
        buttons.append(InlineKeyboardButton("Посмотреть материалы для аналитики", callback_data="get_materials_analytics"))
        buttons.append(InlineKeyboardButton("Посмотреть материалы для поиска", callback_data="get_materials_search"))
    
    buttons.append(InlineKeyboardButton("Другое", callback_data="other"))

    inline_markup = InlineKeyboardMarkup(row_width=1)
    inline_markup.add(*buttons)

    return inline_markup


# кнопка-ссылка на видео
def get_video_link(link: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    vb = InlineKeyboardButton(text='Смотреть материал 🎥', url=link)
    kb.add(vb)

    return kb


# кнопка-старт
def get_start_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    vb = InlineKeyboardButton(text="Старт регистрации", callback_data="Старт регистрации")
    kb.add(vb)

    return kb


# подписан ли договор
def get_is_signed_markup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    vb1 = InlineKeyboardButton(text="Подписали договор", callback_data="signed")
    vb2 = InlineKeyboardButton(text="Договор НЕ подписан", callback_data="unsigned")
    kb.add(vb1)
    kb.add(vb2)

    return kb
