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
from datetime import datetime, timedelta
import asyncio


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
scheduler.start() # TODO: оттестить


# старт регистрации
@dp.message_handler(commands=['start'], state="*")
async def start_cmd(msg: types.Message):
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
    await msg.reply("Ок")
    await msg.answer("Теперь введите дату рождения (в формате ГГГГ-ММ-ДД):")
    
    await WorkStates.reg_enter_brthday.set()


# ввод даты рождения
@dp.message_handler(state=WorkStates.reg_enter_brthday, regexp=r'\d{4}\.\d{2}\.\d{2}')
async def enter_brth(msg: types.Message, state: FSMContext):
    # TODO: проверка на формат даты
    async with state.proxy() as data:
        data["birthday"] = msg.text
    await msg.reply("Ок")
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
    await bot.send_message(callback.from_user.id, "Ок")
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
            # TODO: заполнить нулями (а может и не надо - чтобы сохранить статистику)
            Report.create(rielter_id=data["rielter_id"]).save()
    profile = Rielter.get(Rielter.rielter_id == callback.from_user.id)
    # TODO: всрать клавиатуру
    await bot.send_message(callback.from_user.id, f"Ваш профиль сформирован!\n\nID: {profile.rielter_id},\nФИО: {profile.fio},\nДата рождения: {profile.birthday},\nПол: {profile.gender},\nНаправление работы: {Rielter_type.get_by_id(pk=profile.rielter_type).rielter_type_name}")
    await bot.send_message(callback.from_user.id, f"В каком направлении будешь работать сейчас?", reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()

    # запуск утреннего и вечернего оповещения 
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(good_morning_notification, trigger=CronTrigger(hour=10, minute=0), kwargs={"chat_id": callback.from_user.id, "bot": bot})
    scheduler.add_job(good_evening_notification, trigger=CronTrigger(hour=19, minute=0), kwargs={"chat_id": callback.from_user.id, "bot": bot})
    scheduler.start()


# default хэндлер для клавиатуры, которая будет доступна всегда в состоянии ready
@dp.callback_query_handler(state=WorkStates.ready)
async def start_new_activity(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "analytics":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, предложить новую работу!")
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        if tmp:
            count += tmp.analytics
            Report.update(analytics=count+1).where(Report.rielter_id == callback.from_user.id).execute()
        scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(hours=1), kwargs={"chat_id": callback.from_user.id, "bot": bot, "text": "Чем займёшься дальше?", "state": WorkStates.ready, "keyboard": get_inline_menu_markup()})

    elif callback.data == "meeting":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, удачной поездки, вернусь...!")
        scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=3), kwargs={"chat_id": callback.from_user.id, "bot": bot, "text": "Как прошла встреча?", "state": WorkStates.deal_retult, "keyboard": get_meeting_result_markup()})

    elif callback.data == "call":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, поитересоваться твоими успехами!")
        scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(hours=1), kwargs={"chat_id": callback.from_user.id, "bot": bot, "text": "Как твои успехи в прозвонах? Сколько рабочих звонкоы ты успел совершить?", "state": WorkStates.enter_calls_count, "keyboard": None})

    elif callback.data == "show":
        pass
    elif callback.data == "search":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, предложить новую работу!")
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        if tmp:
            count += tmp.analytics
            Report.update(analytics=count+1).where(Report.rielter_id == callback.from_user.id).execute()
        scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(hours=1), kwargs={"chat_id": callback.from_user.id, "bot": bot, "text": "Чем займёшься дальше?", "state": WorkStates.ready, "keyboard": get_inline_menu_markup()})

    elif callback.data == "flyer":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, поитересоваться твоими успехами!")
        scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(hours=1), kwargs={"chat_id": callback.from_user.id, "bot": bot, "text": "Как твои успехи в расклейке? Прогулялся, отдохнул, готов к работе? Сколько объявлений ты расклеил?", "state": WorkStates.enter_flyer_count, "keyboard": None})
        
    elif callback.data == "deal":
        await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_meeting_markup())
        await WorkStates.deal_enter_deal_type.set()
    
    elif callback.data == "deposit":
        pass
    elif callback.data == "vacation":
        pass
    elif callback.data == "sick_leave":
        pass
    else:
        print("О нет, необработанная ситация!\nПросим вас сделать скриншот этой ситуации и направить разработчикам. ")


# количество расклеенных листовок
@dp.message_handler(lambda msg: msg.text, state=WorkStates.enter_flyer_count)
async def enter_posting_adverts_count(msg: types.Message, state: FSMContext):
    count: int = 0
    try:
        count = int(msg.text)
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!")
        return
    await msg.answer("Молодчина!")
    tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
    if tmp:
        count += tmp.posting_adverts
        Report.update(posting_adverts=count).where(Report.rielter_id == msg.from_user.id).execute()
    await WorkStates.ready.set()
    

# количество звонков
@dp.message_handler(lambda msg: msg.text, state=WorkStates.enter_calls_count)
async def enter_posting_adverts_count(msg: types.Message, state: FSMContext):
    count: int = 0
    try:
        count = int(msg.text)
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!")
        return
    await msg.answer("Просто супер!")
    tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
    if tmp:
        count += tmp.cold_call_count
        Report.update(cold_call_count=count).where(Report.rielter_id == msg.from_user.id).execute()
    await WorkStates.ready.set()


# вид сделки
@dp.message_handler(lambda msg: msg.text in ["Квартира", "Земля", "Дом", "Назад"], state=WorkStates.deal_enter_deal_type)
async def enter_deal_type(msg: types.Message, state: FSMContext):
    if msg.text == "Назад":
        await msg.answer(text="Отмена!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text=f"В каком направлении будешь работать сейчас?", reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        return
    
    elif msg.text == "Квартира":
        pass
    elif msg.text == "Земля": 
        pass
    elif msg.text == "Дом":
        pass
    
    scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(seconds=5), kwargs={"chat_id": msg.from_user.id, "bot": bot, "text": f"Как прошла сделка в категории: #{msg.text} ?", "state": WorkStates.deal_retult, "keyboard": get_meeting_result_markup()})
    await msg.answer(text=f"Отлично! Вернусь через [некоторое время] и спрошу как у тебя дела!", reply_markup=types.ReplyKeyboardRemove())
    await WorkStates.ready.set()


# результат сделки
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо", "Есть возражения"], state=WorkStates.deal_retult)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    if msg.text == "Хорошо":
        tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
        count = 0
        if tmp:
            count += tmp.deals_count
            Report.update(posting_adverts=count+1).where(Report.rielter_id == msg.from_user.id).execute()
        await msg.answer("Ну ты молодец, я в тебя верил!")
    elif msg.text == "Плохо":
        await msg.answer("Не расстраивайся! Давай разберемся:", reply_markup=get_bad_deal_result())
        await WorkStates.deal_bad_result.set()


# результат сделки
@dp.message_handler(lambda msg: msg.text in ["Плохой объект", "Продавец неграмотный", "Назад"], state=WorkStates.deal_bad_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    if msg.text == "Плохой объект":
        pass
    elif msg.text == "Продавец неграмотный":
        pass
    else:
        await send_notification(chat_id=msg.from_user.id, bot=bot, text="Как прошла встреча?", state=WorkStates.deal_retult, keyboard=get_meeting_result_markup())
        await WorkStates.deal_retult.set()


# TODO: скорее всего надо будет написать команду "запланировать активность"