from aiogram.utils import executor
from handlers import *
from models import *


create_db()

executor.start_polling(dp, skip_updates=True)