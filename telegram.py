from typing import Union

import telebot

from config import TELEGRAM_BOT_TOKEN
from utils import run_in_thread

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@run_in_thread
def send_message(chat_id: Union[int, str], message: str):
    print(f'{chat_id=}')
    bot.send_message(chat_id, message)
