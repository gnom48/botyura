from aiogram.dispatcher.filters.state import StatesGroup, State

class WorkStates(StatesGroup):
    reg_enter_login = State()
    reg_enter_brthday = State()
    reg_enter_gender = State()
    reg_enter_type = State()

    ready = State()

    enter_flyer_count = State()
    enter_calls_count = State()

    deal_enter_deal_type = State()
    deal_retult = State()
    deal_bad_result = State()
    show_result = State()
    deposit_result = State()

    meet_new_object_result = State()

    no_work_type = State()
    enter_days_ill_or_rest = State()

    task_name = State()
    task_desc = State()
    task_date = State()

    enter_task_id = State()

    restart = State()