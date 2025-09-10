# import sys
# import os
# import django
#
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tw_m_main')))
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tw_m_main.settings.settings')
# django.setup()
#
# from tw_m_main.auth.models import User

from typing import Union
from config import TELEGRAM_BOT_TOKEN
from utils import run_in_thread
import telebot


bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

COMMANDS = {
    "/start": "Приветствие и список команд",
    "/help": "Показать список команд",
    "/id": "Показать ваш chat_id"
}

def format_commands() -> str:
    return "\n".join(f"{cmd} — {desc}" for cmd, desc in COMMANDS.items())

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    text = (
        "👋 Привет! Я Telegram-бот для уведомлений.\n\n"
        "Доступные команды:\n"
        f"{format_commands()}"
    )
    bot.send_message(chat_id, text)
    print(f"[Telegram] Пользователь {chat_id} запустил /start")

@bot.message_handler(commands=['help'])
def help_command(message):
    chat_id = message.chat.id
    text = (
        "Список доступных команд:\n"
        f"{format_commands()}"
    )
    bot.send_message(chat_id, text)
    print(f"[Telegram] Пользователь {chat_id} запросил /help")

@bot.message_handler(commands=['id'])
def send_chat_id(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"Ваш chat_id: <b>{chat_id}</b>")
    print(f"[Telegram] Пользователь запросил chat_id: {chat_id}")

@bot.message_handler(func=lambda m: True)
def echo_and_show_id(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"Ваш chat_id: <b>{chat_id}</b>")
    print(f"[Telegram] Получено сообщение от {chat_id}: {message.text}")

# @bot.message_handler(commands=['link'])
# def link_account(message):
#     args = message.text.split()
#     if len(args) < 2:
#         bot.reply_to(message, "Укажите email: /link your@email.com")
#         return
#     email = args[1].strip()
#     try:
#         user = User.objects.get(email=email)
#         user.telegram_chat_id = str(message.chat.id)
#         user.save(update_fields=['telegram_chat_id'])
#         bot.reply_to(message, "✅ Telegram успешно привязан к аккаунту.")
#     except User.DoesNotExist:
#         bot.reply_to(message, "❌ Пользователь с таким email не найден.")

@run_in_thread
def send_message(chat_id: Union[int, str], message: str):
    try:
        print(f"[Telegram] Отправка в {chat_id}: {message}")
        bot.send_message(chat_id, message)
    except Exception as e:
        print(f"[Telegram][ERROR] Не удалось отправить сообщение: {e}")

def run_bot():
    print("[Telegram] Бот запущен. Напишите ему в Telegram, чтобы узнать chat_id.")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)


# if __name__ == '__main__':
#     run_bot()
