import os
import logging
import asyncio
import traceback
import html
import json
import tempfile
import pydub
from pathlib import Path
from datetime import datetime
import re
from datetime import datetime, timedelta, date

import telegram
from telegram import (
    Update,
    User,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    AIORateLimiter,
    filters
)
from telegram.constants import ParseMode, ChatAction

import config
import database
import openai_utils
import fortune_requests


# setup
db = database.Database()
logger = logging.getLogger(__name__)

user_semaphores = {}
user_tasks = {}

# ⚪ /retry – спросить бота ещё раз
# ⚪ /new – Начать новый диалог
# ⚪ /mode – Select chat mode
HELP_MESSAGE = """Commands:
⚪ /settings – Показать настройки
⚪ /balance – Показать баланс
⚪ /help – Показать комманды
"""


def split_text_into_chunks(text, chunk_size):
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]

async def start_handle(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    reply_text = "Я таролог, маг и предсказатель. Я использую таро-карты, чтобы предсказывать будущее и помочь людям в их жизни. \n"
    reply_text += "\nКак я могу помочь?"

    await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)

async showlog():
    messages = db.get_last_n_dialog_messages(10)
    messages = str(messages)
    await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)

async def help_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    await update.message.reply_text(HELP_MESSAGE, parse_mode=ParseMode.HTML)

async def message_handle(update: Update, context: CallbackContext, message=None, use_new_dialog_timeout=True):
    pass

async def error_handle(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    try:
        # collect error message
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            f"An exception was raised while handling an update\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
            "</pre>\n\n"
            f"<pre>{html.escape(tb_string)}</pre>"
        )

        # split text into multiple messages due to 4096 character limit
        for message_chunk in split_text_into_chunks(message, 4096):
            try:
                await context.bot.send_message(update.effective_chat.id, message_chunk, parse_mode=ParseMode.HTML)
            except telegram.error.BadRequest:
                # answer has invalid characters, so we send it without parse_mode
                await context.bot.send_message(update.effective_chat.id, message_chunk)
    except:
        await context.bot.send_message(update.effective_chat.id, "Some error in error handler")

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/list", "Показать последние 10 запросов"),
        # BotCommand("/mode", "Select chat mode"),
        # BotCommand("/retry", "Сгенерировать предыдущий ответ заново"),
        # BotCommand("/balance", "Показать баланс"),
        # BotCommand("/settings", "Показать настройки"),
        # BotCommand("/help", "Показать комманды"),
    ])

def convert_to_dialogue(messages):
    dialogue = ''
    for message in messages:
        if 'user' in message:
            user_message = message['user']
            dialogue += f"Пользователь: {user_message}\n"
        if 'bot' in message:
            bot_message = message['bot']
            dialogue += f"Бот: {bot_message}\n"
    return dialogue

def is_before_today(dt):
    if dt is None:
        return True
    today = date.today()
    return dt.date() < today

def run_bot() -> None:
    application = (
        ApplicationBuilder()
        .token(config.telegram_token)
        .concurrent_updates(True)
        .rate_limiter(AIORateLimiter(max_retries=5))
        .post_init(post_init)
        .build()
    )

    # add handlers
    user_filter = filters.ALL
    if len(config.allowed_telegram_usernames) > 0:
        usernames = [x for x in config.allowed_telegram_usernames if isinstance(x, str)]
        user_ids = [x for x in config.allowed_telegram_usernames if isinstance(x, int)]
        user_filter = filters.User(username=usernames) | filters.User(user_id=user_ids)

    application.add_handler(CommandHandler("start", start_handle, filters=user_filter))

    application.add_error_handler(error_handle)

    # start the bot
    application.run_polling()


if __name__ == "__main__":
    run_bot()