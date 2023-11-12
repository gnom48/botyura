from aiogram.utils import executor
from handlers import *
from models import *


# TODO: подготовка работы с бд
create_db()


executor.start_polling(dp, skip_updates=True)