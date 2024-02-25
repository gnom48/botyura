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
        buttons.append(InlineKeyboardButton("Почитать материалы по теме", callback_data="get_materials_analytics"))
    
    buttons.append(InlineKeyboardButton("Другое", callback_data="other"))

    inline_markup = InlineKeyboardMarkup(row_width=1)
    inline_markup.add(*buttons)

    return inline_markup


# кнопка-ссылка на видео
def get_video_link(link: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    vb = InlineKeyboardButton(text='Смотреть материал 📖', url=link)
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


# база знаний - корень
def get_knowledge_base_root_markup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    b = [
        InlineKeyboardButton(text="Аналитика", callback_data="analytics"),
        InlineKeyboardButton(text="Холодный звонок", callback_data="calls"),
        InlineKeyboardButton(text="Возражения клиентов", callback_data="bad_clients"),
        InlineKeyboardButton(text="Встреча", callback_data="meets"),
        InlineKeyboardButton(text="Показ", callback_data="shows"),
        InlineKeyboardButton(text="Договоры", callback_data="deals"),
        InlineKeyboardButton(text="Коммерческая недвижимость", callback_data="commercial")
    ]
    for i in b:
        kb.add(i)
    return kb
    

# база знаний - раздел возражения клиентов
def get_knowledge_base_bad_clients_markup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    b = [
        InlineKeyboardButton(text="Контекст", callback_data="context"),
        InlineKeyboardButton(text="Общее правило борьбы с возражениями", callback_data="general"),
        InlineKeyboardButton(text="Возражения при звонке", callback_data="bad_calls"),
        InlineKeyboardButton(text="Отработка возражений", callback_data="anti_bad"),
        InlineKeyboardButton(text="Возражения при встрече", callback_data="bad_meets")
    ]
    for i in b:
        kb.add(i)
    return kb
    
    
# база знаний - раздел встречи
def get_knowledge_base_bad_meets_markup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    b = [
        InlineKeyboardButton(text="Технология SMALL-TALK", callback_data="small-talk"),
        InlineKeyboardButton(text="Технология СПИН", callback_data="spin"),
        InlineKeyboardButton(text="Технология '3 ДА'", callback_data="3yes"),
        InlineKeyboardButton(text="Все можно продать", callback_data="all_able")
    ]
    for i in b:
        kb.add(i)
    return kb


# база знаний - раздел все возможно продать
def get_knowledge_base_all_able_markup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    b = [
        InlineKeyboardButton(text="Цена", callback_data="price"),
        InlineKeyboardButton(text="Хоумстейджинг", callback_data="homestaging")
    ]
    for i in b:
        kb.add(i)
    return kb


# база знаний - раздел договоры
def get_knowledge_base_deals_markup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    b = [
        InlineKeyboardButton(text="Эксклюзивный", callback_data="exclusive"),
        InlineKeyboardButton(text="Поисковой", callback_data="serching"),
        InlineKeyboardButton(text="Аукционный метод", callback_data="auction")
    ]
    for i in b:
        kb.add(i)
    return kb