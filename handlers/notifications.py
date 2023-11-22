from aiogram import types, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time, date, timedelta
from models import *
from aiogram.dispatcher.filters.state import State
from bot import *
import holidays
import asyncio


last_messages = dict() # словарь структуры { chat_id : (lasr_message_time, bool) }
holidays_ru = {"state_holidays": {}, "birthdays": {}}


# таймер игнора
async def counter_time(chat_id: int, bot: Bot) -> None:
    time_point = datetime.now().time()
    if time_point > time(18, 0) or time_point < time_point(10, 0):
        return
    last_messages[chat_id] = (time_point, True)
    await asyncio.sleep(10) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты занят, расскажи, пожалуйста, как у тебя дела?")
    else:
        return
    
    await asyncio.sleep(10) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты очень сильно занят, но напиши, пожалуйста, как у тебя дела?")
    else:
        return
    
    await asyncio.sleep(10) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник #{chat_id} не отвечает на сообщения уже 3 часа!")
        await bot.send_message(chat_id=chat_id, text=f"О нет, вы игнорируете меня уже 3 часа к ряду! Я был вынужден сообщить вашему руководителю.")
    else:
        return
    

# напоминание
async def send_notification(chat_id: int, bot: Bot, text: str, state: State, keyboard, timeout: bool):
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    if state:
        await state.set()
    if timeout:
        await counter_time(chat_id=chat_id, bot=bot)

        
# ежедневные утренние напоминания
async def morning_notifications(chat_id: int, bot: Bot, text: str, state: State, keyboard):
    # ежедневный сброс счётчиков
    tmp = Report.get_or_none(Report.rielter_id == chat_id)
    if tmp:
        tmp.cold_call_count = 0
        tmp.meet_new_objects = 0
        tmp.take_in_work = 0
        tmp.contrects_signed = 0
        tmp.show_objects = 0
        tmp.posting_adverts = 0
        tmp.ready_deposit_count = 0
        tmp.take_deposit_count = 0
        tmp.deals_count = 0
        tmp.analytics = 0
        tmp.save()
    else:
        Report.create(rielter_id=chat_id).save()

    holidays_ru["state_holidays"] = holidays.Russia(years=datetime.now().year)
    if datetime.now().weekday() == 5 or datetime.now().weekday() == 6 or datetime.now().date() in holidays_ru:
        if datetime.now().date() in holidays_ru:
            await bot.send_message(chat_id=chat_id, text=f"Поздравляю с праздником! Сегодня - {holidays_ru['state_holidays'][datetime.now().date()]}", reply_markup=keyboard)
        return

    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    # напоминания на день
    task_list: list = Task.select().where(Task.rielter_id == chat_id and Task.date_planed == datetime.now().date())
    if len(task_list) != 0:
        tasks_str = f"Напоминаю, что на сегодня вы запланировали:\n\n"
        for task in task_list:
            tasks_str = tasks_str + f" - {task.task_name} ({task.task_deskription})\n\n"
        await bot.send_message(chat_id=chat_id, text=tasks_str)
    if state:
        await state.set()


def get_total_statistics(currentWorkerId: int) -> str:
    results = Report.get_or_none(Report.rielter_id == currentWorkerId)
    if results:
        results_str = f"Долгосрочная статистика сотрудника #{currentWorkerId}:\n"
        results_str += f"\nзвонков: {results.total_cold_call_count} \nвыездов на осмотры: {results.total_meet_new_objects}" \
            + f"\nаналитика: {results.total_analytics} \nподписано контрактов: {results.total_contrects_signed}" \
            + f"\nпоказано объектов: {results.total_show_objects} \nрасклеено объявлений: {results.total_posting_adverts}" \
            + f"\nклиентов готовых подписать договор: {results.total_take_in_work} \nклиентов внесли залог: {results.total_take_deposit_count}" \
            + f"\nзавершено сделок: {results.total_deals_count}"
        return results_str


# ежедневное вечернее подведение итогов
async def good_evening_notification(chat_id: int, bot: Bot):
    holidays_ru["state_holidays"] = holidays.Russia(years=datetime.now().year)
    # др
    for rielter in Rielter.select().where(fn.strftime('%m-%d', Rielter.birthday) == (date.today() + timedelta(days=1)).strftime('%m-%d')):
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Напоминаю, что завтра день рождения у нашего коллеги - {rielter.fio}!\n")
    
    if datetime.now().weekday() == 5 or datetime.now().weekday() == 6 or datetime.now().date() in holidays_ru:
        return
    day_results = Report.get_or_none(Report.rielter_id == chat_id)
    day_results_str = ""
    if day_results:
        day_results_str = f"\nЗвонков: {day_results.cold_call_count} \nвыездов на осмотры: {day_results.meet_new_objects}" \
            + f"\nаналитика: {day_results.analytics} \nподписано контрактов: {day_results.contrects_signed}" \
            + f"\nпоказано объектов: {day_results.show_objects} \nрасклеено объявлений: {day_results.posting_adverts}" \
            + f"\nклиентов готовых подписать договор: {day_results.take_in_work} \nклиентов внесли залог: {day_results.take_deposit_count}" \
            + f"\nзавершено сделок: {day_results.deals_count}"
    # dop_res: str = "" # TODO: похвалить по категориям
    # if day_results.cold_call_count >= 5:

    # if day_results.meet_new_objects >= 2:
    # if day_results.show_objects >= 
    # if day_results.posting_adverts >= 10:
    # if day_results.ready_deposit_count
    # if day_results.take_deposit_count
    # if day_results.deals_count

        day_results.total_cold_call_count += day_results.cold_call_count
        day_results.total_meet_new_objects  += day_results.meet_new_objects
        day_results.total_take_in_work  += day_results.take_in_work
        day_results.total_contrects_signed  += day_results.contrects_signed
        day_results.total_show_objects  += day_results.show_objects
        day_results.total_posting_adverts  += day_results.posting_adverts
        day_results.total_take_deposit_count  += day_results.take_deposit_count
        day_results.total_deals_count  += day_results.deals_count
        day_results.total_analytics  += day_results.analytics
        day_results.save()
    else:
        Report.create(rielter_id=chat_id).save()

    worker = Rielter.get_by_id(pk=chat_id)

    await bot.send_message(chat_id=chat_id, text=f"Доброе вечер! Жаль, но пора заканчивать рабочий день. \n\nДавай посмотрим, как ты потрудился сегодня: \n{day_results_str}")
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник #{chat_id} {worker.fio} завершил рабочий день. \nОтчет: \n{day_results_str}")
    