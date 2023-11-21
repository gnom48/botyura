from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from bot import *
from keybords import *
from models import *
from .notifications import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, time
import re
import asyncio
from apscheduler.triggers.cron import CronTrigger


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

main_scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
main_scheduler.start()

support_scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
support_scheduler.start()

month_scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
month_scheduler.start()

last_messages = dict() # словарь структуры { chat_id : (lasr_message_time, bool) }
scheduler_list = dict() # словарь структуры { chat_id : { task_id : (kwargs, "занятие") } }


# таймер игнора
async def counter_time(chat_id: int) -> None:
    time_point = datetime.now().time()
    if time_point > time(18, 0) or time_point < time_point(10, 0):
        return
    last_messages[chat_id] = (time_point, True)
    await asyncio.sleep(5) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты занят, расскажи, пожалуйста, как у тебя дела?")
    else:
        return
    
    await asyncio.sleep(5) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты очень сильно занят, но напиши, пожалуйста, как у тебя дела?")
    else:
        return
    
    await asyncio.sleep(5) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник #{chat_id} не отвечает на сообщения уже 3 часа!")
        await bot.send_message(chat_id=chat_id, text=f"О нет, вы игнорируете меня уже 3 часа к ряду! Я был вынужден сообщить вашему руководителю.")
    else:
        return


# команда досрочно завершить заадчу
@dp.message_handler(commands=['del_task'], state=WorkStates.ready)
async def del_task_cmd(msg: types.Message, state: FSMContext):
    res_str = ""
    c = 0
    for t in scheduler_list[msg.from_user.id].keys():
        res_str += f"{c+1}) задача #{scheduler_list[msg.from_user.id][t][1]}\n"
        c += 1
    res_str += "\n\nВведите порядковый номер задачи, которую хотите завершить досрочно \n(Введите 0 чтобы выйти):"
    await bot.send_message(chat_id=msg.from_user.id, text=res_str)
    await WorkStates.enter_task_id.set()


# ввод порядкового номера задачи, которую досрочно завершаем
@dp.message_handler(lambda msg: msg.text.isdigit(), state=WorkStates.enter_task_id)
async def enter_del_task_id(msg: types.Message, state: FSMContext):
    if msg.text == "0":
        return
    c = 0
    if len(scheduler_list[msg.from_user.id].keys()) < c or c < 0:
        await msg.answer("Боюсь вы ввели неправильное число, попробуйте еще раз!")
        return
    for task_id in scheduler_list[msg.from_user.id].keys():
        if c+1 == int(msg.text):
            support_scheduler.remove_job(task_id)
            await send_notification(**scheduler_list[msg.from_user.id][task_id][0])
            scheduler_list[msg.from_user.id].pop(task_id)
            break
        c =+ 1


# инлайн режим бота
@dp.inline_handler()
async def inline_mode_query_handler(inline_query: types.InlineQuery):
    text = inline_query.query or "default"
    if text == "default":
        return
    elif text == "сотрудники":
        res_str = "Список ID сотрудников:\n"
        for rielter in Rielter.select():
            res_str += f"\n#{rielter.rielter_id}"
        item = types.InlineQueryResultArticle(input_message_content=types.InputTextMessageContent(res_str), id=ADMIN_CHAT_ID, title="Список ID сотрудников")
        await bot.answer_inline_query(inline_query_id=inline_query.id, results=[item], cache_time=1)
    elif re.match(r'отч[её]т #\d+', text):
        try:
            currentWorkerId = int(text.split('#')[1])
            result_str = get_total_statistics()
        except Exception:
                results_str = "Нет информации по такому сотруднику!"
        item = types.InlineQueryResultArticle(input_message_content=types.InputTextMessageContent(results_str), id=ADMIN_CHAT_ID, title=result_str)
        await bot.answer_inline_query(inline_query_id=inline_query.id, results=[item], cache_time=1)
    else:
        return


# команда задача
@dp.message_handler(commands=['task'], state=WorkStates.ready)
async def start_cmd(msg: types.Message, state: FSMContext):
    await msg.answer("Отлично, давайте запишем новое напоминание!", reply_markup=types.ReplyKeyboardRemove())
    await msg.answer("Напишите краткое название задачи:")
    await WorkStates.task_name.set()


# ввод названия задачи
@dp.message_handler(state=WorkStates.task_name)
async def enter_task_name(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["task_name"] = msg.text
    await msg.answer("Теперь напишите описание задачи (то что не хотите забыть):")
    await WorkStates.task_desc.set()


# ввод описания задачи
@dp.message_handler(state=WorkStates.task_desc)
async def enter_task_desk(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["task_deskription"] = msg.text
    await msg.answer("Теперь напишите дату (в формате ГГГГ-ММ-ДД), когда вам нужно об этом напомнить:")
    await WorkStates.task_date.set()


# ввод даты задачи
@dp.message_handler(state=WorkStates.task_date)
async def enter_task_date(msg: types.Message, state: FSMContext):
    if re.match(r'\d{4}\-\d{2}\-\d{2}', msg.text):
        async with state.proxy() as data:
            Task.create(rielter_id=msg.from_user.id,
                task_name=data["task_name"],
                task_deskription=data["task_deskription"],
                date_planed=msg.text).save()
        await msg.answer("Принято! Я обязательно напомню тебе об этом, когда придет время.")
        await WorkStates.ready.set()
    else:
        await msg.answer("Возможно что-то с форматом даты, попробуй еще раз", reply_markup=types.ReplyKeyboardRemove())


# команда меню
@dp.message_handler(commands=['menu'], state=WorkStates.ready)
async def start_cmd(msg: types.Message):
    await msg.answer(f"Чем займемся сейчас?", reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()


# команда старт
@dp.message_handler(commands=['start'], state="*")
async def start_cmd(msg: types.Message):
    scheduler_list[msg.from_user.id] = {}
    oldRielter: any
    try:
        oldRielter = Rielter.get_by_id(pk=msg.from_user.id)
    except Exception:
        oldRielter = None
    if oldRielter:
        await msg.answer(f"С возвращением, {oldRielter.fio}!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(f"Чем займемся сейчас?", reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        return
    await msg.answer("Привет!", reply_markup=get_start_markup())
    await WorkStates.restart.set()


# подтверждение начала регистрации
@dp.message_handler(lambda msg: msg.text == "Старт регистрации", state=WorkStates.restart)
async def send_welcome(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["rielter_id"] = msg.from_user.id
    await msg.answer("Введите ФИО:", reply_markup=types.ReplyKeyboardRemove())
    await WorkStates.reg_enter_login.set()


# ввод ФИО
@dp.message_handler(state=WorkStates.reg_enter_login)
async def enter_fio(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["fio"] = msg.text
    await msg.answer("Теперь введите дату рождения (в формате ГГГГ-ММ-ДД):")
    await WorkStates.reg_enter_brthday.set()


# ввод даты рождения
@dp.message_handler(state=WorkStates.reg_enter_brthday)
async def enter_brth(msg: types.Message, state: FSMContext):
    if re.match(r'\d{4}\-\d{2}\-\d{2}', msg.text):
        async with state.proxy() as data:
            data["birthday"] = msg.text
    else:
        await msg.answer("Возможно что-то с форматом даты, попробуй еще раз", reply_markup=types.ReplyKeyboardRemove())
        return
    await msg.answer("Теперь введите пол:", reply_markup=get_gender_kb())
    await WorkStates.reg_enter_gender.set()


# выбор пола
@dp.callback_query_handler(state=WorkStates.reg_enter_gender)
async def process_callback_gender(callback: types.CallbackQuery, state: FSMContext):
    if not (callback.data == "М" or callback.data == "Ж"):
        await bot.send_message(callback.from_user.id, "Ошибка, попробуйте снова!")
        return
    await callback.answer("✓")
    async with state.proxy() as data:
        data["gender"] = callback.data
    await bot.send_message(callback.from_user.id, "Ок")
    await bot.send_message(callback.from_user.id, "Теперь выберите, направления вашей деятельности:", reply_markup=get_realtors_type_kb())
    await WorkStates.reg_enter_type.set()


# выбор направления работы и подведение итога регистрации
@dp.callback_query_handler(state=WorkStates.reg_enter_type)
async def process_callback_gender(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "residential":
        async with state.proxy() as data:
            data["rielter_type"] = 0
    elif callback.data == "commercial":
        async with state.proxy() as data:
            data["rielter_type"] = 1
    else:
        await bot.send_message(callback.from_user.id, "Ошибка, попробуйте снова!")
        return
    await callback.answer("✓")
    async with state.proxy() as data:
        profile_tmp = Rielter.get_or_none(Rielter.rielter_id == callback.from_user.id)
        if profile_tmp != None:
            profile_tmp = Rielter.update(rielter_id=data["rielter_id"],
                                         fio=data["fio"],
                                         birthday=data["birthday"],
                                         gender=data["gender"],
                                         rielter_type=data["rielter_type"]).where(Rielter.rielter_id == data["rielter_id"]).execute()
            Report.update(rielter_id=data["rielter_id"]).execute()
        else:
            Rielter.create(rielter_id=data["rielter_id"],
                           fio=data["fio"],
                           birthday=data["birthday"],
                           gender=data["gender"],
                           rielter_type=data["rielter_type"]).save()
            Report.create(rielter_id=data["rielter_id"]).save()
        profile = Rielter.get(Rielter.rielter_id == callback.from_user.id)

        await bot.send_message(callback.from_user.id, f"Ваш профиль сформирован!\n\nID: {profile.rielter_id},\nФИО: {profile.fio},\nДата рождения: {profile.birthday},\nПол: {profile.gender},\nНаправление работы: {Rielter_type.get_by_id(pk=profile.rielter_type).rielter_type_name}")
        await bot.send_message(callback.from_user.id, f"В каком направлении будешь работать сейчас?", reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()

        # запуск утреннего и вечернего оповещения
        main_scheduler.add_job(morning_notifications, trigger=CronTrigger(hour=10, minute=0), kwargs={"chat_id": callback.from_user.id, "bot": bot, "text": get_day_plan(data["rielter_type"]), "state": None, "keyboard": types.ReplyKeyboardRemove()})
        main_scheduler.add_job(good_evening_notification, trigger=CronTrigger(hour=18, minute=30), kwargs={"chat_id": callback.from_user.id, "bot": bot})

        # запуск ежемесячного отчета
        month_scheduler.add_job(send_notification, 'date', run_date=datetime.now().replace(hour=10, minute=30) + timedelta(days=1), kwargs={"chat_id": callback.from_user.id, "bot": bot, "text": get_total_statistics(callback.from_user.id), "state": None, "keyboard": types.ReplyKeyboardRemove()})


# default хэндлер для клавиатуры, которая будет доступна всегда в состоянии ready
@dp.callback_query_handler(state=WorkStates.ready)
async def start_new_activity(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("✓")
    last_messages[callback.from_user.id] = (datetime.now().time(), True)
    if callback.data == "analytics":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, предложить новую работу!")
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        count = 0
        if tmp:
            count += tmp.analytics
            Report.update(analytics=count+1).where(Report.rielter_id == callback.from_user.id).execute()
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Чем займёшься дальше?", "state": WorkStates.ready, "keyboard": get_inline_menu_markup()}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=300), kwargs=tmpKwargs)
        scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Аналитика")
        await counter_time(callback.from_user.id)

    elif callback.data == "meeting":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, удачной поездки, вернусь...!")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как прошла встреча?", "state": WorkStates.meet_new_object_result, "keyboard": get_meeting_result_markup()}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=300), kwargs=tmpKwargs)
        scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Встреча")
        await counter_time(callback.from_user.id)

    elif callback.data == "call":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, поитересоваться твоими успехами!")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как твои успехи в прозвонах? Сколько рабочих звонков ты успел совершить?", "state": WorkStates.enter_calls_count, "keyboard": None}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=300), kwargs=tmpKwargs)
        scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Прозвон")
        await counter_time(callback.from_user.id)

    elif callback.data == "show":
        await bot.send_message(chat_id=callback.from_user.id, text="Отлично, желаю удачного показа, скоро вернусь!")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как прошел показ?", "state": WorkStates.show_result, "keyboard": get_meeting_result_markup()}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=300), kwargs=tmpKwargs)
        scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Показ")
        await counter_time(callback.from_user.id)

    elif callback.data == "search":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, предложить новую работу!")
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        if tmp:
            count = 0
            count += tmp.analytics
            Report.update(analytics=count+1).where(Report.rielter_id == callback.from_user.id).execute()
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Чем займёшься дальше?", "state": WorkStates.ready, "keyboard": get_inline_menu_markup()}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=300), kwargs=tmpKwargs)
        scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Поиск")
        await counter_time(callback.from_user.id)

    elif callback.data == "flyer":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, поитересоваться твоими успехами!")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как твои успехи в расклейке? Прогулялся, отдохнул, готов к работе? Сколько объявлений ты расклеил?", "state": WorkStates.enter_flyer_count, "keyboard": None}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=300), kwargs=tmpKwargs)
        scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Расклейка")
        await counter_time(callback.from_user.id)

    elif callback.data == "deal":
        tmp = Rielter.get_or_none(Rielter.rielter_id == callback.from_user.id)
        if tmp.rielter_type_id == 0:
            await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_meeting_private_markup())
        elif tmp.rielter_type_id == 1:
            await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_meeting_commercial_markup())
        await counter_time(callback.from_user.id)
        await WorkStates.deal_enter_deal_type.set()

    elif callback.data == "deposit":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, удачи. Скоро вернусь")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как прошло получение задатка?", "state": WorkStates.deposit_result, "keyboard": get_meeting_result_markup()}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=300), kwargs=tmpKwargs)
        scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Задаток")
        await counter_time(callback.from_user.id)

    elif callback.data == "no_work":
        await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_rest_markup())
        await WorkStates.no_work_type.set()
        await counter_time(callback.from_user.id)

    else:
        await bot.send_message(chat_id=callback.from_user.id, text="О нет, необработанная ситация!\nПросим вас сделать скриншот этой ситуации и направить разработчикам.")


# количество расклеенных листовок
@dp.message_handler(lambda msg: msg.text, state=WorkStates.enter_flyer_count)
async def enter_posting_adverts_count(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (datetime.now().time(), True)
    count: int = 0
    try:
        count = int(msg.text)
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!")
        return
    await msg.answer(generate_motivation_compliment())
    tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
    if tmp:
        count += tmp.posting_adverts
        Report.update(posting_adverts=count).where(Report.rielter_id == msg.from_user.id).execute()
    await msg.answer(f"Чем займемся дальше?", reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()


# количество звонков
@dp.message_handler(lambda msg: msg.text, state=WorkStates.enter_calls_count)
async def enter_posting_adverts_count(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (datetime.now().time(), True)
    count: int = 0
    try:
        count = int(msg.text)
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!")
        return
    await msg.answer(generate_motivation_compliment())
    tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
    if tmp:
        count += tmp.cold_call_count
        Report.update(cold_call_count=count).where(Report.rielter_id == msg.from_user.id).execute()
    await msg.answer(f"Чем займемся сейчас?", reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()


# вид сделки
@dp.message_handler(lambda msg: msg.text in ["Квартира", "Земля", "Дом", "Офис", "Магазин", "Другое", "Назад"], state=WorkStates.deal_enter_deal_type)
async def enter_deal_type(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (datetime.now().time(), True)
    if msg.text == "Назад":
        await msg.answer(text="Отмена!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text=f"В каком направлении будешь работать сейчас?", reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        return

    await WorkStates.ready.set()
    await msg.answer(text=f"Отлично! Вернусь через 2 часа и спрошу как у тебя дела!", reply_markup=types.ReplyKeyboardRemove())
    tmpKwargs = {"chat_id": msg.from_user.id, "bot": bot, "text": f"Как прошла сделка в категории: #{msg.text} ?", "state": WorkStates.deal_retult, "keyboard": get_meeting_result_markup()}
    job = support_scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=300), kwargs=tmpKwargs)
    scheduler_list[msg.from_user.id][job.id] = (tmpKwargs, "Задаток")
    await counter_time(msg.from_user.id)

# if msg.text.split('#')[1][:-2] == "Квартира":
#     pass
# elif msg.text.split('#')[1][:-2] == "Земля":
#     pass
# elif msg.text.split('#')[1][:-2] == "Дом":
#     pass


# результат сделки
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо", "Есть возражения"], state=WorkStates.deal_retult)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (datetime.now().time(), True)
    if msg.text == "Хорошо":
        tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
        count = 0
        if tmp:
            count += tmp.deals_count
            Report.update(posting_adverts=count+1).where(Report.rielter_id == msg.from_user.id).execute()
        await msg.answer(generate_deal_related_compliment())
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
    await msg.answer(f"Чем займемся сейчас?", reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()


# результат показа
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо", "Есть возражения"], state=WorkStates.show_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (datetime.now().time(), True)
    if msg.text == "Хорошо":
        tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
        count = 0
        if tmp:
            count += tmp.show_objects
            Report.update(show_objects=count+1).where(Report.rielter_id == msg.from_user.id).execute()
        await msg.answer(generate_property_showing_compliment())
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
    await msg.answer(f"Чем займемся сейчас?", reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()


# результат задатка
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо", "Есть возражения"], state=WorkStates.deposit_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (datetime.now().time(), True)
    if msg.text == "Хорошо":
        tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
        count = 0
        if tmp:
            count += tmp.take_deposit_count
            Report.update(take_deposit_count=count+1).where(Report.rielter_id == msg.from_user.id).execute()
        await msg.answer(generate_initiative_compliment())
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
    await msg.answer(f"Чем займемся сейчас?", reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()


# результат встречи по новому объекту
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо", "Есть возражения"], state=WorkStates.meet_new_object_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (datetime.now().time(), True)
    if msg.text == "Хорошо":
        tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
        count = 0
        if tmp:
            count += tmp.meet_new_objects
            Report.update(meet_new_objects=count+1).where(Report.rielter_id == msg.from_user.id).execute()
        await msg.answer(generate_initiative_compliment())
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
    await msg.answer(f"Чем займемся сейчас?", reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()


# не могу работать
@dp.message_handler(lambda msg: msg.text in ["Устал", "Отпуск", "Больничный", "Назад"], state=WorkStates.no_work_type)
async def enter_no_work_type(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (datetime.now().time(), True)
    if msg.text == "Назад":
        await msg.answer("В каком направлении будешь работать сейчас?", reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
    elif msg.text == "Устал":
        await msg.answer("Конечно ты можешь отдохнуть, я напомню тебе про работу через час.")
        tmpKwargs = {"chat_id": msg.from_user.id, "bot": bot, "text": "Отдохнул, готов поработать?", "state": WorkStates.ready, "keyboard": get_inline_menu_markup()}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(hours=1), kwargs=tmpKwargs)
        scheduler_list[msg.from_user.id][job.id] = (tmpKwargs, "Отдых")
        await WorkStates.ready.set()
    elif msg.text == "Отпуск":
        await msg.answer("Сейчас уточню у руководителя...")
    else:
        await msg.answer("Болеть всегда неприятно, но ты поправляйся, а я сообщю руководителю. Сколько дней тебя не тревожить?")
        await WorkStates.enter_days_illor_rest.set()


# сколько дней болеть или отдыхать
@dp.message_handler(state=WorkStates.enter_days_illor_rest)
async def enter_no_work_type(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (datetime.now().time(), True)
    try:
        days_count = int(msg.text)
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!")
        return
    await msg.answer(f"Я все понял. Не буду беспокоить тебя {days_count} дней!")
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник #{msg.from_user.id} взял больничный на {days_count} дней.")
    await WorkStates.ready.set()
