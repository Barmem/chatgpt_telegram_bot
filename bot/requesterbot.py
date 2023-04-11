from telegram import ForceReply, Update, Bot, KeyboardButton, ReplyKeyboardMarkup, Update
import telegram
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler, JobQueue
import fortune_requests
import os
import textsfetch
import config

final_texts = textsfetch.getset()
WORKING, REQUEST, STOP = range(3)
bot_token = config.tarot_token
list_of_requests = fortune_requests.requestslist() 

async def send_message(context: ContextTypes.DEFAULT_TYPE):
    request = list_of_requests.get_table_length()
    if request > 0:
        ids = list_of_requests.getworking()
        for id in ids:
            await context.bot.send_message(chat_id=id, text=final_texts["tarolog"]["request_count"] + f"{request}")


# def start_repeating(update, context):
#     job = context.job_queue.run_repeating(send_message, interval=600, first=0)
#     context.chat_data['job'] = job

# def stop_repeating(update, context):
#     job = context.chat_data.get('job')
#     if job:
#         job.schedule_removal()
#         del context.chat_data['job']

async def start(update, context):
    keyboard = [[KeyboardButton(text=final_texts["tarolog"]["start_work"])]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=final_texts["tarolog"]["start_message"], reply_markup=reply_markup)
    return WORKING

async def working(update, context):
    list_of_requests.setsworkingtatus(update.message.from_user.id, 1)
    keyboard = [[KeyboardButton(text=final_texts["tarolog"]["get_request"])],[KeyboardButton(text=final_texts["tarolog"]["stop_work"])]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    matcher = update.message.text
    if matcher == final_texts["tarolog"]["start_work"]:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=final_texts["tarolog"]["start_work"], reply_markup=reply_markup)
    if matcher == final_texts["tarolog"]["return"]:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=final_texts["tarolog"]["start_work"], reply_markup=reply_markup)
    if matcher == final_texts["tarolog"]["close_request"]:
        list_of_requests.setstatus(context.chat_data['current_request'], 3)
        del context.chat_data['current_request']
        await context.bot.send_message(chat_id=update.effective_chat.id, text=final_texts["tarolog"]["close_request"], reply_markup=reply_markup)
    if matcher == final_texts["tarolog"]["cancel_request"]:
        list_of_requests.setstatus(context.chat_data['current_request'], 1)
        del context.chat_data['current_request']
        await context.bot.send_message(chat_id=update.effective_chat.id, text=final_texts["tarolog"]["request_canceled"], reply_markup=reply_markup)
    return REQUEST

async def got_request(update, context):
    list_of_requests.setsworkingtatus(update.message.from_user.id, 0)
    # stop_repeating(update, context)
    matcher = update.message.text
    if matcher == final_texts["tarolog"]["get_request"]:
        # try:
        request, id = list_of_requests.getrand()
        context.chat_data['current_request']=id
        if id == 0:
            request = final_texts["tarolog"]["no_requests"]
            keyboard = [[KeyboardButton(text=final_texts["tarolog"]["return"])]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=request, reply_markup=reply_markup)
            return WORKING
        list_of_requests.setstatus(context.chat_data['current_request'], 2)
        # except Exception as e:
        #     print(request)
        #     request = final_texts["tarolog"]["no_requests"]
        #     keyboard = [[KeyboardButton(text=final_texts["tarolog"]["return"])]]
        #     reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        #     await context.bot.send_message(chat_id=update.effective_chat.id, text=request, reply_markup=reply_markup)
        #     return WORKING
        
        keyboard = [[KeyboardButton(text=final_texts["tarolog"]["close_request"])],[KeyboardButton(text=final_texts["tarolog"]["cancel_request"])]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=request, reply_markup=reply_markup)
        return WORKING
    if matcher == final_texts["tarolog"]["stop_work"]:
        keyboard = [[KeyboardButton(text=final_texts["tarolog"]["start_work"])]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=final_texts["tarolog"]["end_work"], reply_markup=reply_markup)
        return WORKING

async def error(update, context):
    list_of_requests.setsworkingtatus(update.effective_chat.id, 0)
    keyboard = [[KeyboardButton(text=final_texts["tarolog"]["start_work"])]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=final_texts["tarolog"]["error_work"], reply_markup=reply_markup)
    return WORKING

async def get_request(update, context):
    request = list_of_requests.getrand()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=request)

def main():
    manager = Application.builder().token(bot_token).build()
    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(final_texts["tarolog"]["start_work"]), working), MessageHandler(filters.Text([final_texts["tarolog"]["stop_work"], final_texts["tarolog"]["get_request"], final_texts["tarolog"]["no_requests"], final_texts["tarolog"]["return"], final_texts["tarolog"]["close_request"], final_texts["tarolog"]["cancel_request"]]), error)],
        states={
            WORKING: [MessageHandler(filters.TEXT, working)],
            REQUEST: [MessageHandler(filters.TEXT, got_request)],
            STOP: [MessageHandler(filters.TEXT, start)]
        },
        fallbacks=[CommandHandler('cancel', start)]
    )
    manager.add_handler(conversation_handler)
    manager.add_handler(CommandHandler("start", start))
    manager.job_queue.run_repeating(send_message, interval=300, first=30)

    
    # manager.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responce))
    # Run the bot until the user presses Ctrl-C
    manager.run_polling()

if __name__ == '__main__':
    main()
