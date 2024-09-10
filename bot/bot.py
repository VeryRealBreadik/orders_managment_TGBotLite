from telegram import Update
from telegram.ext import Application, ConversationHandler, CommandHandler, MessageHandler, ContextTypes, ReplyKeyboardMarkup, filters
import re


ACTION, CONFIRMATION = range(2)

def main():
    application = Application.builder().token("").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ACTION: [MessageHandler(filters.REGEX("^Add(.+)?$"), add_order), 
                    MessageHandler(filters.REGEX("^Delete(.+)?$"), delete_order)],
            CONFIRMATION: [MessageHandler(filters.REGEX("^YES$"), confirm_action), 
                            MessageHandler(filters.REGEX("^NO$"), start)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Action canceled.")
    return await start(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data["action"] = None
    user_data["order_info"] = None

    reply_keyboard = [["Add order", "Delete last order"]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Please choose an action:", reply_markup=reply_markup)
    return ACTION


async def add_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data

    await update.message.reply_text("Please enter the order details:")

    order = update.message.text
    pattern = r"^(.+) (.+) (.+) (.+) (\d+) (\d+)$"
    matched_order = re.match(pattern, order)
    if matched_order:
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

        reply_keyboard = [["YES", "NO"]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        await update.message.reply_text(f"{order_info}\nDo you want to add this order to the google sheet?", reply_markup=reply_markup)

        user_data["order_info"] = order_info
        user_data["action"] = "add"

        return CONFIRMATION
    else:
        await update.message.reply_text("Invalid order details. Please try again.")
        return await add_order(update, context)


async def delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data

    if user_data["order_info"]:
        reply_keyboard = [["Yes", "No"]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

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
        pass
        #  TODO: Add some code to add the order to the google sheet
    elif user_data["action"] == "delete":
        pass
        #  TODO: Add some code to delete the last order from the google sheet
    else:
        await update.message.reply_text("Invalid action.")
        return await start(update, context)
