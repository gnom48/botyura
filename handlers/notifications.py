from aiogram import types, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import time, date, timedelta
from datetime import datetime as dt
from models import *
from keybords import *
from aiogram.dispatcher.filters.state import State
from bot import *
import holidays
import asyncio


last_messages = dict() # словарь структуры { chat_id : (lasr_message_time, bool) }
holidays_ru = {"state_holidays": {}, "birthdays": {}}


# таймер игнора
async def counter_time(chat_id: int, bot: Bot) -> None:
    time_point = dt.now().time()
    # if time_point > time(18, 0) or time_point < time_point(10, 0):
    #     return
    last_messages[chat_id] = (time_point, True)
    await asyncio.sleep(10) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты занят, расскажи, пожалуйста, как у тебя дела?")
    else:
        return
    
    await asyncio.sleep(20) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты очень сильно занят, но напиши, пожалуйста, как у тебя дела?")
    else:
        return
    
    await asyncio.sleep(30) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        # await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник {Rielter.get_or_none(Rielter.rielter_id == chat_id).fio} (#{chat_id}) не отвечает на сообщения уже 3 часа!")
        await bot.send_message(chat_id=chat_id, text=f"О нет, вы игнорируете меня уже 3 часа к ряду! Я был вынужден сообщить вашему руководителю.")
    else:
        return
    

# универсальное сообщение
async def send_notification(chat_id: int, bot: Bot, text: str, state: State, keyboard, timeout: bool):
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    if state:
        await state.set()
    if timeout:
        await counter_time(chat_id=chat_id, bot=bot)

        
# ежедневные утренние напоминания
async def morning_notifications(bot: Bot):
    # ежедневный сброс счётчиков
    last_messages.clear()

    holidays_ru["state_holidays"] = holidays.Russia(years=dt.now().year)
    for rielter in Rielter.select():
        holidays_ru["birthdays"][rielter.birthday] = rielter.fio

    reports = Report.select()
    for tmp in reports:
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
        tmp.bad_seller_count = 0
        tmp.bad_object_count = 0
        tmp.save()

        if dt.now().weekday() == 5 or dt.now().weekday() == 6 or dt.now().date() in holidays_ru:
            if dt.now().date() in holidays_ru:
                await bot.send_message(chat_id=tmp.rielter_id, text=f"Поздравляю с праздником! Сегодня - {holidays_ru['state_holidays'][dt.now().date()]}")
            # return
        try:
            if dt.now().date() in holidays_ru["birthdays"][dt.now().date()]:
                await bot.send_message(chat_id=tmp.rielter_id, text=f"От наших коллег, руководителей и от себя, поздравляю тебя с днем рождения! 🎉 Желаю вам океан счастья, гору улыбок и сверкающих моментов в этот особенный день! 🎂❤️")
        except:
            pass

        await bot.send_message(chat_id=tmp.rielter_id, text=get_day_plan(Rielter.get_by_id(pk=tmp.rielter_id).rielter_type_id))

        # напоминания на день
        task_list: list = Task.select().where(Task.rielter_id == tmp.rielter_id and Task.date_planed == dt.now().date())
        if len(task_list) != 0:
            tasks_str = f"Напоминаю, что на сегодня вы запланировали:\n\n"
            for task in task_list:
                tasks_str = tasks_str + f" - {task.task_name} ({task.task_deskription})\n\n"
            await bot.send_message(chat_id=tmp.rielter_id, text=tasks_str)


# статистики еженедельная
async def get_week_statistics(bot: Bot):
    weekResolts = WeekReport.select()
    for results in weekResolts:
        tmp = Rielter.get_or_none(Rielter.rielter_id == results.rielter_id)
        results_str = f"Статистика сотрудника {tmp.fio} (#{tmp.rielter_id}) за последнюю рабочую неделю:\n"
        results_str += f"\nзвонков: {results.cold_call_count} \nвыездов на осмотры: {results.meet_new_objects}" \
            + f"\nаналитика: {results.analytics} \nподписано контрактов: {results.contrects_signed}" \
            + f"\nпоказано объектов: {results.show_objects} \nрасклеено объявлений: {results.posting_adverts}" \
            + f"\nклиентов готовых подписать договор: {results.take_in_work} \nклиентов внесли залог: {results.take_deposit_count}" \
            + f"\nзавершено сделок: {results.deals_count}\n" \
            + f"\nнарвался на плохих продавцов / клиентов: {results.bad_seller_count}" \
            + f"\nнарвался на плохие объекты: {results.bad_object_count}"
        await bot.send_message(chat_id=tmp.rielter_id, text=results_str)

        results.cold_call_count = 0
        results.meet_new_objects = 0
        results.take_in_work = 0
        results.contrects_signed = 0
        results.show_objects = 0
        results.posting_adverts = 0
        results.ready_deposit_count = 0
        results.take_deposit_count = 0
        results.deals_count = 0
        results.analytics = 0
        results.bad_seller_count = 0
        results.bad_object_count = 0
        results.save()



# статистики ежемесячная
async def get_month_statistics(bot: Bot):
    monthResults = MonthReport.select()
    for results in monthResults:
        tmp = Rielter.get_or_none(Rielter.rielter_id == results.rielter_id)
        results_str = f"Статистика сотрудника {tmp.fio} (#{tmp.rielter_id}) за последний месяц:\n"
        results_str += f"\nзвонков: {results.cold_call_count} \nвыездов на осмотры: {results.meet_new_objects}" \
            + f"\nаналитика: {results.analytics} \nподписано контрактов: {results.contrects_signed}" \
            + f"\nпоказано объектов: {results.show_objects} \nрасклеено объявлений: {results.posting_adverts}" \
            + f"\nклиентов готовых подписать договор: {results.take_in_work} \nклиентов внесли залог: {results.take_deposit_count}" \
            + f"\nзавершено сделок: {results.deals_count}\n" \
            + f"\nнарвался на плохих продавцов / клиентов: {results.bad_seller_count}" \
            + f"\nнарвался на плохие объекты: {results.bad_object_count}"
        await bot.send_message(chat_id=tmp.rielter_id, text=results_str)

        results.cold_call_count = 0
        results.meet_new_objects = 0
        results.take_in_work = 0
        results.contrects_signed = 0
        results.show_objects = 0
        results.posting_adverts = 0
        results.ready_deposit_count = 0
        results.take_deposit_count = 0
        results.deals_count = 0
        results.analytics = 0
        results.bad_seller_count = 0
        results.bad_object_count = 0
        results.save()


# ежедневное вечернее подведение итогов
async def good_evening_notification(bot: Bot):
    holidays_ru["state_holidays"] = holidays.Russia(years=dt.now().year)
    # др
    for rielter in Rielter.select().where(fn.strftime('%m-%d', Rielter.birthday) == (date.today() + timedelta(days=1)).strftime('%m-%d')):
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Напоминаю, что завтра день рождения у нашего коллеги - {rielter.fio}!\n")
    
    # if dt.dt.now().weekday() == 5 or dt.dt.now().weekday() == 6 or dt.dt.now().date() in holidays_ru:
    #     return
    
    dayReport = Report.select()
    day_results_str = ""
    for day_results in dayReport:
        day_results_str = f"\nЗвонков: {day_results.cold_call_count} \nвыездов на осмотры: {day_results.meet_new_objects}" \
            + f"\nаналитика: {day_results.analytics} \nподписано контрактов: {day_results.contrects_signed}" \
            + f"\nпоказано объектов: {day_results.show_objects} \nрасклеено объявлений: {day_results.posting_adverts}" \
            + f"\nклиентов готовых подписать договор: {day_results.take_in_work} \nклиентов внесли залог: {day_results.take_deposit_count}" \
            + f"\nзавершено сделок: {day_results.deals_count}\n" \
            + f"\nнарвался на плохих продавцов / клиентов: {day_results.bad_seller_count}" \
            + f"\nнарвался на плохие объекты: {day_results.bad_object_count}"
        
        kb = InlineKeyboardMarkup(row_width=1)

        # Звонки
        if day_results.cold_call_count < 5:
            calls_praise = "Мало! 😔 Ты должен делать минимум 5 звонков в день. Но не переживай, изучи эти материалы, и сможешь стать еще продуктивнее."
            vb = InlineKeyboardButton(text='Про звонки 🎥', url=why_bad_str_list[0][1])
            kb.add(vb)
        elif 5 <= day_results.cold_call_count < 10:
            calls_praise = "Молодец! Продолжай в том же духе! 👍"
        else:
            calls_praise = "Ты просто супер! Ты крутой сотрудник! 🥳"

        # Расклейка
        if day_results.posting_adverts < 50:
            stickers_praise = "Плохо! Нужно больше расклеек! 😔 Давай посмотрим видео-материалы про правила расклейки, может быть ты подчерпнешь для себя что-то новое."
            vb = InlineKeyboardButton(text='Про расклейки 🎥', url=why_bad_str_list[1][1])
            kb.add(vb)
        elif 50 <= day_results.posting_adverts < 100:
            stickers_praise = "Молодец! Так держать! 👍"
        else:
            stickers_praise = "Супер молодец! Мега продуктивная работа! 🥳"

        # Связанное предложение
        praise_sentence = f"Что я могу сказать по поводу эффективности твоей работы:\n\nЗвонки: {calls_praise}\n\nРасклейка: {stickers_praise}"

        worker = Rielter.get_by_id(pk=day_results.rielter_id)

        await bot.send_message(chat_id=day_results.rielter_id, text=f"Доброе вечер! Жаль, но пора заканчивать рабочий день. \n\nДавай посмотрим, как ты потрудился сегодня: \n{day_results_str}")
        await bot.send_message(chat_id=day_results.rielter_id, text=f"{praise_sentence}", reply_markup=kb)
        # await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник {worker.fio} (#{day_results.rielter_id}) завершил рабочий день. \nОтчет: \n{day_results_str}")

        week_result = WeekReport.get_or_none(WeekReport.rielter_id == day_results.rielter_id)
        if week_result:
            week_result.cold_call_count += day_results.cold_call_count
            week_result.meet_new_objects += day_results.meet_new_objects
            week_result.take_in_work += day_results.take_in_work
            week_result.contrects_signed += day_results.contrects_signed
            week_result.show_objects += day_results.show_objects
            week_result.posting_adverts += day_results.posting_adverts
            week_result.take_deposit_count += day_results.take_deposit_count
            week_result.deals_count += day_results.deals_count
            week_result.analytics += day_results.analytics
            week_result.bad_seller_count += day_results.bad_seller_count
            week_result.bad_object_count += day_results.bad_object_count
            week_result.save()
        else:
            WeekReport.create(rielter_id=day_results.rielter_id).save()
            
        month_result = WeekReport.get_or_none(WeekReport.rielter_id == day_results.rielter_id)
        if month_result:
            month_result.cold_call_count += day_results.cold_call_count
            month_result.meet_new_objects += day_results.meet_new_objects
            month_result.take_in_work += day_results.take_in_work
            month_result.contrects_signed += day_results.contrects_signed
            month_result.show_objects += day_results.show_objects
            month_result.posting_adverts += day_results.posting_adverts
            month_result.take_deposit_count += day_results.take_deposit_count
            month_result.deals_count += day_results.deals_count
            month_result.analytics += day_results.analytics
            month_result.bad_seller_count += day_results.bad_seller_count
            month_result.bad_object_count += day_results.bad_object_count
            month_result.save()
        else:
            WeekReport.create(rielter_id=day_results.rielter_id).save()
    