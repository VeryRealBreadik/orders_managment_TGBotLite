from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters, PicklePersistence, BaseHandler
import re

from ..gsheets.gsheets import GSheet


CHOOSE_ACTION, ACTION, CONFIRMATION = range(3)
with open("essentials/users.txt", "r") as file:
    authorized_users = list(map(int, file.read().splitlines()))


class RestrictedAccess_handler(BaseHandler):
    def __init__(self):
        super().__init__(self.cb)

    async def cb(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Вы не авторизованы для использования данного бота.")

    def check_update(self, update: Update) -> bool:
        if update.message is None or update.message.from_user.id not in authorized_users:
            return True
        
        return False


class Bot:
    def __init__(self, bot_token: str, sheet: GSheet):
        self.bot_token = bot_token
        self.sheet = sheet
        self.persistence = PicklePersistence(filepath="mainbot.pkl")
        self.application = ApplicationBuilder().token(self.bot_token).persistence(self.persistence).build()

    async def start(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_cmd)],
            states={
                CHOOSE_ACTION: [MessageHandler(filters.Regex("^Добавить(.+)?$"), self.add_action), 
                        MessageHandler(filters.Regex("^Удалить(.+)?$"), self.delete_order)],
                ACTION: [MessageHandler(filters.Regex("([а-яА-Я]+) (\d+п)?\s?(\dк)? (\d+р)"), self.add_order), 
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

        self.application.add_handler(RestrictedAccess_handler())
        self.application.add_handler(conv_handler)

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()


    async def restrict_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user.id
        if user_id not in authorized_users:
            await update.message.reply_text("У вас нет доступа к этому боту.")
            return ConversationHandler.END
        return


    async def error_fallback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Произошла ошибка, попробуйте снова.")
        return await self.start_cmd(update, context)


    async def invalid_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Неверный формат ввода. Пожалуйста, попробуйте снова.")
        return await self.add_action(update, context)


    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        user_data["action"] = None
        if update.message.text == "/start":
            user_data["orders_info"] = None
            user_data["last_order"] = None
        reply_keyboard = [["Добавить заказ(-ы)", "Удалить последний заказ"]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
        return CHOOSE_ACTION


    async def add_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        user_data["action"] = "add"

        reply_keyboard = [["Вернуться"]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

        await update.message.reply_text("Отправьте детали заказа(-ов):", reply_markup=reply_markup)

        return ACTION


    async def add_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        msg = update.message.text
        if "\n" in msg:
            orders = msg.split("\n")
        else:
            orders = [msg]
        
        orders_info = []
        for order in orders:
            pattern = r"^([а-яА-Я]+) (\d+п)?\s?(\dк)? (\d+р)$"
            matched_order = re.match(pattern, order)

            company = matched_order[1]
            pallets = matched_order[2]
            boxes = matched_order[3]
            sum = matched_order[4]

            order_info = {
                "company": company,
                "pallets": pallets,
                "boxes": boxes,
                "sum": sum,
            }

            orders_info.append(order_info)

        reply_keyboard = [["Да", "Нет"]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await update.message.reply_text(f"{orders_info}\nВы хотите добавить данный(-е) заказ(-ы) в гугл таблицу?", reply_markup=reply_markup)

        user_data["orders_info"] = orders_info

        return CONFIRMATION


    async def delete_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        order_info = self.sheet.get_last_row_values()
        if order_info:
            reply_keyboard = [["Да", "Нет"]]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

            await update.message.reply_text(f"Последний заказ: {order_info}\nВы хотите удалить этот заказ из гугл таблицы?", reply_markup=reply_markup)

            user_data["action"] = "delete"
            user_data["last_order"] = order_info

            return CONFIRMATION
        else:
            await update.message.reply_text("Заказы для удаления не найдены.")
            return await self.start_cmd(update, context)


    async def confirm_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        if user_data["action"] == "add":
            orders_info = user_data["orders_info"]
            self.sheet.add_n_rows(orders_info)
            await update.message.reply_text(f"Заказ(-ы) добавлен(-ы) в гугл таблицу: {orders_info}")
            return await self.add_action(update, context)
        elif user_data["action"] == "delete":
            order_info = user_data["last_order"]
            self.sheet.delete_last_row()
            await update.message.reply_text(f"Заказ удален из гугл таблицы: {order_info}")
            return await self.delete_order(update, context)
        else:
            await update.message.reply_text("Неверное действие.")

        return await self.start_cmd(update, context)
