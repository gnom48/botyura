from aiogram import types, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from models import *
from aiogram.dispatcher.filters.state import State
from bot import *
import holidays


# напоминание
async def send_notification(chat_id: int, bot: Bot, text: str, state: State, keyboard):
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    if state:
        await state.set()
        
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
        tmp.save()
    else:
        Report.create(rielter_id=chat_id).save()

    holidays_ru = holidays.Russia(years=datetime.now().year)
    if datetime.now().weekday() == 5 or datetime.now().weekday() == 6 or datetime.now().date() in holidays_ru:
        if datetime.now().date() in holidays_ru:
            await bot.send_message(chat_id=chat_id, text=f"Поздравляю с праздником! Сегодня - {holidays_ru[datetime.now().date()]}", reply_markup=keyboard)
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


# ежедневное вечернее подведение итогов
async def good_evening_notification(chat_id: int, bot: Bot):
    holidays_ru = holidays.Russia(years=datetime.now().year)
    if datetime.now().weekday() == 5 or datetime.now().weekday() == 6 or datetime.now().date() in holidays_ru:
        return
    day_results = Report.get(Report.rielter_id == chat_id)
    day_results_str = f"\nЗвонков: {day_results.cold_call_count} \nвыездов на осмотры: {day_results.meet_new_objects}" \
        + f"\аналитика: {day_results.analytics} \nподписано контрактов: {day_results.contrects_signed}" \
        + f"\nпоказано объектов: {day_results.show_objects} \nрасклеено объявлений: {day_results.posting_adverts}" \
        + f"\nклиентов готовых подписать договор: {day_results.take_deposit_count} \nклиентов внесли залог: {day_results.take_deposit_count}" \
        + f"\nзавершено сделок: {day_results.deals_count}"
    # dop_res: str = ""
    # if day_results.cold_call_count >= 5:

    # if day_results.meet_new_objects >= 2:
    # if day_results.show_objects >= 
    # if day_results.posting_adverts >= 10:
    # if day_results.ready_deposit_count
    # if day_results.take_deposit_count
    # if day_results.deals_count

    await bot.send_message(chat_id=chat_id, text=f"Доброе вечер! Жаль, но заканчивать рабочий день. \n\nДавай посмотрим, как ты потрудился сегодня: \n{day_results_str}")
    