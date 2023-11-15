from aiogram import types, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from models import *
from aiogram.dispatcher.filters.state import State


# напоминание
async def send_notification(chat_id: int, bot: Bot, text: str, state: State, keyboard):
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    await state.set()


# ежедневное утреннее приветствие
async def good_morning_notification(chat_id: int, bot: Bot):
    # TODO: я не знаю откуда брать данные (мб из бд)
    await bot.send_message(chat_id=chat_id, text="Доброе утро! Как настроение, готов поработать?\n Чем думаешь заниматься сегодня?\nНапоминаю, что у тебя на чегодня запланировано: ...")
    # ежедневный сброс счётчиков
    tmp = Report.get_by_id(pk=chat_id)
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

# ежедневное вечернее подведение итогов
async def good_evening_notification(chat_id: int, bot: Bot):
    # TODO: я не знаю какую информацию выводить
    day_results = Report.get(Report.rielter_id == chat_id)
    day_results_str = f"\nЗвонков: {day_results.cold_call_count}, \nвыездов на осмотры: {day_results.meet_new_objects}" \
        + f"\nпринято объектов в работу: {day_results.take_in_work}, \nподписано контрактов: {day_results.contrects_signed}" \
        + f"\nпоказано объектов: {day_results.show_objects}, \nрасклеено объявлений: {day_results.posting_adverts}" \
        + f"\nклиентов готовых подписать договор: {day_results.ready_deposit_count}, \nклиентов внесли залог: {day_results.take_deposit_count}" \
        + f"\nзавершено сделок: {day_results.deals_count}"
    await bot.send_message(chat_id=chat_id, text=f"Доброе вечер! Жаль, но заканчивать рабочий день. Давай посмотрим, как ты потрудился сегодня: {day_results_str}")
    