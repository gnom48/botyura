import random


# значения по callback.data с ссылками на яндекс диск
why_bad_str_list = {
    "analytics" : "https://disk.yandex.ru/i/AnAsCJirq9_w2A", 
    "calls" : "https://disk.yandex.ru/i/I2RbitoFIHM80g", 
    "shows" : "https://disk.yandex.ru/i/AoO0qajb78R2iA", 
    "context" : "https://disk.yandex.ru/i/KytgGrnN80GyfQ", 
    "general" : "https://disk.yandex.ru/i/KytgGrnN80GyfQ", 
    "bad_calls" : "https://disk.yandex.ru/i/KytgGrnN80GyfQ", 
    "anti_bad" : "https://disk.yandex.ru/i/KytgGrnN80GyfQ", 
    "bad_meets" : "https://disk.yandex.ru/i/KytgGrnN80GyfQ", 
    "small-talk" : "https://disk.yandex.ru/i/TuVuDeona4t18A", 
    "spin" : "https://disk.yandex.ru/i/owxcwxKSzzDyKA", 
    "price" : "https://disk.yandex.ru/i/GF8SnVfH4es5Mg", 
    "exclusive" : "https://disk.yandex.ru/i/XbeovgGuvziSPQ", 
    "exclusive" : "https://disk.yandex.ru/i/Zb2Zl6tiAmZnQg", 
    "serching" : "https://disk.yandex.ru/i/2lVl5v3cfEKcSw", 
    "auction" : "https://disk.yandex.ru/i/Zb2Zl6tiAmZnQg",
    "commercial": "https://disk.yandex.ru/i/hMe_CatbwMckbQ"
                    }


# минимальный план на день
def get_day_plan(rielter_type_id: int) -> str:
    tmp: str = "любая"
    if rielter_type_id == 0:
        tmp = "дом, участок, квартира ..."
    elif rielter_type_id == 1:
        tmp = "офис, магазин ..."
    return f"Доброе утро, напоминаю про план-минимум на день!\n\n1) найти в интернете (на Авито или Циан) объекты недвижимости ({tmp}),\n" + \
        f"2) сделать за день минимум 5 холодных звонков собственникам объектов\n" + \
        f"3) договориться минимум на 2 встречи\n" + \
        f"4) провести минимум 2 встречи в день\n" + \
        f"5) предложить собственнику недвижимости заключить договор\n" + \
        f"6) заключить минимум 5 договоров в месяц\n" + \
        f"7) сделать расклейку минимум 50 листов."


# Общие мотивационные фразы когда мы просто будем хвалить сотрудника в большинстве случаев
def generate_motivation_compliment():
    compliments = [
        "Ты настоящий профессионал! Твои навыки удивительны.",
        "Твоё умение находить лучшие варианты поражает.",
        "Твоя преданность работе безупречна. Продолжай в том же духе!",
        "Твои клиенты в восторге от тебя! Они в надежных руках.",
        "Ты умеешь подходить к каждому клиенту индивидуально и находить лучшие решения.",
        "Твой профессионализм не имеет границ! Продолжай в том же духе!",
        "Твои навыки ведения переговоров поражают. Это превосходно!",
        "Ты всегда ставишь интересы клиента на первое место. Это восхитительно!",
        "Твоё стремление к совершенству не знает границ. Это вдохновляет!",
        "Твой профессионализм и умение решать проблемы делают тебя уникальным риелтором.",
        "Твои клиенты довольны твоими услугами - это самое лучшее подтверждение твоей работы.",
        "Твоё упорство и трудолюбие достойны восхищения! Продолжай двигаться вперед!"
    ]
    return random.choice(compliments)


# Фразы для кнопки сделка
def generate_deal_related_compliment():
    compliments = [
        "Ты замечательно провёл эту сделку! Твои навыки ведения переговоров поражают.",
        "Твоя уверенность в сделке вдохновляет! Это было превосходно!",
        "Твой профессионализм был важен для успешного завершения этой сделки.",
        "Это было невероятно! Твои навыки находить лучшие решения сыграли ключевую роль в этой сделке.",
        "Твои клиенты безмерно довольны! Эта сделка - твоё достижение.",
        "Твоё умение поддерживать спокойствие в самых сложных ситуациях помогло завершить эту сделку.",
        "Ты с легкостью находишь общий язык с клиентами - это один из твоих ключевых навыков в этой сделке.",
        "Эта сделка была проведена с твоим обычным профессионализмом и исключительным качеством работы.",
        "Твоё упорство и трудолюбие помогли добиться успеха в этой сделке."
    ]
    return random.choice(compliments)


# Фразы для кнопки задаток
def generate_deposit_compliment():
    compliments = [
        "Твоё инициативное поведение внесло большой вклад в задаток клиента. Отличная работа!",
        "Твоё быстрое реагирование и предприимчивость помогли клиенту с задатком. Превосходно!",
        "Твоя инициатива и умение проводить задаток эффективно помогли клиенту сделать правильный выбор.",
        "Это было впечатляюще! Твой профессионализм в оформлении задатка поразил клиента.",
        "Твоё умение поддержать клиента и провести задаток - это твоё преимущество в работе.",
        "Ты с легкостью нашёл оптимальные решения для задатка клиента. Отличная работа!",
        "Твоё понимание важности задатка для клиента сыграло большую роль в успешной сделке.",
        "Твои знания и опыт помогли клиенту принять правильное решение о задатке."
    ]
    return random.choice(compliments)


# Фразы для кнопки показ 
def generate_property_showing_compliment():
    compliments = [
        "Твоя профессиональная подача показа объекта поражает! Отличная работа!",
        "Ты с легкостью демонстрируешь объект и привлекаешь клиентов своим профессионализмом.",
        "Твоё умение выделить особенности объекта во время показа - это твоя сила!",
        "Клиенты остались впечатлены твоей энергией и информативным показом объекта.",
        "Твоя уверенность и знание объекта сделали показ более убедительным и привлекательным.",
        "Твой профессионализм во время показа помог клиентам лучше понять особенности объекта.",
        "Ты внимателен к потребностям клиента во время показа - это важно и ценится."
    ]
    return random.choice(compliments)


# Фразы для кнопки встреча
def generate_client_meeting_compliment():
    compliments = [
        "Твоё умение установить прекрасный контакт с клиентами поражает! Отличная работа!",
        "Твой профессионализм и эмпатия помогли клиентам почувствовать себя комфортно на встрече.",
        "Твоё умение слушать и понимать потребности клиентов помогло успешно провести встречу.",
        "Клиенты оценили твоё внимание к деталям на встрече - это твоё преимущество.",
        "Твоя способность адаптироваться к различным типам клиентов впечатляет. Продолжай в том же духе!",
        "Твои клиенты чувствуют себя важными и понимаемыми во время встречи благодаря твоему отношению.",
        "Ты создаешь доверительную атмосферу на встречах с клиентами - это твой ключ к успеху."
    ]
    return random.choice(compliments)


# фразы при неудачном исходе
def generate_bad_meeting_or_deal():
    compliments = [
        "Каждая встреча - это шанс для твоего роста. Ты постоянно улучшаешь свои навыки!",
        "Трудности - это временные испытания, которые помогают тебе стать еще сильнее в своей профессии.",
        "Не бойся извлекать уроки из каждой ситуации. Это поможет тебе стать опытнее в работе риелтором.",
        "Важно помнить, что даже в неудачах есть свои уроки. Найди их и используй для своего развития.",
        "Каждый клиент и всякий раз - это шанс показать свои профессиональные способности.",
        "Способность сохранять спокойствие в непредвиденных ситуациях - твое преимущество в работе с клиентами.",
        "Любая сложная ситуация может принести тебе пользу, если посмотреть на нее с другой стороны.",
        "Не давай временным трудностям подорвать твою уверенность. Ты движешься к успеху!",
        "Твоя постоянная готовность учиться и развиваться вдохновляет окружающих. Это замечательно!"
    ]
    return random.choice(compliments)

#планы на день
def generate_main_menu_text():
    compliments = [
        "Что будем делать?",
        "Чем планируешь заниматься?"
        
    ]
    return random.choice(compliments)

# help
def get_help_command_text() -> str:
    return "Приветствуем тебя в телеграмм-боте ProНедвижимость – твоем надежном помощнике в сфере недвижимости!\n\nЭтот бот разработан специально для риелторов компании ProНедвижимость с целью мотивации, управления и обеспечения эффективности вашей работы.\n\nСписок доступных команд и их краткие описания вы можете увидеть в разделе Меню.\n\nВаша персональная техническая поддержка - @Darik097"
