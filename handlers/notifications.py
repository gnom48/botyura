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
from aiogram.dispatcher import Dispatcher


last_messages = dict() # словарь структуры { chat_id : (lasr_message_time, bool) }
holidays_ru = {"state_holidays": {}, "birthdays": {}}

main_scheduler = AsyncIOScheduler(timezone="UTC")
support_scheduler = AsyncIOScheduler(timezone="UTC")
month_week_scheduler = AsyncIOScheduler(timezone="UTC")


# таймер игнора СТАВИТЬ СТРОГО ПОСЛЕ УСТАНОВКИ СОСТОЯНИЯ
async def counter_time(chat_id: int, bot: Bot) -> None:
    time_point = dt.now().time()
    if time_point > time(18-3, 0) or time_point < time(10-3, 0):
        return
    last_messages[chat_id] = (time_point, True)
    await asyncio.sleep(1800) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты занят, расскажи, пожалуйста, как у тебя дела?")
    else:
        return
    
    await asyncio.sleep(3600) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True):
        await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты очень сильно занят, но напиши, пожалуйста, как у тебя с делом?")
    else:
        return
    
    await asyncio.sleep(3600) # 3600 - 1 час
    if last_messages[chat_id] == (time_point, True) and not (dt.now().weekday() == 5 or dt.now().weekday() == 6 or dt.now() in holidays_ru["state_holidays"]):
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник {Rielter.get_or_none(Rielter.rielter_id == chat_id).fio} (#{chat_id}) не отвечает на сообщения уже 3 часа!")
        await bot.send_message(chat_id=chat_id, text=f"О нет, вы игнорируете меня уже 3 часа к ряду! Я был вынужден сообщить вашему руководителю.")
    else:
        return

   
# таймер игнора для группы пользователей СТАВИТЬ СТРОГО ПОСЛЕ УСТАНОВКИ СОСТОЯНИЯ
async def counter_time_group(chats: list, bot: Bot) -> None:
    time_point = dt.now().time()
    if time_point > time(18-3, 0) or time_point < time(10-3, 0):
        return
    for i in chats:
        last_messages[i] = (time_point, True)
    await asyncio.sleep(1800) # 3600 - 1 час
    for i in chats:
        if last_messages[i] == (time_point, True):
            await bot.send_message(chat_id=i, text="Я понимаю, что ты занят, расскажи, пожалуйста, как у тебя дела?")
        else:
            continue
    await asyncio.sleep(3600) # 3600 - 1 час
    for i in chats:
        if last_messages[i] == (time_point, True):
            await bot.send_message(chat_id=chats, text="Я понимаю, что ты очень сильно занят, но напиши, пожалуйста, как у тебя с делом?")
        else:
            continue
    await asyncio.sleep(3600) # 3600 - 1 час
    for i in chats:
        if last_messages[i] == (time_point, True) and not (dt.now().weekday() == 5 or dt.now().weekday() == 6 or dt.now() in holidays_ru["state_holidays"]):
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник {Rielter.get_or_none(Rielter.rielter_id == chats).fio} (#{chats}) не отвечает на сообщения уже 3 часа!")
            await bot.send_message(chat_id=chats, text=f"О нет, вы игнорируете меня уже 3 часа к ряду! Я был вынужден сообщить вашему руководителю.")
        else:
            continue
    

# универсальное сообщение
async def send_notification(chat_id: int, bot: Bot, text: str, state: State, keyboard, timeout: bool):
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    if state:
        await state.set()
    if timeout:
        await counter_time(chat_id=chat_id, bot=bot)

        
# ежедневные утренние напоминания
async def morning_notifications(bot: Bot, dp: Dispatcher):
    # сброс счётчиков
    last_messages.clear()

    # др
    for rielter in Rielter.select():
        try:
            if rielter.birthday[:5] == dt.now().strftime('%d-%m'):
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"От наших коллег, руководителей и от себя, поздравляю тебя с днем рождения! 🎉 Желаю вам океан счастья, гору улыбок и сверкающих моментов в этот особенный день! 🎂❤️")
        except:
            pass

    holidays_ru["state_holidays"] = holidays.Russia(years=dt.now().year)
    for rielter in Rielter.select():
        holidays_ru["birthdays"][rielter.birthday] = rielter.fio

    reports = Report.select()
    chats = []
    for tmp in reports:
        chats.append(tmp.rielter_id)
        
        # tmp.cold_call_count = 0
        # tmp.meet_new_objects = 0
        # tmp.take_in_work = 0
        # tmp.contrects_signed = 0
        # tmp.show_objects = 0
        # tmp.posting_adverts = 0
        # tmp.ready_deposit_count = 0
        # tmp.take_deposit_count = 0
        # tmp.deals_count = 0
        # tmp.analytics = 0
        # tmp.bad_seller_count = 0
        # tmp.bad_object_count = 0
        # tmp.save()

        # напоминания на день
        task_list: list = Task.select().where(Task.rielter_id == tmp.rielter_id)
        tasks_str = ""
        if len(task_list) != 0:
            tasks_str = f"Напоминаю, что на сегодня ты запланировал:\n\n"
            for task in task_list:
                if tmp.rielter_id == task.rielter_id and dt.strptime(task.date_planed, '%d-%m-%Y').date() == dt.now().date():
                    tasks_str = tasks_str + f" - {task.task_name}\n\n"
                    time_obj: dt
                    try:
                        time_obj = dt.strptime(str(task.time_planed), '%H:%M:%S').time()
                    except:
                        continue
                    dt_tmp = dt(year=dt.now().year, month=dt.now().month, day=dt.now().day, hour=time_obj.hour, minute=time_obj.minute, second=0)
                    tmpKwargs = {"chat_id": tmp.rielter_id, "bot": bot, "text": f"Напоминаю, что ты запланировал в {task.time_planed} заняться: {task.task_name}", "state": None, "keyboard": None, "timeout": False}
                    support_scheduler.add_job(send_notification, trigger="date", run_date=(dt_tmp - timedelta(hours=3, seconds=10)), kwargs=tmpKwargs)
                    Task.delete().where(Task.id == task.id).execute()
            await bot.send_message(chat_id=tmp.rielter_id, text=tasks_str)

        if dt.now().weekday() == 5 or dt.now().weekday() == 6 or dt.now() in holidays_ru["state_holidays"]:
            if dt.now() in holidays_ru['state_holidays']:
                await bot.send_message(chat_id=tmp.rielter_id, text=f"Поздравляю с праздником! Сегодня - {holidays_ru['state_holidays'][dt.now()]}")
            return

        last_messages[tmp.rielter_id] = (dt.now().time(), True)
        await bot.send_message(chat_id=tmp.rielter_id, text=get_day_plan(Rielter.get_by_id(pk=tmp.rielter_id).rielter_type_id))

        await bot.send_message(chat_id=tmp.rielter_id, text=generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await dp.storage.set_state(user=tmp.rielter_id, state=WorkStates.ready)
    await counter_time_group(chats=chats, bot=bot)


# ежедневное вечернее подведение итогов
async def good_evening_notification(bot: Bot):
    holidays_ru["state_holidays"] = holidays.Russia(years=dt.now().year)
    # др
    for rielter in Rielter.select():
        try:
            if rielter.birthday[:5] == (dt.now() + timedelta(days=1)).strftime('%d-%m'):
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Напоминаю, что завтра день рождения у нашего коллеги - {rielter.fio}!\n")
        except:
            pass

    flag = False
    if dt.now().weekday() == 5 or dt.now().weekday() == 6 or dt.now() in holidays_ru["state_holidays"]:
        flag = True
    
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
            vb = InlineKeyboardButton(text='Про звонки 🎥', url=why_bad_str_list[1][1])
            kb.add(vb)
        elif 5 <= day_results.cold_call_count < 10:
            calls_praise = "Молодец! Продолжай в том же духе! 👍"
        else:
            calls_praise = "Ты просто супер! Ты крутой сотрудник! 🥳"

        # Расклейка
        if day_results.posting_adverts < 50:
            stickers_praise = "Плохо! Нужно больше расклеек! 😔 Давай посмотрим видео-материалы про правила расклейки, может быть ты подчерпнешь для себя что-то новое."
            vb = InlineKeyboardButton(text='Про расклейки 🎥', url=why_bad_str_list[2][1])
            kb.add(vb)
        elif 50 <= day_results.posting_adverts < 100:
            stickers_praise = "Молодец! Так держать! 👍"
        else:
            stickers_praise = "Супер молодец! Мега продуктивная работа! 🥳"

        # Связанное предложение
        praise_sentence = f"Что я могу сказать по поводу эффективности твоей работы:\n\nЗвонки: {calls_praise}\n\nРасклейка: {stickers_praise}"

        worker = Rielter.get_by_id(pk=day_results.rielter_id)

        if not flag:
            await bot.send_message(chat_id=day_results.rielter_id, text=f"Доброе вечер! Жаль, но пора заканчивать рабочий день. \n\nДавай посмотрим, как ты потрудился сегодня:") #\n{day_results_str}")
            await bot.send_message(chat_id=day_results.rielter_id, text=f"{praise_sentence}", reply_markup=kb)
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник {worker.fio} (#{day_results.rielter_id}) завершил рабочий день. \nОтчет: \n{day_results_str}")

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
            
        month_result = MonthReport.get_or_none(MonthReport.rielter_id == day_results.rielter_id)
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

        day_res = Report.get_or_none(Report.rielter_id == day_results.rielter_id)
        if day_res:
            day_res.cold_call_count = 0
            day_res.meet_new_objects = 0
            day_res.take_in_work = 0
            day_res.contrects_signed = 0
            day_res.show_objects = 0
            day_res.posting_adverts = 0
            day_res.ready_deposit_count = 0
            day_res.take_deposit_count = 0
            day_res.deals_count = 0
            day_res.analytics = 0
            day_res.bad_seller_count = 0
            day_res.bad_object_count = 0
            day_res.save()


# статистики еженедельная [отправить]
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
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=results_str)

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


# статистики ежемесячная [текст]
def get_month_statistics_str(rielter_id) -> str:
    results = Report.get_or_none(Report.rielter_id == rielter_id)
    tmp = Rielter.get_or_none(Rielter.rielter_id == rielter_id)
    results_str = f"Статистика сотрудника {tmp.fio} (#{tmp.rielter_id}) за последний месяц:\n"
    results_str += f"\nзвонков: {results.cold_call_count} \nвыездов на осмотры: {results.meet_new_objects}" \
        + f"\nаналитика: {results.analytics} \nподписано контрактов: {results.contrects_signed}" \
        + f"\nпоказано объектов: {results.show_objects} \nрасклеено объявлений: {results.posting_adverts}" \
        + f"\nклиентов готовых подписать договор: {results.take_in_work} \nклиентов внесли залог: {results.take_deposit_count}" \
        + f"\nзавершено сделок: {results.deals_count}\n" \
        + f"\nнарвался на плохих продавцов / клиентов: {results.bad_seller_count}" \
        + f"\nнарвался на плохие объекты: {results.bad_object_count}"
    return results_str


# статистики ежемесячная [отправить]
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
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=results_str)

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
