from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters, PicklePersistence
import re

from ..gsheets.gsheets import GSheet


CHOOSE_ACTION, ACTION, CONFIRMATION = range(3)


class Bot:
    def __init__(self, token: str, sheet: GSheet):
        self.token = token
        self.sheet = sheet
        self.persistence = PicklePersistence(filepath="mainbot.pkl")
        self.application = ApplicationBuilder().token(self.token).persistence(self.persistence).build()

    async def start(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_cmd)],
            states={
                CHOOSE_ACTION: [MessageHandler(filters.Regex("^Добавить(.+)?$"), self.add_action), 
                        MessageHandler(filters.Regex("^Удалить(.+)?$"), self.delete_order)],
                ACTION: [MessageHandler(filters.Regex("^(.+) (.+) (.+) (.+) (\d+) (\d+) (\d+)$"), self.add_order), 
                        MessageHandler(filters.Regex("^Вернуться$"), self.start_cmd), 
                        MessageHandler(filters.ALL, self.invalid_input)],
                CONFIRMATION: [MessageHandler(filters.Regex("^Да$"), self.confirm_action), 
                                MessageHandler(filters.Regex("^Нет$"), self.start_cmd)],
            },
            fallbacks=[MessageHandler(filters.ALL, self.error_fallback)],
            name="main_conversation",
            persistent=True,
            allow_reentry=True
        )

        self.application.add_handler(conv_handler)

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()


    async def error_fallback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Произошла ошибка, пожалуйста, попробуйте снова.")
        return await self.start_cmd(update, context)


    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        user_data["action"] = None
        if update.message.text == "/start":
            user_data["order_info"] = None

        reply_keyboard = [["Добавить заказ", "Удалить последний заказ"]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, выберите действие:", reply_markup=reply_markup)
        return CHOOSE_ACTION


    async def add_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        user_data["action"] = "add"

        reply_keyboard = [["Вернуться"]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

        await update.message.reply_text("Пожалуйста, отправьте детали заказа (формат 'Фамилия Имя Отчество Компания (слитно или через -) Кол-во паллетов Кол-во коробок Сумма заказа'):", reply_markup=reply_markup)

        return ACTION


    async def add_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        order = update.message.text
        pattern = r"^(.+) (.+) (.+) (.+) (\d+) (\d+) (\d+)$"
        matched_order = re.match(pattern, order)

        lastname = matched_order[1]
        name = matched_order[2]
        middlename = matched_order[3]
        company = matched_order[4]
        pallets = matched_order[5]
        boxes = matched_order[6]
        sum = matched_order[7]

        order_info = {
            "lastname": lastname,
            "name": name,
            "middlename": middlename,
            "company": company,
            "pallets": pallets,
            "boxes": boxes,
            "sum": sum,
        }

        reply_keyboard = [["Да", "Нет"]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await update.message.reply_text(f"{order_info}\nВы хотите добавить данный заказ в гугл таблицу?", reply_markup=reply_markup)

        user_data["order_info"] = order_info

        return CONFIRMATION


    async def invalid_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Неверный формат ввода. Пожалуйста, попробуйте снова.")
        return await self.add_action(update, context)


    async def delete_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data

        if user_data["order_info"]:
            reply_keyboard = [["Да", "Нет"]]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

            await update.message.reply_text(f"Последний заказ: {user_data['order_info']}\nВы хотите его удалить из гугл таблицы?", reply_markup=reply_markup)

            user_data["action"] = "delete"

            return CONFIRMATION
        else:
            await update.message.reply_text("Заказы для удаления не найдены.")
            return await self.start_cmd(update, context)


    async def confirm_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        if user_data["action"] == "add":
            order_info = user_data["order_info"]
            self.sheet.add_row(order_info)
            await update.message.reply_text(f"Заказ добавлен в гугл таблицу: {order_info}")
        elif user_data["action"] == "delete":
            order_info = user_data["order_info"]
            self.sheet.delete_last_row()
            await update.message.reply_text(f"Заказ удалён из гугл таблицы: {order_info}")
            user_data["order_info"] = None
        else:
            await update.message.reply_text("Неверное действие.")

        return await self.start_cmd(update, context)
