from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from bot import *
from keybords import *
from models import *
from .notifications import *
from apscheduler.triggers.cron import CronTrigger
from datetime import timedelta
from datetime import datetime as dt
import re
import random
import asyncio


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

main_scheduler.start()

# запуск утреннего и вечернего оповещения
main_scheduler.add_job(func=morning_notifications, trigger=CronTrigger(hour=10-3, minute=0), kwargs={"bot": bot, "dp": dp})
main_scheduler.add_job(func=good_evening_notification, trigger=CronTrigger(hour=18-3, minute=30), kwargs={"bot": bot})

# запуск ежемесячного и еженедельного отчета
month_week_scheduler.add_job(func=get_month_statistics, trigger='cron', day='last', hour=10-3, minute=30, kwargs={"bot": bot})
month_week_scheduler.add_job(func=get_week_statistics, trigger='cron', day_of_week='mon', hour=10-3, minute=50, kwargs={"bot": bot})

support_scheduler.start()
month_week_scheduler.start()

scheduler_list = dict() # словарь структуры { chat_id : { task_id : (kwargs, "занятие") } }


# команда помощь
@dp.message_handler(commands=['help'], state=WorkStates.ready)
async def del_task_cmd(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    await msg.answer(get_help_command_text())


# команда досрочно завершить задачу
@dp.message_handler(commands=['del_task'], state=WorkStates.ready)
async def del_task_cmd(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    res_str = ""
    c = 0
    # tasks_to_del = []
    
    for task in scheduler_list[msg.from_user.id].keys():
        if support_scheduler.get_job(task):
            res_str += f"{c+1}) задача #{scheduler_list[msg.from_user.id][task][1]}\n"
            c += 1
        # else:
            # tasks_to_del.append(scheduler_list[msg.from_user.id][task])

    # TODO: придумать как удалять непосредственно из вложенного словаря scheduler_list[msg.from_user.id]

    if c > 0:
        res_str += "\n\nВведи порядковый номер задачи, которую хочешь завершить досрочно \n(Введи 0 чтобы выйти):"
        await bot.send_message(chat_id=msg.from_user.id, text=res_str)
        await WorkStates.enter_task_id.set()
    else:
        await bot.send_message(chat_id=msg.from_user.id, text="Вы еще не начинали никаких задач!")
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)


# ввод порядкового номера задачи, которую досрочно завершаем
@dp.message_handler(lambda msg: msg.text.isdigit(), state=WorkStates.enter_task_id)
async def enter_del_task_id(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if msg.text == "0":
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        return
    c = 0
    if len(scheduler_list[msg.from_user.id].keys()) < c or c < 0:
        await msg.answer("Боюсь ты ввел неправильное число, попробуй еще раз!")
        return
    for task_id in scheduler_list[msg.from_user.id].keys():
        if c+1 == int(msg.text):
            support_scheduler.remove_job(task_id)
            await send_notification(**scheduler_list[msg.from_user.id][task_id][0])
            scheduler_list[msg.from_user.id].pop(task_id)
            break
        c =+ 1


# инлайн режим бота
@dp.inline_handler(state="*")
async def inline_mode_query_handler(inline_query: types.InlineQuery, state: FSMContext):
    text = inline_query.query or "None"
    if text:
        items = []
        for rielter in Rielter.select():
            try:
                items.append(types.InlineQueryResultArticle(input_message_content=types.InputTextMessageContent(get_month_statistics_str(rielter.rielter_id)), id=str(rielter.rielter_id), title=f"Отчёт {rielter.fio}"))
            except:
                continue
        await bot.answer_inline_query(inline_query_id=inline_query.id, results=items, cache_time=1)


# команда задача
@dp.message_handler(commands=['task'], state=WorkStates.ready)
async def start_cmd(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    await msg.answer("Отлично, давай запишем новое напоминание!", reply_markup=types.ReplyKeyboardRemove())
    await msg.answer("Напиши краткое название задачи:")
    await WorkStates.task_name.set()


# ввод названия задачи
@dp.message_handler(state=WorkStates.task_name)
async def enter_task_name(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    async with state.proxy() as data:
        data["task_name"] = msg.text
    await msg.answer("Теперь напиши дату (в формате ДД-ММ-ГГГГ), когда тебе нужно об этом напомнить:")
    await WorkStates.task_date.set()


# ввод даты задачи
@dp.message_handler(state=WorkStates.task_date)
async def enter_task_date(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if re.match(r'\d{2}\-\d{2}\-\d{4}', msg.text):
        date_obj = dt.strptime(msg.text, '%d-%m-%Y')
        if date_obj.date() < dt.now().date():
            await msg.answer("Напоминания можно задавать только на будущее, попробуй еще раз!", reply_markup=types.ReplyKeyboardRemove())
            return
        if dt.now().date().year - date_obj.date().year > 1:
            await msg.answer("Не стоит загадывать на такой большой срок, лучше сосредоточься на настоящем! Попробуй ввести дату еще раз!", reply_markup=types.ReplyKeyboardRemove())
            return
        async with state.proxy() as data:
            data["date_planed"] = msg.text
        await msg.answer("Теперь введи время в формате ЧЧ:ММ")
        await WorkStates.task_time.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    else:
        await msg.answer("Возможно что-то с форматом даты, попробуй еще раз", reply_markup=types.ReplyKeyboardRemove())
        await WorkStates.task_date.set()
        
        
# ввод времени задачи
@dp.message_handler(state=WorkStates.task_time)
async def enter_task_date(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if re.match(r'\d{2}\:\d{2}', msg.text):
        time_obj: dt
        try:
            time_obj = dt.strptime(msg.text, '%H:%M').time()
        except:
            await msg.answer("Возможно что-то с форматом времени, попробуй еще раз", reply_markup=types.ReplyKeyboardRemove())
            await WorkStates.task_time.set()
            return
        async with state.proxy() as data:
            if dt.strptime(data["date_planed"], '%d-%m-%Y').date() == dt.now().date():
                dt_tmp = dt(year=dt.now().year, month=dt.now().month, day=dt.now().day, hour=time_obj.hour, minute=time_obj.minute, second=0)
                if (dt_tmp - dt.now()).seconds < 3500:
                    await msg.answer("Боюсь что я не могу поставить напоминание ранее, ранее чем через час! Попробуй еще раз")
                    return
                tmpKwargs = {"chat_id": msg.from_user.id, "bot": bot, "text": f"Напоминаю, что ты запланировал в {msg.text} заняться: {data['task_name']}", "state": None, "keyboard": None, "timeout": False}
                support_scheduler.add_job(send_notification, trigger="date", run_date=(dt_tmp - timedelta(hours=3, minutes=30)), kwargs=tmpKwargs)
                await msg.answer("Принято! Я обязательно напомню тебе сегодня (за полчаса до)")
                await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
                await WorkStates.ready.set()
                await counter_time(chat_id=msg.from_user.id, bot=bot)
                return
            Task.create(rielter_id=msg.from_user.id,
                task_name=data["task_name"],
                date_planed=data["date_planed"],
                time_planed=msg.text).save()
        await msg.answer("Принято! Я обязательно напомню тебе, когда придет время (за полчаса до)")
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    else:
        await msg.answer("Возможно что-то с форматом времени, попробуй еще раз", reply_markup=types.ReplyKeyboardRemove())
        await WorkStates.task_time.set()


# команда меню
@dp.message_handler(commands=['menu'], state="*")
async def start_cmd(msg: types.Message):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()
    await counter_time(chat_id=msg.from_user.id, bot=bot)
    

# служебная команда для отладки
@dp.message_handler(commands=['debug'], state="*")
async def start_cmd(msg: types.Message, state: FSMContext):
    await msg.answer(state.get_state())


# команда старт
@dp.message_handler(commands=['start'], state="*")
async def start_cmd(msg: types.Message):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    scheduler_list[msg.from_user.id] = {}
    oldRielter: any
    try:
        oldRielter = Rielter.get_by_id(pk=msg.from_user.id)
    except Exception:
        oldRielter = None
    if oldRielter:
        await msg.answer(f"С возвращением, {oldRielter.fio}!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
        return
    await msg.answer("Привет!\nДля начала работы нажми на кнопку 'Старт регистрации'", reply_markup=get_start_button())
    await WorkStates.restart.set()


# подтверждение начала регистрации
@dp.callback_query_handler(lambda callback: callback.data == "Старт регистрации", state=WorkStates.restart)
async def send_welcome(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("✓")
    async with state.proxy() as data:
        data["rielter_id"] = callback.from_user.id
    await bot.send_message(chat_id=callback.from_user.id, text="Введи ФИО:")
    await WorkStates.reg_enter_login.set()


# ввод ФИО
@dp.message_handler(state=WorkStates.reg_enter_login)
async def enter_fio(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    async with state.proxy() as data:
        data["fio"] = msg.text
    await msg.answer("Теперь введи дату рождения (в формате ДД-ММ-ГГГГ):")
    await WorkStates.reg_enter_brthday.set()


# ввод даты рождения
@dp.message_handler(state=WorkStates.reg_enter_brthday)
async def enter_brth(msg: types.Message, state: FSMContext):
    if re.match(r'\d{2}\-\d{2}\-\d{4}', msg.text):
        date_obj = dt.strptime(msg.text, '%d-%m-%Y')
        if date_obj > dt.now():
            await msg.answer("О, ты из будущего, попробуй ввести еще раз!", reply_markup=types.ReplyKeyboardRemove())
            return
        if dt.now().date().year - date_obj.date().year < 16:
            await msg.answer("Слишком юный возраст, попробуй ввести еще раз!", reply_markup=types.ReplyKeyboardRemove())
            return
        async with state.proxy() as data:
            data["birthday"] = msg.text
    else:
        await msg.answer("Возможно что-то с форматом даты, попробуй еще раз!", reply_markup=types.ReplyKeyboardRemove())
        return
    await msg.answer("Теперь укажи пол:", reply_markup=get_gender_kb())
    await WorkStates.reg_enter_gender.set()


# выбор пола
@dp.callback_query_handler(state=WorkStates.reg_enter_gender)
async def process_callback_gender(callback: types.CallbackQuery, state: FSMContext):
    if not (callback.data == "М" or callback.data == "Ж"):
        await bot.send_message(callback.from_user.id, "Ошибка, попробуй снова!")
        return
    await callback.answer("✓")
    async with state.proxy() as data:
        data["gender"] = callback.data
    await bot.send_message(callback.from_user.id, "Теперь выбери, направления вашей деятельности:", reply_markup=get_realtors_type_kb())
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
        await bot.send_message(callback.from_user.id, "Ошибка, попробуй снова!")
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
        else:
            Rielter.create(rielter_id=data["rielter_id"],
                           fio=data["fio"],
                           birthday=data["birthday"],
                           gender=data["gender"],
                           rielter_type=data["rielter_type"]).save()
            Report.create(rielter_id=callback.from_user.id).save()
            WeekReport.create(rielter_id=callback.from_user.id).save()
            MonthReport.create(rielter_id=callback.from_user.id).save()

        profile = Rielter.get(Rielter.rielter_id == callback.from_user.id)

        await bot.send_message(callback.from_user.id, f"Профиль сформирован!\n\nID: {profile.rielter_id},\nФИО: {profile.fio},\nДата рождения: {profile.birthday},\nПол: {profile.gender},\nНаправление работы: {Rielter_type.get_by_id(pk=profile.rielter_type).rielter_type_name}")
        await bot.send_message(callback.from_user.id, generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=callback.from_user.id, bot=bot)


# default хэндлер для клавиатуры, которая будет доступна всегда в состоянии ready
@dp.callback_query_handler(state=WorkStates.ready)
async def start_new_activity(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("✓")
    last_messages[callback.from_user.id] = (dt.now().time(), True)
    if callback.data == "analytics":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, предложить новую работу!")
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        count = 0
        if tmp:
            count += tmp.analytics
            Report.update(analytics=count+1).where(Report.rielter_id == callback.from_user.id).execute()
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как прошло занятие аналитикой, уверен супер продуктивно?", "state": WorkStates.analytics_result, "keyboard": get_good_bed_result_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Аналитика")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Аналитика")


    elif callback.data == "meeting":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, удачной поездки, скоро вернусь и спрошу как все прошло!")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как прошла встреча?", "state": WorkStates.meet_new_object_result, "keyboard": get_good_bed_result_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Встреча")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Встреча")

    elif callback.data == "call":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, поитересоваться твоими успехами!")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как твои успехи в прозвонах? Сколько рабочих звонков ты успел совершить?", "state": WorkStates.enter_calls_count, "keyboard": None, "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Прозвон")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Прозвон")

    elif callback.data == "show":
        await bot.send_message(chat_id=callback.from_user.id, text="Отлично, желаю удачного показа, скоро вернусь!")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как прошел показ?", "state": WorkStates.show_result, "keyboard": get_good_bed_result_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Показ")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Показ")

    elif callback.data == "search":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, предложить новую работу!")
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        if tmp:
            count = 0
            count += tmp.analytics
            Report.update(analytics=count+1).where(Report.rielter_id == callback.from_user.id).execute()
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как прошло занятие по поиску новых объектов, уверен супер продуктивно?", "state": WorkStates.analytics_result, "keyboard": get_good_bed_result_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Поиск")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Поиск")

    elif callback.data == "flyer":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, поитересоваться твоими успехами!")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как твои успехи в расклейке? Прогулялся, отдохнул, готов к работе? Сколько объявлений ты расклеил?", "state": WorkStates.enter_flyer_count, "keyboard": None, "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Расклейка")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Расклейка")

    elif callback.data == "deal":
        tmp = Rielter.get_or_none(Rielter.rielter_id == callback.from_user.id)
        if tmp.rielter_type_id == 0:
            await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_meeting_private_markup())
        elif tmp.rielter_type_id == 1:
            await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_meeting_commercial_markup())
        await WorkStates.deal_enter_deal_type.set()

    elif callback.data == "deposit":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, удачи. Скоро вернусь и спрошу как все прошло!")
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Как прошло получение задатка?", "state": WorkStates.deposit_result, "keyboard": get_good_bed_result_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Задаток")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Задаток")

    elif callback.data == "no_work":
        await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_rest_markup())
        await WorkStates.no_work_type.set()
        
    elif callback.data == "d_base":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...")
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_root_markup())
        await WorkStates.knowledge_base_root.set()

    else:
        await bot.send_message(chat_id=callback.from_user.id, text="О нет, непредвиденная ситация!\nПросим вас сделать скриншот этой ситуации и направить разработчикам.")


# выбор раздела в базе знаний - корень
@dp.callback_query_handler(state=WorkStates.knowledge_base_root)
async def choose_what_bad(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now().time(), True)
    await callback.answer("✓")

    if callback.data == "analytics" or callback.data == "calls" or callback.data == "shows" or callback.data == "commercial":
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()

        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Изучил материал? Все понял, или нужно что-то еще?", "state": WorkStates.is_all_materials_ok, "keyboard": get_is_all_materials_ok_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_SHORT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")

    elif callback.data == "bad_clients":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...")
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_bad_clients_markup())
        await WorkStates.knowledge_base_bad_clients.set()

    elif callback.data == "meets":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...")
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_bad_meets_markup())
        await WorkStates.knowledge_base_bad_meets.set()
    
    elif callback.data == "deals":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...")
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_deals_markup())
        await WorkStates.knowledge_base_base_deals.set()
        
        
# выбор раздела в базе знаний - раздел с возражениями клиентов
@dp.callback_query_handler(state=WorkStates.knowledge_base_bad_clients)
async def choose_what_bad_clients(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now().time(), True)
    await callback.answer("✓")

    if callback.data in ["context", "general", "bad_calls", "anti_bad", "bad_meets"]:
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()

        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Изучил материал? Все понял, или нужно что-то еще?", "state": WorkStates.is_all_materials_ok, "keyboard": get_is_all_materials_ok_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_SHORT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")
            
            
# выбор раздела в базе знаний - раздел с договорами
@dp.callback_query_handler(state=WorkStates.knowledge_base_base_deals)
async def choose_what_deals(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now().time(), True)
    await callback.answer("✓")

    if callback.data in ["exclusive", "serching", "auction"]:
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()

        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Изучил материал? Все понял, или нужно что-то еще?", "state": WorkStates.is_all_materials_ok, "keyboard": get_is_all_materials_ok_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_SHORT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")


# выбор раздела в базе знаний - раздел с встречами
@dp.callback_query_handler(state=WorkStates.knowledge_base_bad_meets)
async def choose_what_meets(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now().time(), True)
    await callback.answer("✓")

    if callback.data in ["small-talk", "spin", "3yes"]:
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()

        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Изучил материал? Все понял, или нужно что-то еще?", "state": WorkStates.is_all_materials_ok, "keyboard": get_is_all_materials_ok_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_SHORT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")

    elif callback.data == "all_able":
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери далее:", reply_markup=get_knowledge_base_all_able_markup())
        await WorkStates.knowledge_base_all_able.set()
        
        
# выбор раздела в базе знаний - подраздел все можно продать
@dp.callback_query_handler(state=WorkStates.knowledge_base_all_able)
async def choose_what_all_able_to_sale(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now().time(), True)
    await callback.answer("✓")

    if callback.data in ["price", "homestaging"]:
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()

        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Изучил материал? Все понял, или нужно что-то еще?", "state": WorkStates.is_all_materials_ok, "keyboard": get_is_all_materials_ok_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_SHORT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")


# количество расклеенных листовок
@dp.message_handler(lambda msg: msg.text, state=WorkStates.enter_flyer_count)
async def enter_posting_adverts_count(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    count: int = 0
    try:
        count = int(msg.text)
        if count < 0:
            raise Exception()
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!", reply_markup=types.ReplyKeyboardRemove())
        return
    await msg.answer("Расклейка объявлений играет важную роль в привлечении новых клиентов! Чем больше расклеишь, тем больше людей о нас узнают!", reply_markup=types.ReplyKeyboardRemove())
    tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
    if tmp:
        count += tmp.posting_adverts
        Report.update(posting_adverts=count).where(Report.rielter_id == msg.from_user.id).execute()
    await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()
    await counter_time(chat_id=msg.from_user.id, bot=bot)


# количество звонков
@dp.message_handler(lambda msg: msg.text, state=WorkStates.enter_calls_count)
async def enter_posting_adverts_count(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    count: int = 0
    try:
        count = int(msg.text)
        if count < 0:
            raise Exception()
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!", reply_markup=types.ReplyKeyboardRemove())
        return
    await msg.answer("Если клиенты не идут к нам, мы будем звонить им и звать сами!", reply_markup=types.ReplyKeyboardRemove())
    tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
    if tmp:
        count += tmp.cold_call_count
        Report.update(cold_call_count=count).where(Report.rielter_id == msg.from_user.id).execute()
    await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()
    await counter_time(chat_id=msg.from_user.id, bot=bot)


# вид сделки
@dp.message_handler(lambda msg: msg.text in ["Квартира", "Земля", "Дом", "Офис", "Магазин", "Другое", "Назад"], state=WorkStates.deal_enter_deal_type)
async def enter_deal_type(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if msg.text == "Назад":
        await msg.answer(text="Отмена!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text=generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
        return

    await WorkStates.ready.set()
    await msg.answer(text=f"Отлично! Вернусь через 2 часа и спрошу как у тебя дела!", reply_markup=types.ReplyKeyboardRemove())
    tmpKwargs = {"chat_id": msg.from_user.id, "bot": bot, "text": f"Как прошла сделка в категории: #{msg.text} ?", "state": WorkStates.deal_retult, "keyboard": get_good_bed_result_markup(), "timeout": True}
    job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
    try:
        scheduler_list[msg.from_user.id][job.id] = (tmpKwargs, "Сделка")
    except:
        scheduler_list[msg.from_user.id] = {}
        scheduler_list[msg.from_user.id][job.id] = (tmpKwargs, "Сделка")


# что конкретно не так (обработка кнопок и список) универсальная
@dp.callback_query_handler(state=WorkStates.deal_why_bad_result)
async def enter_why_deal_bad(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now().time(), True)
    await callback.answer("✓")
    tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
    if callback.data in ("Объект не понравился", "Задаток сорвался", "Продавец привередливый", "Покупатель привередливый", "Встреча не состоялась", "get_materials_analytics", "get_materials_search"):
        if callback.data == "Объект не понравился":
            count = 0
            if tmp:
                count += tmp.bad_object_count
                Report.update(bad_object_count=count+1).where(Report.rielter_id == callback.from_user.id).execute()
            await bot.send_message(chat_id=callback.from_user.id, text=f"Бывают и такие объекты, которые не стоили потраченного времени!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["meets"]))
            await WorkStates.ready.set()
            
        elif callback.data == "Задаток сорвался":
            await bot.send_message(chat_id=callback.from_user.id, text = "Жаль, это был потенциальный клиент!")
            await bot.send_message(chat_id=callback.from_user.id, text=f"Выйти на задаток - самая сложная часть нашей работы, не!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["anti_bad"]))
            await WorkStates.ready.set()

        elif callback.data == "Продавец привередливый":
            count = 0
            if tmp:
                count += tmp.bad_seller_count
                Report.update(bad_seller_count=count+1).where(Report.rielter_id == callback.from_user.id).execute()
            await bot.send_message(chat_id=callback.from_user.id, text=f"Порой на рынке встречаются крайне неприятные продавцы, что поделаешь!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["bad_meets"]))
            await WorkStates.ready.set()
            
        elif callback.data == "Покупатель привередливый":
            count = 0
            if tmp:
                count += tmp.bad_seller_count
                Report.update(bad_seller_count=count+1).where(Report.rielter_id == callback.from_user.id).execute()
            await bot.send_message(chat_id=callback.from_user.id, text=f"Порой на рынке встречаются крайне неприятные покупатели, что поделаешь!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["bad_meets"]))
            await WorkStates.ready.set()
            
        elif callback.data == "Встреча не состоялась":
            count = 0
            if tmp:
                count += tmp.bad_seller_count
                Report.update(bad_seller_count=count+1).where(Report.rielter_id == callback.from_user.id).execute()
            await bot.send_message(chat_id=callback.from_user.id, text=f"Иногда попадаются просто безответственные продавцы, не хочется иметь с ними дело!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["bad_meets"]))
            await WorkStates.ready.set()

        elif callback.data == "get_materials_analytics":
            await bot.send_message(chat_id=callback.from_user.id, text=f"Всегда полезно самосовершенствование, особенно когда дело касается аналитики рынка!:", 
                                reply_markup=get_video_link(why_bad_str_list["analytics"]))
            await WorkStates.ready.set()
            
        elif callback.data == "get_materials_search":
            await bot.send_message(chat_id=callback.from_user.id, text=f"Конечно, вот держи материалы, которые прояснять твои проблемы с поиском новых объектов:", 
                                reply_markup=get_video_link(why_bad_str_list["analytics"]))
            await WorkStates.ready.set()        

        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Изучил материал? Все понял, или нужно что-то еще?", "state": WorkStates.is_all_materials_ok, "keyboard": get_is_all_materials_ok_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")

    elif callback.data == "Сделку перенесли" or callback.data == "Задаток перенесен":
        await bot.send_message(chat_id=callback.from_user.id, text = "Ладно, переносы имеют место в нашей работе, давай запишем тебе напоминание!", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text = "Напиши краткое название задачи:")
        await WorkStates.task_name.set()

    elif callback.data == "Клиент передумал":
        await bot.send_message(chat_id=callback.from_user.id, text = generate_bad_meeting_or_deal())
        await bot.send_message(chat_id=callback.from_user.id, text = generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
    
    elif callback.data == "other":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...")
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_root_markup())
        await WorkStates.knowledge_base_root.set()


# все понятно или повторить?
@dp.message_handler(lambda msg: msg.text in ["Спасибо, все понятно", "Нужна еще информация"], state=WorkStates.is_all_materials_ok)
async def is_all_materials_ok_handler(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if msg.text == "Спасибо, все понятно":
        await msg.answer("Рад, что смог помочь тебе повысить уровень знаний в профессиональной сфере!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    elif msg.text == "Нужна еще информация":
        await bot.send_message(chat_id=msg.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...")
        await bot.send_message(chat_id=msg.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_root_markup())
        await WorkStates.knowledge_base_root.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
        

# результат сделки
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.deal_retult)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if msg.text == "Хорошо":
        tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
        count = 0
        if tmp:
            count += tmp.deals_count
            Report.update(deals_count=count+1).where(Report.rielter_id == msg.from_user.id).execute()
        await msg.answer(generate_deal_related_compliment())
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Давай разберемся, что могло пойти не так!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Выбери проблему:", reply_markup=get_bed_result(from_state=WorkStates.deal_retult))
        await WorkStates.deal_why_bad_result.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    

# результат аналитики и поиска
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.analytics_result)
async def enter_analytics_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if msg.text == "Хорошо":
        await msg.answer(f"Умение анализировать рынок - важный навык для риелтора! Продолжай в том же духе!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(f"{generate_main_menu_text()}", reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)

    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Выбери проблему:", reply_markup=get_bed_result(from_state=WorkStates.analytics_result))
        await WorkStates.deal_why_bad_result.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
        

# результат показа
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.show_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if msg.text == "Хорошо":
        await msg.answer(text="В итоге вы подписали договор?", reply_markup=get_is_signed_markup())
        await WorkStates.is_signed.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    elif msg.text == "Плохо":
        await bot.send_message(chat_id=msg.from_user.id, text=generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=msg.from_user.id, text="Выбери проблему:", reply_markup=get_bed_result(from_state=WorkStates.show_result))
        await WorkStates.deal_why_bad_result.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
        

# подписан ли договор
@dp.callback_query_handler(state=WorkStates.is_signed)
async def is_contract_signed(callback: types.Message, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now().time(), True)
    await callback.answer("✓")
    if callback.data == "signed":
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        count_shows = 0
        count_contrects_signed = 0
        if tmp:
            count_shows += tmp.show_objects
            count_contrects_signed += tmp.contrects_signed
            Report.update(show_objects=count_shows+1, contrects_signed=count_contrects_signed+1).where(Report.rielter_id == callback.from_user.id).execute()
        await bot.send_message(chat_id=callback.from_user.id, text="Это потрясающий успех, я в тебя всегда верил!", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text=generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await counter_time(chat_id=callback.from_user.id, bot=bot)
        await WorkStates.ready.set()

    elif callback.data == "unsigned":
        await bot.send_message(chat_id=callback.from_user.id, text="Значит в следующий раз точно подпишите!" , reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text="А пока советую посмотреть материалы по этой теме, чтобы в следующий раз быть готовом на 100%", reply_markup=get_video_link("https://www.youtube.com/watch?v=XtXbWpa_tzE"))
        tmpKwargs = {"chat_id": callback.from_user.id, "bot": bot, "text": "Изучил материал? Все понял, или нужно что-то еще?", "state": WorkStates.is_all_materials_ok, "keyboard": get_is_all_materials_ok_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_SHORT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")
        except:
            scheduler_list[callback.from_user.id] = {}
            scheduler_list[callback.from_user.id][job.id] = (tmpKwargs, "Изучение теоретических материалов")
        await WorkStates.ready.set()

    elif callback.data == "later":
        last_messages[callback.from_user.id] = (dt.now().time(), True)
        await bot.send_message(chat_id=callback.from_user.id, text = "Ладно, клиенту необходимо хорошенько подумать, давай запишем тебе напоминание!", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text = "Напиши краткое название задачи:")
        await WorkStates.task_name.set()
        await counter_time(chat_id=callback.from_user.id, bot=bot)
        

# результат задатка
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.deposit_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if msg.text == "Хорошо":
        tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
        count_deposits = 0
        count_contrects_signed = 0
        if tmp:
            count_deposits += tmp.take_deposit_count
            count_contrects_signed += tmp.contrects_signed
            Report.update(take_deposit_count=count_deposits+1, contrects_signed=count_contrects_signed+1).where(Report.rielter_id == msg.from_user.id).execute()
        await msg.answer(generate_deposit_compliment(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Что пошло не так?", reply_markup=get_bed_result(from_state=WorkStates.deposit_result))
        await WorkStates.deal_why_bad_result.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
        

# результат встречи 
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.meet_new_object_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if msg.text == "Хорошо":
        await msg.answer(text="В итоге вы подписали договор?", reply_markup=get_is_signed_markup())
        await WorkStates.is_signed.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Выбери проблему:", reply_markup=get_bed_result(from_state=WorkStates.meet_new_object_result))
        await WorkStates.deal_why_bad_result.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
        

# не могу работать
@dp.message_handler(lambda msg: msg.text in ["Устал", "Отпуск", "Больничный", "Назад"], state=WorkStates.no_work_type)
async def enter_no_work_type(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    if msg.text == "Назад":
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    elif msg.text == "Устал":
        await msg.answer("Конечно ты можешь отдохнуть, я напомню тебе про работу через час.", reply_markup=types.ReplyKeyboardRemove())
        tmpKwargs = {"chat_id": msg.from_user.id, "bot": bot, "text": generate_main_menu_text(), "state": WorkStates.ready, "keyboard": get_inline_menu_markup(), "timeout": True}
        job = support_scheduler.add_job(send_notification, trigger="date", run_date=dt.now() + SHIFT_TIMEDELTA, kwargs=tmpKwargs)
        try:
            scheduler_list[msg.from_user.id][job.id] = (tmpKwargs, "Отдых")
        except:
            scheduler_list[msg.from_user.id] = {}
            scheduler_list[msg.from_user.id][job.id] = (tmpKwargs, "Отдых")
        await WorkStates.ready.set()
    elif msg.text == "Отпуск":
        async with state.proxy() as data:
            data["rest_type"] = "отпуск"
        await msg.answer("Отпуск - лучшее время в году! Напиши, сколько дней планируешь отдыхать, а я сообщу руководителю:", reply_markup=types.ReplyKeyboardRemove())
        await WorkStates.enter_days_ill_or_rest.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
    else:
        async with state.proxy() as data:
            data["rest_type"] = "больничный"
        await msg.answer("Болеть всегда неприятно, но ты поправляйся, а я сообщю руководителю.\nСколько дней тебя не тревожить?", reply_markup=types.ReplyKeyboardRemove())
        await WorkStates.enter_days_ill_or_rest.set()
        await counter_time(chat_id=msg.from_user.id, bot=bot)
        

# сколько дней болеть или отдыхать
@dp.message_handler(state=WorkStates.enter_days_ill_or_rest)
async def enter_no_work_type(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    try:
        days_count = int(msg.text)
        if days_count < 0:
            raise Exception()
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!")
        await counter_time(chat_id=msg.from_user.id, bot=bot)
        return
    async with state.proxy() as data:
        await msg.answer(f"Я все понял. Не буду тревожить тебя дней: {days_count}", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник  {Rielter.get_or_none(Rielter.rielter_id == msg.from_user.id).fio} #{msg.from_user.id} хочет взять #{data['rest_type']} на дней: {days_count}.")
        await WorkStates.ready.set()


# если поболтать
@dp.message_handler(state=WorkStates.ready)
async def talks(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now().time(), True)
    await msg.answer("Тебе стоит выбрать какое-нибудь действие, если ты потерялся - обратись к справке /help или своему руководителю!")
