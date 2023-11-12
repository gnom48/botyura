from aiogram.dispatcher.filters.state import StatesGroup, State

class WorkStates(StatesGroup):
    reg_enter_login = State()
    reg_enter_brthday = State()
    reg_enter_gender = State()
    reg_enter_type = State()
    ready = State()
    restart = State()