from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
import re

from dotenv import load_dotenv
import os


load_dotenv()

CHOOSE_ACTION, ACTION, CONFIRMATION = range(3)

def main():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_ACTION: [MessageHandler(filters.Regex("^Add(.+)?$"), add_action), 
                    MessageHandler(filters.Regex("^Delete(.+)?$"), delete_order)],
            ACTION: [MessageHandler(filters.Regex("^(.+) (.+) (.+) (.+) (\d+) (\d+)$"), add_order), 
                    MessageHandler(filters.ALL, invalid_input)],
            CONFIRMATION: [MessageHandler(filters.Regex("^Yes$"), confirm_action), 
                            MessageHandler(filters.Regex("^No$"), start)],
        },
        fallbacks=[MessageHandler(filters.ALL, error_fallback)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


async def error_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Error occured. Please try again.")
    return await start(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data["action"] = None
    if update.message.text == "/start":
        user_data["order_info"] = None

    reply_keyboard = [["Add order", "Delete last order"]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text("Please choose an action:", reply_markup=reply_markup)
    return CHOOSE_ACTION


async def add_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data["action"] = "add"

    await update.message.reply_text("Please enter the order details:")

    return ACTION


async def add_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    order = update.message.text
    pattern = r"^(.+) (.+) (.+) (.+) (\d+) (\d+)$"
    matched_order = re.match(pattern, order)

    lastname = matched_order[1]
    name = matched_order[2]
    middlename = matched_order[3]
    company = matched_order[4]
    boxes = matched_order[5]
    sum = matched_order[6]

    order_info = {
        "lastname": lastname,
        "name": name,
        "middlename": middlename,
        "company": company,
        "boxes": boxes,
        "sum": sum,
    }

    reply_keyboard = [["Yes", "No"]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text(f"{order_info}\nDo you want to add this order to the google sheet?", reply_markup=reply_markup)

    user_data["order_info"] = order_info

    return CONFIRMATION


async def invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Invalid input. Please try again.")
    return await add_action(update, context)


async def delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data

    if user_data["order_info"]:
        reply_keyboard = [["Yes", "No"]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

        await update.message.reply_text(f"Last order info: {user_data['order_info']}\nDo you want to delete it?", reply_markup=reply_markup)

        user_data["action"] = "delete"
        
        return CONFIRMATION
    else:
        await update.message.reply_text("No order to delete.")
        return await start(update, context)


async def confirm_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    if user_data["action"] == "add":
        order_info = user_data["order_info"]
        await update.message.reply_text(f"Order added: {order_info}")
    elif user_data["action"] == "delete":
        order_info = user_data["order_info"]
        await update.message.reply_text(f"Order deleted: {order_info}")
        user_data["order_info"] = None
    else:
        await update.message.reply_text("Invalid action.")

    return await start(update, context)
