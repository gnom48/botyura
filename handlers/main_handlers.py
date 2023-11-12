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


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# старт регистрации
@dp.message_handler(commands=['start'], state="*")
async def start_cmd(msg: types.Message):
    oldRielter = Rielter.get_by_id(pk=msg.from_user.id)
    if oldRielter:
        await msg.answer(f"С возвращением, {oldRielter.fio}!", reply_markup=types.ReplyKeyboardRemove())
        await WorkStates.ready.set()
        return
    await msg.answer("Привет!", reply_markup=get_start_markup())
    await WorkStates.restart.set()


# подтверждение начала регистрацииовлво
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
@dp.message_handler(state=WorkStates.reg_enter_brthday)
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
    await bot.send_message(callback.from_user.id, f"Ваш профиль сформирован!\n\nID: {profile.rielter_id},\nФИО: {profile.fio},\nДата рождения: {profile.birthday},\nПол: {profile.gender},\nНаправление работы: {Rielter_type.get_by_id(pk=profile.rielter_type).rielter_type_name}", reply_markup=None)
    await WorkStates.ready.set()

    # запуск утреннего и вечернего оповещения 
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(good_morning_notification, trigger=CronTrigger(hour=10, minute=0), kwargs={"chat_id": callback.from_user.id, "bot": bot})
    scheduler.add_job(good_evening_notification, trigger=CronTrigger(hour=19, minute=0), kwargs={"chat_id": callback.from_user.id, "bot": bot})
    scheduler.start()


# default хэндлер для клавиатуры, которая будет доступна всегда в состоянии ready
@dp.message_handler(lambda msg: msg.text, state=WorkStates.ready)
async def start_new_activity(msg: types.Message, state: FSMContext):
    if msg.text == "Расклейка":
        msg.answer("Хорошо, я вернусь через час, поитересоваться твоими успехами!")

        scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
        scheduler.add_job(send_notification, trigger="date", run_date=datetime.now() + timedelta(hours=1), kwargs={"msg": msg, "text": "Как твои успехи в расклейке? Прогулялся, отдохнул, готов к работе?"})
        scheduler.start()
        
    elif msg.text == "Прозвон":
        pass
        # так то можно аналогичные scheduler'ы написать но надо как то оптимизировать
    elif msg.text == "Показ":
        pass
    elif msg.text == "Осмотр":
        pass
    elif msg.text == "Сделка":
        pass
    else:
        pass


# TODO: скорее всего надо будет написать команду "запланировать активность"